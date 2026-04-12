package com.satengine.dto;

import java.util.UUID;

/**
 * Per-question answer detail for session review.
 * Includes the correct answer (safe to expose post-submission).
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
        String explanationShort
) {}
