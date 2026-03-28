package com.satengine.dto;

import java.time.OffsetDateTime;
import java.util.UUID;

/**
 * Response DTO representing the current state of a session.
 */
public record SessionResponse(
        UUID id,
        String sessionType,
        String section,
        String status,
        OffsetDateTime startedAt,
        int questionsAnswered,
        int correctCount
) {
}
