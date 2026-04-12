package com.satengine.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

/**
 * Request body for creating a new practice session.
 *
 * domainBandCounts — granular per-domain per-difficulty-band question counts:
 *   { "algebra": { "easy": 2, "medium": 5, "hard": 1 },
 *     "geometry_trigonometry": { "easy": 3, "medium": 2 } }
 * Bands: easy=1-2, medium=3-5, hard=6-7.
 * Bands with count 0 or absent are skipped.
 */
public record CreateSessionRequest(
        @NotBlank String sessionType,
        String section,
        Map<String, Map<String, Integer>> domainBandCounts,
        Boolean timedMode,      // reserved — future timed-exam mode, ignored for now
        Integer moduleNumber    // reserved — future multi-module support, ignored for now
) {}
