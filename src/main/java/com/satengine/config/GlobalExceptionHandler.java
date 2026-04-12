package com.satengine.config;

import com.satengine.exception.DuplicateAnswerException;
import com.satengine.exception.InvalidRequestException;
import com.satengine.exception.ResourceNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 404 — entity not found (Session, Question, Answer, etc.).
     */
    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<Map<String, String>> handleNotFound(
            ResourceNotFoundException ex, HttpServletRequest request) {
        log.debug("not found: {} [{} {}]", ex.getMessage(), request.getMethod(), request.getRequestURI());
        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(Map.of("error", ex.getMessage()));
    }

    /**
     * 409 — student tried to answer the same question twice in one session.
     */
    @ExceptionHandler(DuplicateAnswerException.class)
    public ResponseEntity<Map<String, String>> handleDuplicateAnswer(
            DuplicateAnswerException ex, HttpServletRequest request) {
        log.debug("duplicate answer: {} [{} {}]", ex.getMessage(), request.getMethod(), request.getRequestURI());
        return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(Map.of("error", ex.getMessage()));
    }

    /**
     * 400 — application-level validation failure (bad field value, missing required data, etc.).
     */
    @ExceptionHandler(InvalidRequestException.class)
    public ResponseEntity<Map<String, String>> handleInvalidRequest(
            InvalidRequestException ex, HttpServletRequest request) {
        log.debug("invalid request: {} [{} {}]", ex.getMessage(), request.getMethod(), request.getRequestURI());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", ex.getMessage()));
    }

    /**
     * 400 — invalid path/query parameter type (e.g. "not-a-uuid" where UUID is expected).
     */
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<Map<String, String>> handleTypeMismatch(
            MethodArgumentTypeMismatchException ex, HttpServletRequest request) {
        String msg = "Invalid value for parameter '" + ex.getName() + "': " + ex.getValue();
        log.debug("type mismatch: {} [{} {}]", msg, request.getMethod(), request.getRequestURI());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", msg));
    }

    /**
     * 400 — Bean Validation failures (@NotNull, @NotBlank, etc.).
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidationException(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        String errors = ex.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .collect(Collectors.joining("; "));
        log.debug("validation failed: {} [{} {}]", errors, request.getMethod(), request.getRequestURI());
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(Map.of("error", errors));
    }

    /**
     * 500 — unexpected RuntimeException (programming error, DB failure, etc.).
     * Logs full stack trace so we can debug; returns generic message to client.
     */
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<Map<String, String>> handleRuntimeException(
            RuntimeException ex, HttpServletRequest request) {
        log.error("Unhandled RuntimeException on {} {}: {}", request.getMethod(), request.getRequestURI(),
                ex.getMessage(), ex);
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "An unexpected error occurred"));
    }

    /**
     * 500 — catch-all for unexpected checked exceptions.
     * Logs full stack trace so we can debug; returns generic message to client.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGenericException(
            Exception ex, HttpServletRequest request) {
        log.error("Unhandled Exception on {} {}: {}", request.getMethod(), request.getRequestURI(),
                ex.getMessage(), ex);
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(Map.of("error", "An unexpected error occurred"));
    }
}
