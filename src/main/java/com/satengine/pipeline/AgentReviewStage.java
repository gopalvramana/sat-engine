package com.satengine.pipeline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.domain.question.QuestionReview;
import com.satengine.domain.question.QuestionReviewRepository;
import com.satengine.pipeline.claude.ClaudeClient;
import com.satengine.pipeline.claude.PromptLibrary;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class AgentReviewStage {

    private final QuestionRepository       questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final QuestionReviewRepository questionReviewRepository;
    private final ClaudeClient             claudeClient;
    private final ObjectMapper             objectMapper;

    private static final String REVIEW_MODEL = "claude-opus-4-5";
    private static final int    MAX_TOKENS   = 1200;
    private static final double MIN_CONF     = 0.85;

    public void run(boolean onlyFailed) {
        List<Question> queue = onlyFailed
                ? questionRepository.findByStatus(QuestionStatus.GENERATED.lower()).stream()
                    .filter(q -> questionReviewRepository.findByQuestion(q)
                            .map(r -> !r.getPass()).orElse(false))
                    .toList()
                : questionRepository.findByStatus(QuestionStatus.GENERATED.lower());

        if (queue.isEmpty()) {
            log.info("No questions with status=generated to review.");
            return;
        }

        log.info("═".repeat(60));
        log.info(" Agent Review  questions={} onlyFailed={} model={}", queue.size(), onlyFailed, REVIEW_MODEL);
        log.info("═".repeat(60));

        int passed = 0, failed = 0, errors = 0;

        for (int i = 0; i < queue.size(); i++) {
            Question q = queue.get(i);
            try {
                JsonNode result = reviewQuestion(q);
                saveReview(q, result);

                boolean autoPass = result.path("pass").asBoolean() && result.path("confidence").asDouble() >= MIN_CONF;
                String icon = result.path("pass").asBoolean() ? (autoPass ? "PASS" : "WARN") : "FAIL";
                log.info("[{}/{}] {}  {} conf:{}", i + 1, queue.size(),
                        padEnd(q.getExternalId(), 20), icon,
                        String.format("%.2f", result.path("confidence").asDouble()));

                if (result.path("pass").asBoolean()) passed++; else failed++;

            } catch (Exception e) {
                log.error("[{}/{}] {} error: {}", i + 1, queue.size(), q.getExternalId(), e.getMessage());
                errors++;
            }
        }
        log.info("─".repeat(60));
        log.info(" Results: {} passed  {} failed  {} errors", passed, failed, errors);
    }

    private JsonNode reviewQuestion(Question q) throws Exception {
        // Build slim question JSON (omit heavy diagram config)
        ObjectNode slim = buildSlimNode(q);
        String prompt = PromptLibrary.buildReviewPrompt(objectMapper.writeValueAsString(slim), q.getSection(), q.getQuestionType());
        String raw = claudeClient.call(REVIEW_MODEL, MAX_TOKENS, "", prompt);
        String cleaned = raw.replaceAll("(?i)^```json\\s*", "").replaceAll("\\s*```$", "").strip();
        JsonNode result = objectMapper.readTree(cleaned);

        // Sanitize solvedAnswer
        return sanitizeSolvedAnswer(result);
    }

    private JsonNode sanitizeSolvedAnswer(JsonNode result) throws Exception {
        String sa = result.path("solvedAnswer").asText(null);
        if (sa == null) return result;

        String s = sa.strip();
        ObjectNode mutable = (ObjectNode) objectMapper.readTree(objectMapper.writeValueAsString(result));

        if (s.matches("(?i)[A-D]")) {
            mutable.put("solvedAnswer", s.toUpperCase());
        } else if (s.matches("-?\\d+(\\.\\d+)?")) {
            mutable.put("solvedAnswer", s); // SPR numeric
        } else {
            // Model returned prose — critical failure
            String originalText = s;
            java.util.regex.Matcher m = java.util.regex.Pattern.compile("(?i)^([A-D])\\b|^(-?\\d+(\\.\\d+)?)")
                    .matcher(s);
            if (m.find()) {
                mutable.put("solvedAnswer", m.group(1) != null ? m.group(1).toUpperCase() : m.group(2));
            } else {
                mutable.putNull("solvedAnswer");
            }
            mutable.put("pass", false);
            com.fasterxml.jackson.databind.node.ArrayNode issues =
                    mutable.withArray("issues");
            ObjectNode issue = objectMapper.createObjectNode();
            issue.put("check", "MATH");
            issue.put("severity", "critical");
            issue.put("detail", "Agent could not identify a valid answer. solvedAnswer returned: \"" + originalText + "\". All options may be wrong.");
            issues.add(issue);
        }
        return mutable;
    }

    @Transactional
    void saveReview(Question q, JsonNode result) {
        QuestionReview review = questionReviewRepository.findByQuestion(q)
                .orElse(QuestionReview.builder().question(q).build());

        review.setPass(result.path("pass").asBoolean(false));
        review.setConfidence(BigDecimal.valueOf(result.path("confidence").asDouble(0)));
        review.setSolvedAnswer(result.path("solvedAnswer").asText(null));
        try {
            review.setIssues(objectMapper.writeValueAsString(result.path("issues")));
        } catch (Exception ignored) {}
        review.setNotes(result.path("notes").asText(null));
        review.setModel(REVIEW_MODEL);
        review.setCheckedAt(OffsetDateTime.now());

        questionReviewRepository.save(review);

        // Advance status
        q.setStatus(QuestionStatus.REVIEWED.lower());
        questionRepository.save(q);
    }

    private ObjectNode buildSlimNode(Question q) {
        ObjectNode n = objectMapper.createObjectNode();
        n.put("externalId",       q.getExternalId());
        n.put("section",          q.getSection());
        n.put("domain",           q.getDomain());
        n.put("difficulty",       q.getDifficulty());
        n.put("questionType",     q.getQuestionType());
        n.put("questionStem",     q.getQuestionStem());
        if (q.getOptionA() != null) n.put("optionA", q.getOptionA());
        if (q.getOptionB() != null) n.put("optionB", q.getOptionB());
        if (q.getOptionC() != null) n.put("optionC", q.getOptionC());
        if (q.getOptionD() != null) n.put("optionD", q.getOptionD());

        // SPR fields — must be included so the reviewer can validate SPR_RANGE and SCHEMA
        if (q.getSprMin() != null) n.put("sprMin", q.getSprMin().doubleValue());
        if (q.getSprMax() != null) n.put("sprMax", q.getSprMax().doubleValue());

        // explanationShort — required field for both MCQ and SPR schema checks
        if (q.getExplanationShort() != null) n.put("explanationShort", q.getExplanationShort());

        // Attach correct answer
        questionAnswerRepository.findByQuestionId(q.getId())
                .ifPresent(qa -> n.put("correctAnswer", qa.getCorrectAnswer()));

        if (q.getExplanationSteps() != null) {
            try { n.set("explanationSteps", objectMapper.readTree(q.getExplanationSteps())); }
            catch (Exception ignored) {}
        }
        if (q.getCoreConcept() != null) {
            try { n.set("coreConcept", objectMapper.readTree(q.getCoreConcept())); }
            catch (Exception ignored) {}
        }
        if (q.getPrerequisites() != null) {
            try { n.set("prerequisites", objectMapper.readTree(q.getPrerequisites())); }
            catch (Exception ignored) {}
        }
        if (q.getDiagram() != null) {
            try {
                JsonNode d = objectMapper.readTree(q.getDiagram());
                ObjectNode slim = objectMapper.createObjectNode();
                slim.put("diagramType", d.path("diagramType").asText());
                slim.put("_note", "Full diagram config omitted for brevity");
                n.set("diagram", slim);
            } catch (Exception ignored) {}
        }
        n.put("pool", q.getPool());
        return n;
    }

    private String padEnd(String s, int len) {
        if (s == null) s = "";
        return s.length() >= len ? s : s + " ".repeat(len - s.length());
    }
}
