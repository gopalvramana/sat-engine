package com.satengine.dto;

/**
 * One pre-queued question in a SAT-style session.
 * Includes position (0-based), mark state, any existing answer (for resume),
 * and the full question payload.
 */
public record SessionQuestionResponse(
        int     position,
        boolean marked,
        String  existingAnswer,   // null if not yet answered; populated on resume
        QuestionResponse question
) {}
