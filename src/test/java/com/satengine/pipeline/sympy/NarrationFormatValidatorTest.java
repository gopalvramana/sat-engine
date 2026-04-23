package com.satengine.pipeline.sympy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class NarrationFormatValidatorTest {

    private final ObjectMapper mapper = new ObjectMapper();
    private NarrationFormatValidator validator;

    @BeforeEach
    void setUp() {
        validator = new NarrationFormatValidator();
    }

    private JsonNode parse(String json) throws Exception {
        return mapper.readTree(json);
    }

    // ── Rule 1: stem_contamination ───────────────────────────────────────────

    @Nested
    @DisplayName("Rule 1: stem_contamination")
    class StemContamination {

        @Test
        void cleanStemPasses() throws Exception {
            JsonNode n = parse("{\"questionStem\": \"What is the value of x?\"}");
            assertThat(validator.validate(n)).isEmpty();
        }

        @Test
        void leakedChoicesFlagged() throws Exception {
            JsonNode n = parse("{\"questionStem\": \"What is x? A. 5 B. 7 C. 10 D. 12\"}");
            assertThat(validator.validate(n))
                    .anyMatch(v -> v.startsWith("stem_contamination:questionStem"));
        }

        @Test
        void bareLetterDoesNotLeak() throws Exception {
            JsonNode n = parse("{\"questionStem\": \"Point A is located at x=3.\"}");
            List<String> v = validator.validate(n);
            assertThat(v).noneMatch(s -> s.startsWith("stem_contamination"));
        }
    }

    // ── Rule 2: latex_wrapper_missing ────────────────────────────────────────

    @Nested
    @DisplayName("Rule 2: latex_wrapper_missing")
    class LatexWrapper {

        @Test
        void wrappedLatexPasses() throws Exception {
            JsonNode n = parse("{\"explanationShort\": \"Solve \\\\(\\\\frac{1}{2}x = 3\\\\)\"}");
            assertThat(validator.validate(n))
                    .noneMatch(v -> v.startsWith("latex_wrapper_missing"));
        }

        @Test
        void nakedLatexCommandFlagged() throws Exception {
            JsonNode n = parse("{\"explanationShort\": \"Compute \\\\frac{1}{2} directly.\"}");
            assertThat(validator.validate(n))
                    .anyMatch(v -> v.startsWith("latex_wrapper_missing:explanationShort"));
        }

        @Test
        void plainProseWithNumbersPasses() throws Exception {
            // Conservative rule — numeric equations alone don't flag
            JsonNode n = parse("{\"explanationShort\": \"Student bought 3 items at $5 each = $15 total.\"}");
            assertThat(validator.validate(n))
                    .noneMatch(v -> v.startsWith("latex_wrapper_missing"));
        }

        @Test
        void nakedLeqFlagged() throws Exception {
            JsonNode n = parse("{\"coreConcept\": \"The inequality x \\\\leq 10 means...\"}");
            assertThat(validator.validate(n))
                    .anyMatch(v -> v.startsWith("latex_wrapper_missing:coreConcept"));
        }
    }

    // ── Rule 3: rationale_hygiene ────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 3: rationale_hygiene")
    class Hygiene {

        @Test
        void cleanRationalePasses() throws Exception {
            JsonNode n = parse("{\"distractorRationale\": {\"B\": \"Student subtracted incorrectly.\"}}");
            assertThat(validator.validate(n))
                    .noneMatch(v -> v.startsWith("rationale_hygiene"));
        }

        @Test
        void thinkingOutLoudFlagged() throws Exception {
            JsonNode n = parse("{\"distractorRationale\": {\"B\": \"Actually, the student flipped the sign.\"}}");
            assertThat(validator.validate(n))
                    .anyMatch(v -> v.startsWith("rationale_hygiene:distractorRationale.B"));
        }

        @Test
        void waitInProseFlagged() throws Exception {
            JsonNode n = parse("{\"explanationShort\": \"Wait, we need to subtract first.\"}");
            assertThat(validator.validate(n))
                    .anyMatch(v -> v.startsWith("rationale_hygiene:explanationShort"));
        }

        @Test
        void letMeCheckFlagged() throws Exception {
            JsonNode n = parse("{\"explanationShort\": \"Let me check that calculation.\"}");
            assertThat(validator.validate(n))
                    .anyMatch(v -> v.startsWith("rationale_hygiene:explanationShort"));
        }

        @Test
        void ordinaryWaitTimeDoesNotFlag() throws Exception {
            // "wait time" is a domain phrase — but "wait" as standalone word IS flagged.
            // Conservative: flag on any word-boundary "wait". Acceptable false-positive
            // since human reviews; better than missing real hygiene issues.
            JsonNode n = parse("{\"explanationShort\": \"The average wait time was 5 minutes.\"}");
            List<String> v = validator.validate(n);
            // This will flag, documenting the known over-match.
            assertThat(v).anyMatch(s -> s.startsWith("rationale_hygiene"));
        }
    }

    // ── Multi-field & clean ─────────────────────────────────────────────────

    @Test
    void completelyCleanNarrationReturnsEmpty() throws Exception {
        String json = "{"
                + "\"questionStem\": \"What is the value of x when 2x + 3 is 11?\","
                + "\"explanationShort\": \"Subtract 3, then divide by 2.\","
                + "\"explanationSteps\": [{\"step\": 1, \"title\": \"Isolate\", \"content\": \"Move 3 to the right side.\"}],"
                + "\"coreConcept\": \"Linear equations isolate x with inverse operations.\","
                + "\"distractorRationale\": {\"B\": \"Student forgot to divide by 2.\"}"
                + "}";
        assertThat(validator.validate(parse(json))).isEmpty();
    }

    @Test
    void nullNarrationReturnsEmpty() {
        assertThat(validator.validate(null)).isEmpty();
    }

    @Test
    void missingFieldsDoNotCrash() throws Exception {
        assertThat(validator.validate(parse("{}"))).isEmpty();
    }

    @Test
    void multipleViolationsAllReported() throws Exception {
        String json = "{"
                + "\"questionStem\": \"What is x? A. 5 B. 10 C. 15 D. 20\","
                + "\"explanationShort\": \"Actually, compute \\\\frac{x}{2}.\""
                + "}";
        List<String> violations = validator.validate(parse(json));
        assertThat(violations).anyMatch(v -> v.startsWith("stem_contamination"));
        assertThat(violations).anyMatch(v -> v.startsWith("rationale_hygiene"));
        assertThat(violations).anyMatch(v -> v.startsWith("latex_wrapper_missing"));
    }
}
