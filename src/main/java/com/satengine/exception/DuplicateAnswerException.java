package com.satengine.exception;

/**
 * Thrown when a student tries to answer the same question twice in one session.
 * Maps to HTTP 409 Conflict in GlobalExceptionHandler.
 */
public class DuplicateAnswerException extends RuntimeException {

    public DuplicateAnswerException(Object sessionId, Object questionId) {
        super("Question " + questionId + " already answered in session " + sessionId);
    }
}
