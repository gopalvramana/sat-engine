package com.satengine.pipeline.sympy;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * Deserialized MathObject JSON produced by math_engine.py on stdout.
 *
 * Example:
 * {
 *   "skill":          "linear_eq_one_var",
 *   "difficulty":     3,
 *   "questionType":   "mcq",
 *   "params":         { "a": 3, "b": 7, "c": 22 },
 *   "paramHash":      "a1b2c3...",
 *   "verifiedAnswer": "5",
 *   "distractors":    ["3", "8", "1"],
 *   "sprMin":         null,
 *   "sprMax":         null,
 *   "scenarioTag":    null,
 *   "diagramSpec":    null
 * }
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record MathObject(

        @JsonProperty("skill")          String skill,
        @JsonProperty("difficulty")     int difficulty,
        @JsonProperty("questionType")   String questionType,
        @JsonProperty("params")         Map<String, Object> params,
        @JsonProperty("paramHash")      String paramHash,
        @JsonProperty("verifiedAnswer") String verifiedAnswer,
        @JsonProperty("distractors")    List<String> distractors,
        @JsonProperty("sprMin")         BigDecimal sprMin,
        @JsonProperty("sprMax")         BigDecimal sprMax,
        @JsonProperty("scenarioTag")    String scenarioTag,
        @JsonProperty("diagramSpec")    Map<String, Object> diagramSpec,

        /**
         * Explicit instruction for Haiku: what quantity to ask for and why verifiedAnswer
         * is the correct answer. Prevents LLM from asking about the wrong derived value.
         */
        @JsonProperty("questionContext") String questionContext,

        /**
         * When set, Java uses this as the questionStem verbatim — Haiku's generated stem
         * is discarded. Use for deterministic templates where the stem is fully formulaic
         * and must not be rewritten (e.g. translate_intercept, function_shift).
         */
        @JsonProperty("exactStem")       String exactStem,

        /** Present when Python emitted an error line instead of a valid object. */
        @JsonProperty("error")          String error
) {
    public boolean hasError() {
        return error != null && !error.isBlank();
    }
}
