package com.satengine.pipeline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.pipeline.claude.ClaudeClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Lightweight enrichment pass that generates a one-to-two sentence explanation
 * for WHY each answer choice (A/B/C/D) is correct or incorrect.
 *
 * Stored in questions.choice_explanations as:
 *   {"A": "...", "B": "...", "C": "...", "D": "..."}
 *
 * Only applies to MCQ questions. SPR questions are skipped (no distractors).
 * Does not change question status — purely additive.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EnrichChoiceExplanationsStage {

    private final QuestionRepository       questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final ClaudeClient             claudeClient;
    private final ObjectMapper             objectMapper;

    private static final String MODEL      = "claude-haiku-4-5-20251001";
    private static final int    MAX_TOKENS = 1200;

    // ── Public entry points ─────────────────────────────────────────────────

    /** Backfill all MCQ questions that are missing choiceExplanations. */
    public int runBackfill() {
        List<Question> queue = questionRepository.findMissingChoiceExplanations();
        if (queue.isEmpty()) {
            log.info("Choice explanations backfill: nothing to do.");
            return 0;
        }
        log.info("═".repeat(60));
        log.info(" EnrichChoiceExplanations  questions={}  model={}", queue.size(), MODEL);
        log.info("═".repeat(60));
        return processQueue(queue);
    }

    /** Re-run on a single question by externalId (regardless of current state). */
    public void runById(String externalId) {
        Question q = questionRepository.findByExternalId(externalId)
                .orElseThrow(() -> new IllegalArgumentException("Question not found: " + externalId));
        if (!"mcq".equalsIgnoreCase(q.getQuestionType())) {
            log.info("Skipping {} — not MCQ", externalId);
            return;
        }
        enrichOne(q, 1, 1);
    }

    // ── Internal ────────────────────────────────────────────────────────────

    private int processQueue(List<Question> queue) {
        int done = 0, failed = 0;
        for (int i = 0; i < queue.size(); i++) {
            boolean ok = enrichOne(queue.get(i), i + 1, queue.size());
            if (ok) done++; else failed++;
            if (i < queue.size() - 1) {
                try { Thread.sleep(300); } catch (InterruptedException ignored) {}
            }
        }
        log.info("─".repeat(60));
        log.info(" Results: {} enriched  {} failed", done, failed);
        return done;
    }

    private boolean enrichOne(Question q, int i, int total) {
        String label = padEnd(q.getExternalId(), 20);
        try {
            String correctAnswer = questionAnswerRepository.findByQuestionId(q.getId())
                    .map(qa -> qa.getCorrectAnswer())
                    .orElseThrow(() -> new IllegalStateException("No answer record for " + q.getExternalId()));

            String prompt = buildPrompt(q, correctAnswer);
            String raw    = claudeClient.call(MODEL, MAX_TOKENS, "", prompt);
            String cleaned = raw.replaceAll("(?i)^```json\\s*", "").replaceAll("\\s*```$", "").strip();

            JsonNode result = objectMapper.readTree(cleaned);
            validate(result, q);

            save(q, objectMapper.writeValueAsString(result));
            log.info("[{}/{}] {} done", i, total, label);
            return true;

        } catch (Exception e) {
            log.error("[{}/{}] {} FAILED: {}", i, total, label, e.getMessage());
            return false;
        }
    }

    private String buildPrompt(Question q, String correctAnswer) {
        StringBuilder sb = new StringBuilder();
        sb.append("You are an expert SAT tutor writing concise answer-choice explanations.\n\n");
        sb.append("QUESTION\n");
        sb.append("Section: ").append(q.getSection()).append("\n");
        sb.append("Skill: ").append(q.getSkill()).append("\n");
        sb.append("Stem: ").append(q.getQuestionStem()).append("\n\n");
        sb.append("Answer choices:\n");
        sb.append("A) ").append(q.getOptionA()).append("\n");
        sb.append("B) ").append(q.getOptionB()).append("\n");
        sb.append("C) ").append(q.getOptionC()).append("\n");
        sb.append("D) ").append(q.getOptionD()).append("\n\n");
        sb.append("Correct answer: ").append(correctAnswer).append("\n\n");

        if (q.getTrapExplanation() != null) {
            sb.append("Common mistake context: ").append(q.getTrapExplanation()).append("\n\n");
        }

        sb.append("""
For EACH answer choice (A, B, C, D), write a 1–2 sentence explanation:
- For the CORRECT choice: explain precisely WHY it is correct.
- For each WRONG choice: explain the specific misconception or error that leads a student there.

Return ONLY valid JSON (no markdown fences):
{
  "A": "explanation for choice A",
  "B": "explanation for choice B",
  "C": "explanation for choice C",
  "D": "explanation for choice D"
}

Rules:
- Each explanation: 1–2 sentences, max 40 words
- Be specific to this question — no generic statements
- Use plain English (no LaTeX)
- Wrong choice explanations should name the specific error/trap
""");

        return sb.toString();
    }

    private void validate(JsonNode result, Question q) {
        for (String letter : new String[]{"A", "B", "C", "D"}) {
            // Only validate letters that have actual options
            boolean hasOption = switch (letter) {
                case "A" -> q.getOptionA() != null;
                case "B" -> q.getOptionB() != null;
                case "C" -> q.getOptionC() != null;
                case "D" -> q.getOptionD() != null;
                default  -> false;
            };
            if (hasOption && (result.path(letter).isMissingNode() || result.path(letter).asText("").isBlank())) {
                throw new IllegalStateException("Missing explanation for choice " + letter);
            }
        }
    }

    @Transactional
    void save(Question q, String choiceExplanationsJson) {
        q.setChoiceExplanations(choiceExplanationsJson);
        questionRepository.save(q);
    }

    private String padEnd(String s, int len) {
        if (s == null) s = "";
        return s.length() >= len ? s : s + " ".repeat(len - s.length());
    }
}
