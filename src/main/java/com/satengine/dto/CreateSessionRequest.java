package com.satengine.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

/**
 * Request body for creating a new practice session.
 * section      — optional; null means any section.
 * domainCounts — optional map of domain → desired question count.
 *                When provided, questions are drawn per-domain until quotas are met.
 *                Example: {"algebra":3,"geometry_trigonometry":4,"problem_solving_data":3}
 */
public record CreateSessionRequest(
        @NotBlank String sessionType,
        String section,
        Map<String, Integer> domainCounts
) {
}
