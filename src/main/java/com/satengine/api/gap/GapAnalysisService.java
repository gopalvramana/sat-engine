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

    private static final String MODEL      = "claude-haiku-4-5-20251001";
    private static final int    MAX_TOKENS = 4096;

    /**
     * Generates AI diagnostic probes + gap lessons for a student who answered wrong.
     * Returns raw JSON string matching the probe/lesson schema used by find-my-gap.html.
     */
    public String analyze(UUID questionId, String studentAnswer) {
        Question q = questionRepository.findById(questionId)
                .orElseThrow(() -> new IllegalArgumentException("Question not found: " + questionId));

        QuestionAnswer qa = questionAnswerRepository.findByQuestionId(questionId)
                .orElseThrow(() -> new IllegalArgumentException("Answer not found for: " + questionId));

        String prompt = buildPrompt(q, qa.getCorrectAnswer(), studentAnswer);
        String raw = claudeClient.call(MODEL, MAX_TOKENS, "", prompt);

        // Strip ```json ... ``` fences if present
        String cleaned = raw.replaceAll("(?i)^```json\\s*", "")
                            .replaceAll("\\s*```$", "")
                            .strip();

        // Validate it's parseable JSON before returning
        try {
            objectMapper.readTree(cleaned);
        } catch (Exception e) {
            log.error("Gap analysis returned invalid JSON for question {}: {}", questionId, e.getMessage());
            throw new RuntimeException("Gap analysis returned invalid JSON", e);
        }

        log.info("Gap analysis generated for question {} (student={}, correct={})",
                q.getExternalId(), studentAnswer, qa.getCorrectAnswer());
        return cleaned;
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
