package com.satengine.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.util.UUID;

/**
 * Request body for submitting a student's answer to a question.
 */
public record SubmitAnswerRequest(
        @NotNull UUID questionId,
        @NotBlank String studentAnswer,
        Integer timeSpentSeconds
) {
}
