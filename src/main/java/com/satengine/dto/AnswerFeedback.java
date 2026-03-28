package com.satengine.dto;

import java.util.UUID;

/**
 * Feedback returned after a student submits an answer.
 * This is the ONLY place the correct answer is revealed to the client —
 * and only after the student has already submitted their response.
 */
public record AnswerFeedback(
        UUID questionId,
        boolean isCorrect,
        String correctAnswer,
        String explanationShort,
        String explanationSteps
) {
}
