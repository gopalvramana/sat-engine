package com.satengine.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

/**
 * Request body for creating a new practice session.
 * section       — optional; null means any section.
 * domainCounts  — map of domain → desired question count.
 * minDifficulty — inclusive lower bound (1–7), default 1.
 * maxDifficulty — inclusive upper bound (1–7), default 7.
 */
public record CreateSessionRequest(
        @NotBlank String sessionType,
        String section,
        Map<String, Integer> domainCounts,
        Integer minDifficulty,
        Integer maxDifficulty
) {
}
