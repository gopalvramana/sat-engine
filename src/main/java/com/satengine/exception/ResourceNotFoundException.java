package com.satengine.exception;

/**
 * Thrown when a requested entity (session, question, answer) does not exist.
 * Maps to HTTP 404 in GlobalExceptionHandler.
 */
public class ResourceNotFoundException extends RuntimeException {

    public ResourceNotFoundException(String message) {
        super(message);
    }

    public ResourceNotFoundException(String resource, Object id) {
        super(resource + " not found: " + id);
    }
}
