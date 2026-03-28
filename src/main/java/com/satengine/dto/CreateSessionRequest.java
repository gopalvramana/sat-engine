package com.satengine.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * Request body for creating a new practice session.
 * section is optional — null means any section.
 */
public record CreateSessionRequest(
        @NotBlank String sessionType,
        String section
) {
}
