package com.satengine.exception;

/**
 * Thrown when incoming request data is structurally invalid beyond bean-validation constraints.
 * Maps to HTTP 400 Bad Request in GlobalExceptionHandler.
 */
public class InvalidRequestException extends RuntimeException {

    public InvalidRequestException(String message) {
        super(message);
    }
}
