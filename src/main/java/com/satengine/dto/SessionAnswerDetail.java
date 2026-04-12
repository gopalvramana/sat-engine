package com.satengine.dto;

import java.util.UUID;

/**
 * Per-question answer detail for session review.
 * Includes the correct answer (safe to expose post-submission) and full
 * question data needed to render the review page.
 */
public record SessionAnswerDetail(
        UUID questionId,
        String questionStem,
        String domain,
        String skill,
        Short difficulty,
        String questionType,
        String optionA,
        String optionB,
        String optionC,
        String optionD,
        String correctAnswer,
        String studentAnswer,
        Boolean isCorrect,
        Integer timeSpentSeconds,
        String explanationShort,
        String explanationSteps,
        String coreConceptJson,
        String choiceExplanations,
        String alternativeApproach,
        String animationJson,
        String diagramJson,
        String passageText,
        String passageSource,
        String skillKey
) {}
