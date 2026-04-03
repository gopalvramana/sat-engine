package com.satengine.pipeline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.pipeline.claude.ClaudeClient;
import com.satengine.pipeline.claude.PromptLibrary;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class EnrichStage {

    private final QuestionRepository       questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final ClaudeClient             claudeClient;
    private final ObjectMapper             objectMapper;

    private static final String ENRICH_MODEL = "claude-opus-4-6";
    private static final int    MAX_TOKENS   = 3500;

    /**
     * Normal run: enriches questions with status=reviewed → advances to enriched.
     */
    public void run() {
        run(false, null, null);
    }

    /**
     * @param includeApproved  when true, re-enriches approved questions (all, not just unenriched)
     * @param section          optional filter — "math" | "reading_writing" | null = all
     * @param domain           optional filter — e.g. "algebra" | null = all
     */
    public void run(boolean includeApproved, String section, String domain) {
        List<Question> queue = new java.util.ArrayList<>();

        // Reviewed questions (normal pipeline)
        if (domain != null) {
            queue.addAll(questionRepository.findReviewedByDomain(domain));
        } else if (section != null) {
            queue.addAll(questionRepository.findReviewedBySection(section));
        } else {
            queue.addAll(questionRepository.findByStatus(QuestionStatus.REVIEWED.lower()));
        }

        // Approved questions (re-enrich run)
        if (includeApproved) {
            List<Question> approved;
            if (domain != null) {
                approved = questionRepository.findAllApprovedByDomain(domain);
            } else if (section != null) {
                approved = questionRepository.findAllApprovedBySection(section);
            } else {
                approved = questionRepository.findAllApproved();
            }
            log.info("--include-approved: {} approved questions match filter (domain={}, section={})",
                    approved.size(), domain, section);
            queue.addAll(approved);
        }

        if (queue.isEmpty()) {
            log.info("No questions to enrich.");
            return;
        }

        log.info("═".repeat(60));
        log.info(" Enrich Stage  questions={}  model={}", queue.size(), ENRICH_MODEL);
        log.info("═".repeat(60));

        int enriched = 0, skipped = 0, failed = 0;

        for (int i = 0; i < queue.size(); i++) {
            Question q = queue.get(i);
            String label = padEnd(q.getExternalId(), 20);
            try {
                if ("reading_writing".equals(q.getSection())) {
                    // R&W questions don't need Math-specific enrichment fields.
                    // Just set pool and advance status directly.
                    advanceRWQuestion(q, "approved".equals(q.getStatus()));
                    log.info("[{}/{}] {} skipped (R&W — no enrich needed)", i + 1, queue.size(), label);
                    skipped++;
                } else {
                    JsonNode fields = enrichQuestion(q);
                    applyFields(q, fields, "approved".equals(q.getStatus()));
                    log.info("[{}/{}] {} done", i + 1, queue.size(), label);
                    enriched++;
                }
            } catch (Exception e) {
                log.error("[{}/{}] {} FAILED: {}", i + 1, queue.size(), label, e.getMessage());
                failed++;
            }

            // Rate-limit buffer between questions
            if (i < queue.size() - 1) {
                try { Thread.sleep(500); } catch (InterruptedException ignored) {}
            }
        }

        log.info("─".repeat(60));
        log.info(" Results: {} enriched  {} skipped (R&W)  {} failed", enriched, skipped, failed);
    }

    @Transactional
    void advanceRWQuestion(Question q, boolean keepApproved) {
        q.setPool("both");
        if (!keepApproved) {
            q.setStatus(QuestionStatus.ENRICHED.lower());
        }
        questionRepository.save(q);
    }

    private JsonNode enrichQuestion(Question q) throws Exception {
        ObjectNode slim = buildSlimNode(q);
        String prompt = PromptLibrary.buildEnrichPrompt(
                objectMapper.writeValueAsString(slim),
                q.getSection(),
                q.getDomain(),
                q.getDifficulty(),
                q.getQuestionType());
        String raw = claudeClient.call(ENRICH_MODEL, MAX_TOKENS, "", prompt);
        String cleaned = raw.replaceAll("(?i)^```json\\s*", "").replaceAll("\\s*```$", "").strip();
        JsonNode result = objectMapper.readTree(cleaned);

        // ── Structural validation ────────────────────────────────────────────
        JsonNode steps = result.path("explanationSteps");
        if (!steps.isArray() || steps.size() < 2) {
            throw new IllegalStateException("explanationSteps missing or has fewer than 2 steps");
        }

        // ── Formula-law validation ───────────────────────────────────────────
        // If a step content mentions a named formula, math field must be present.
        // Covers both explanationSteps and alternativeApproach steps.
        validateFormulaLaw(steps, "explanationSteps");
        JsonNode altApproach = result.path("alternativeApproach");
        if (altApproach.isObject()) {
            validateFormulaLaw(altApproach.path("steps"), "alternativeApproach.steps");
        }

        return result;
    }

    /** Named formulas that MUST have a populated math field in the same step. */
    private static final List<String> FORMULA_KEYWORDS = List.of(
        "quadratic formula", "pythagorean theorem", "slope-intercept form",
        "distance formula", "midpoint formula", "law of sines", "law of cosines",
        "completing the square", "discriminant", "vertex formula",
        "point-slope form", "standard form", "exponential formula"
    );

    private void validateFormulaLaw(JsonNode stepsNode, String location) {
        if (!stepsNode.isArray()) return;
        for (JsonNode step : stepsNode) {
            String content = step.path("content").asText("").toLowerCase();
            String math    = step.path("math").asText("").trim();
            boolean mathMissing = math.isEmpty() || math.equalsIgnoreCase("null");
            for (String keyword : FORMULA_KEYWORDS) {
                if (content.contains(keyword) && mathMissing) {
                    throw new IllegalStateException(
                        "Formula law violation in " + location + ": step \"" +
                        step.path("title").asText("?") +
                        "\" mentions \"" + keyword + "\" but math field is empty.");
                }
            }
        }
    }

    @Transactional
    void applyFields(Question q, JsonNode fields) throws Exception {
        applyFields(q, fields, false);
    }

    @Transactional
    void applyFields(Question q, JsonNode fields, boolean keepApproved) throws Exception {
        if (!fields.path("explanationSteps").isMissingNode()) {
            q.setExplanationSteps(objectMapper.writeValueAsString(fields.path("explanationSteps")));
        }
        if (!fields.path("alternativeApproach").isMissingNode() && !fields.path("alternativeApproach").isNull()) {
            q.setAlternativeApproach(objectMapper.writeValueAsString(fields.path("alternativeApproach")));
        }

        if (!fields.path("coreConcept").isMissingNode()) {
            q.setCoreConcept(objectMapper.writeValueAsString(fields.path("coreConcept")));
        }
        if (!fields.path("prerequisites").isMissingNode()) {
            q.setPrerequisites(objectMapper.writeValueAsString(fields.path("prerequisites")));
        }
        if (!fields.path("animation").isMissingNode()) {
            q.setAnimation(objectMapper.writeValueAsString(fields.path("animation")));
        }
        JsonNode wrongAnswers = fields.path("wrongAnswerExplanations");
        if (!wrongAnswers.isMissingNode() && !wrongAnswers.isNull()) {
            q.setWrongAnswerExplanations(objectMapper.writeValueAsString(wrongAnswers));
        }
        q.setPool(fields.path("pool").asText("both"));
        // Keep approved status if already approved; otherwise advance to enriched
        if (!keepApproved) {
            q.setStatus(QuestionStatus.ENRICHED.lower());
        }

        questionRepository.save(q);
    }

    private ObjectNode buildSlimNode(Question q) {
        ObjectNode n = objectMapper.createObjectNode();
        n.put("externalId",      q.getExternalId());
        n.put("section",         q.getSection());
        n.put("domain",          q.getDomain());
        n.put("skill",           q.getSkill());
        n.put("difficulty",      q.getDifficulty());
        n.put("questionType",    q.getQuestionType());
        n.put("questionStem",    q.getQuestionStem());
        if (q.getOptionA() != null) n.put("optionA", q.getOptionA());
        if (q.getOptionB() != null) n.put("optionB", q.getOptionB());
        if (q.getOptionC() != null) n.put("optionC", q.getOptionC());
        if (q.getOptionD() != null) n.put("optionD", q.getOptionD());
        n.put("explanationShort", q.getExplanationShort());
        questionAnswerRepository.findByQuestionId(q.getId())
                .ifPresent(qa -> n.put("correctAnswer", qa.getCorrectAnswer()));
        return n;
    }

    private String padEnd(String s, int len) {
        if (s == null) s = "";
        return s.length() >= len ? s : s + " ".repeat(len - s.length());
    }
}
