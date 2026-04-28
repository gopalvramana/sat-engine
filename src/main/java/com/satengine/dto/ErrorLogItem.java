package com.satengine.dto;

import java.util.UUID;

/**
 * One wrong-answer entry returned by GET /api/error-log.
 */
public record ErrorLogItem(
        UUID questionId,
        UUID sessionId,
        String questionStem,
        String domain,
        String skillKey,
        Short  difficulty,
        String correctAnswer,
        String studentAnswer,
        Integer timeSpentSeconds,
        String answeredAt          // ISO-8601 offset date-time string
) {}
