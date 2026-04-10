package com.satengine.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

import java.util.UUID;

/**
 * Request body for submitting a student's answer to a question.
 *
 * studentAnswer is capped at 10 characters to match the student_answer
 * VARCHAR(10) column — validation fires before the DB is touched so the
 * client gets a 400 instead of a 500 on overflow.
 */
public record SubmitAnswerRequest(
        @NotNull UUID questionId,
        @NotBlank @Size(max = 10, message = "must be 10 characters or fewer") String studentAnswer,
        Integer timeSpentSeconds
) {
}
