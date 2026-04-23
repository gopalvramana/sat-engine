package com.satengine.pipeline.sympy;

/**
 * Thrown when math_engine.py exits non-zero or produces invalid output.
 * Always retried up to the configured max-attempts before propagating.
 */
public class MathTemplateException extends RuntimeException {

    public MathTemplateException(String message) {
        super(message);
    }

    public MathTemplateException(String message, Throwable cause) {
        super(message, cause);
    }
}
