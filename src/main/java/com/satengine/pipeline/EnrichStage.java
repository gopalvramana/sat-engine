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
    private static final int    MAX_TOKENS   = 2000;

    /**
     * Normal run: enriches questions with status=reviewed → advances to enriched.
     */
    public void run() {
        run(false);
    }

    /**
     * @param includeApproved  when true, also enriches approved questions that
     *                         were never enriched (coreConcept IS NULL).
     *                         Those questions keep their approved status.
     */
    public void run(boolean includeApproved) {
        List<Question> queue = new java.util.ArrayList<>(
                questionRepository.findByStatus(QuestionStatus.REVIEWED.lower()));

        if (includeApproved) {
            List<Question> unenriched = questionRepository.findApprovedUnenriched();
            log.info("--include-approved: {} approved questions without enrichment data", unenriched.size());
            queue.addAll(unenriched);
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
        String prompt = PromptLibrary.buildEnrichPrompt(objectMapper.writeValueAsString(slim));
        String raw = claudeClient.call(ENRICH_MODEL, MAX_TOKENS, "", prompt);
        String cleaned = raw.replaceAll("(?i)^```json\\s*", "").replaceAll("\\s*```$", "").strip();
        JsonNode result = objectMapper.readTree(cleaned);

        // Validate
        JsonNode steps = result.path("explanationSteps");
        if (!steps.isArray() || steps.size() < 2) {
            throw new IllegalStateException("explanationSteps missing or has fewer than 2 steps");
        }
        return result;
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
