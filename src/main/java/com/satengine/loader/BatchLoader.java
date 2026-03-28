package com.satengine.loader;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Optional;

/**
 * BatchLoader reads a JSON array of question objects and upserts them into
 * the database, inserting correct answers into question_answers separately.
 *
 * Activate via CLI flag:
 *   java -jar sat-engine.jar --load-batch /path/to/batch.json
 *
 * Questions where reviewed != true are skipped.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class BatchLoader implements ApplicationRunner {

    private final QuestionRepository questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final ObjectMapper objectMapper;

    @Override
    public void run(ApplicationArguments args) throws Exception {
        if (!args.containsOption("load-batch")) {
            return; // Normal server startup — do nothing
        }

        java.util.List<String> values = args.getOptionValues("load-batch");
        if (values == null || values.isEmpty()) {
            log.error("--load-batch requires a file path argument");
            return;
        }

        String filePath = values.get(0);
        loadBatch(filePath);
    }

    @Transactional
    public void loadBatch(String jsonFilePath) throws Exception {
        File file = new File(jsonFilePath);
        if (!file.exists()) {
            throw new IllegalArgumentException("File not found: " + jsonFilePath);
        }

        JsonNode root = objectMapper.readTree(file);
        if (!root.isArray()) {
            throw new IllegalArgumentException("Expected a JSON array at the top level of: " + jsonFilePath);
        }

        int loaded = 0;
        int skipped = 0;

        for (JsonNode node : root) {
            boolean reviewed = node.path("reviewed").asBoolean(false);
            if (!reviewed) {
                skipped++;
                continue;
            }

            String externalId = node.path("externalId").asText(null);
            if (externalId == null || externalId.isBlank()) {
                log.warn("Skipping question with missing externalId");
                skipped++;
                continue;
            }

            // Upsert: find existing or create new
            Optional<Question> existing = questionRepository.findByExternalId(externalId);
            Question question = existing.orElseGet(Question::new);

            // Map scalar fields
            question.setExternalId(externalId);
            question.setSection(node.path("section").asText());
            question.setDomain(node.path("domain").asText());
            question.setSkill(textOrNull(node, "skill"));
            question.setDifficulty((short) node.path("difficulty").asInt(1));
            question.setQuestionType(node.path("questionType").asText());
            question.setQuestionStem(node.path("questionStem").asText());
            question.setOptionA(textOrNull(node, "optionA"));
            question.setOptionB(textOrNull(node, "optionB"));
            question.setOptionC(textOrNull(node, "optionC"));
            question.setOptionD(textOrNull(node, "optionD"));
            question.setSprMin(decimalOrNull(node, "sprMin"));
            question.setSprMax(decimalOrNull(node, "sprMax"));
            question.setExplanationShort(textOrNull(node, "explanationShort"));
            question.setTrapCategory(textOrNull(node, "trapCategory"));
            question.setTrapExplanation(textOrNull(node, "trapExplanation"));
            question.setPool(node.path("pool").asText("both"));
            question.setPassageText(textOrNull(node, "passageText"));
            question.setPassageSource(textOrNull(node, "passageSource"));
            question.setCalculatorOk(node.path("calculatorOk").asBoolean(true));
            question.setSource(node.path("source").asText("ai_generated"));
            question.setReviewed(true);
            question.setReviewNotes(textOrNull(node, "reviewNotes"));

            // Parse generatedAt if present
            String generatedAt = textOrNull(node, "generatedAt");
            if (generatedAt != null) {
                try {
                    question.setGeneratedAt(OffsetDateTime.parse(generatedAt));
                } catch (Exception e) {
                    log.warn("Could not parse generatedAt '{}' for {}", generatedAt, externalId);
                }
            }

            // JSONB fields — store as raw JSON strings
            question.setExplanationSteps(jsonStringOrNull(node, "explanationSteps"));
            question.setCoreConcept(jsonStringOrNull(node, "coreConcept"));
            question.setPrerequisites(jsonStringOrNull(node, "prerequisites"));
            question.setAnimation(jsonStringOrNull(node, "animation"));
            question.setDiagram(jsonStringOrNull(node, "diagram"));

            Question saved = questionRepository.save(question);

            // Upsert correct answer — separate table, separate concern
            String correctAnswer = textOrNull(node, "correctAnswer");
            if (correctAnswer != null && !correctAnswer.isBlank()) {
                QuestionAnswer qa = questionAnswerRepository
                        .findByQuestionId(saved.getId())
                        .orElseGet(() -> QuestionAnswer.builder()
                                .question(saved)
                                .build());
                qa.setCorrectAnswer(correctAnswer);
                questionAnswerRepository.save(qa);
            }

            loaded++;
        }

        System.out.printf("Loaded %d questions (%d skipped — not reviewed)%n", loaded, skipped);
        log.info("Batch load complete: {} loaded, {} skipped (not reviewed)", loaded, skipped);
    }

    // -------------------------------------------------------------------------
    // Helpers
    // -------------------------------------------------------------------------

    private String textOrNull(JsonNode node, String field) {
        JsonNode child = node.path(field);
        if (child.isMissingNode() || child.isNull()) return null;
        String text = child.asText(null);
        return (text == null || text.isBlank()) ? null : text;
    }

    private BigDecimal decimalOrNull(JsonNode node, String field) {
        JsonNode child = node.path(field);
        if (child.isMissingNode() || child.isNull()) return null;
        try {
            return new BigDecimal(child.asText());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private String jsonStringOrNull(JsonNode node, String field) {
        JsonNode child = node.path(field);
        if (child.isMissingNode() || child.isNull()) return null;
        // Already an object/array → serialize back to string for JSONB storage
        if (child.isObject() || child.isArray()) {
            return child.toString();
        }
        // String value — return as-is (already a JSON-encoded string)
        String text = child.asText(null);
        return (text == null || text.isBlank()) ? null : text;
    }
}
