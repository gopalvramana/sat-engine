package com.satengine.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

/**
 * Request body for creating a new practice session.
 * section            — optional; null means any section.
 * domainCounts       — map of domain → desired question count.
 * domainDifficulties — optional per-domain difficulty ranges:
 *                      { "algebra": {"min":1,"max":5}, "geometry_trigonometry": {"min":6,"max":7} }
 *                      Omitted domains default to full range (1–7).
 */
public record CreateSessionRequest(
        @NotBlank String sessionType,
        String section,
        Map<String, Integer> domainCounts,
        Map<String, Map<String, Integer>> domainDifficulties
) {
}
