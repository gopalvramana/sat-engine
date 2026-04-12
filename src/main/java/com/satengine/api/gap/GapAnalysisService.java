package com.satengine.api.gap;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.pipeline.claude.ClaudeClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class GapAnalysisService {

    private final QuestionRepository       questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final ClaudeClient             claudeClient;
    private final ObjectMapper             objectMapper;

    private static final String MODEL        = "claude-haiku-4-5-20251001";
    private static final int    MAX_TOKENS   = 4096;
    private static final int    MAX_ATTEMPTS = 2;

    /**
     * Fallback returned when all Claude attempts fail so the student never sees a raw error.
     * Structured identically to a real gap response — the React component renders it normally.
     */
    private static final String FALLBACK_GAP = """
            {
              "gaps": [{
                "trigger": "I want to review this question",
                "title": "Gap: Review the Solution Steps",
                "body": "Work through the step-by-step solution shown above. Focus on the step where your approach first diverged from the correct method.",
                "example": "Compare your working to each solution step to identify exactly where the mistake occurred.",
                "takeaway": "Understanding the method matters more than just knowing the answer."
              }]
            }
            """;

    /**
     * Generates AI diagnostic gap cards for a student who answered wrong.
     * Retries once on transient failure; returns a generic fallback if both attempts fail
     * so the student always sees something useful instead of an error.
     */
    public String analyze(UUID questionId, String studentAnswer) {
        Question q = questionRepository.findById(questionId)
                .orElseThrow(() -> new IllegalArgumentException("Question not found: " + questionId));

        QuestionAnswer qa = questionAnswerRepository.findByQuestionId(questionId)
                .orElseThrow(() -> new IllegalArgumentException("Answer not found for: " + questionId));

        String prompt = buildPrompt(q, qa.getCorrectAnswer(), studentAnswer);

        Exception lastError = null;
        for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
            try {
                log.info("gap analysis claude call start questionId={} attempt={}/{}", questionId, attempt, MAX_ATTEMPTS);
                long callStart = System.currentTimeMillis();
                String raw = claudeClient.call(MODEL, MAX_TOKENS, "", prompt);
                long callMs = System.currentTimeMillis() - callStart;

                // Strip ```json ... ``` fences if present
                String cleaned = raw.replaceAll("(?i)^```json\\s*", "")
                                    .replaceAll("\\s*```$", "")
                                    .strip();

                objectMapper.readTree(cleaned); // validate parseable JSON

                log.info("gap analysis claude call done questionId={} durationMs={}{}",
                        questionId, callMs,
                        attempt > 1 ? " attempt=" + attempt : "");
                return cleaned;

            } catch (Exception e) {
                lastError = e;
                log.warn("gap analysis attempt {}/{} failed questionId={} error={}",
                        attempt, MAX_ATTEMPTS, questionId, e.getMessage());
                if (attempt < MAX_ATTEMPTS) {
                    try { Thread.sleep(500); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); }
                }
            }
        }

        log.error("gap analysis failed after {} attempts questionId={} — returning fallback. error={}",
                MAX_ATTEMPTS, questionId, lastError.getMessage(), lastError);
        return FALLBACK_GAP.strip();
    }

    private String buildPrompt(Question q, String correctAnswer, String studentAnswer) {
        // Build a compact question representation for the prompt
        StringBuilder sb = new StringBuilder();

        sb.append("You are a diagnostic SAT tutor. A student answered an SAT ")
          .append(q.getSection() != null ? q.getSection().replace("_", " ") : "math")
          .append(" question incorrectly.\n\n");

        sb.append("QUESTION (Domain: ").append(q.getDomain())
          .append(", Skill: ").append(q.getSkill())
          .append(", Difficulty: ").append(q.getDifficulty()).append("/7)\n");

        sb.append("Stem: ").append(q.getQuestionStem()).append("\n");

        if (q.getOptionA() != null) sb.append("A) ").append(q.getOptionA()).append("\n");
        if (q.getOptionB() != null) sb.append("B) ").append(q.getOptionB()).append("\n");
        if (q.getOptionC() != null) sb.append("C) ").append(q.getOptionC()).append("\n");
        if (q.getOptionD() != null) sb.append("D) ").append(q.getOptionD()).append("\n");

        sb.append("Correct answer: ").append(correctAnswer).append("\n");
        sb.append("Student chose: ").append(studentAnswer).append("\n\n");

        if (q.getTrapExplanation() != null) {
            sb.append("Common mistake: ").append(q.getTrapExplanation()).append("\n\n");
        }

        if (q.getExplanationSteps() != null) {
            sb.append("Solution approach (for context):\n");
            try {
                JsonNode steps = objectMapper.readTree(q.getExplanationSteps());
                if (steps.isArray()) {
                    for (JsonNode step : steps) {
                        sb.append("- ").append(step.path("title").asText())
                          .append(": ").append(step.path("content").asText()).append("\n");
                    }
                }
            } catch (Exception e) {
                sb.append(q.getExplanationSteps()).append("\n");
            }
            sb.append("\n");
        }

        sb.append("Student chose ").append(studentAnswer)
          .append(" instead of ").append(correctAnswer).append(".\n\n");

        sb.append("""
Generate 2-3 gap cards explaining the most likely reasons this student got it wrong.
The FIRST card must address the most probable misconception given the specific wrong answer they chose.

Return ONLY valid JSON (no markdown, no explanation):
{
  "gaps": [
    {
      "trigger": "I didn't know [concept in 6 words or less]",
      "title": "Gap: [Concept Name]",
      "body": "2-4 sentence explanation of the missing concept. Use \\\\( LaTeX \\\\) for math.",
      "example": "Worked example applying this concept (2-4 lines). Use \\\\( LaTeX \\\\) for math.",
      "takeaway": "One sentence key rule to remember."
    },
    {
      "trigger": "I confused [thing A] with [thing B]",
      "title": "Gap: [Second Concept]",
      "body": "...",
      "example": "...",
      "takeaway": "..."
    }
  ]
}

Rules:
- 2-3 gap cards total
- trigger: starts with "I ", plain English, max 8 words, no math symbols
- title: starts with "Gap: "
- body: 2-4 sentences, use \\\\( ... \\\\) for inline LaTeX
- example: concrete and specific to this question type
- takeaway: exactly 1 sentence
""");

        return sb.toString();
    }
}
