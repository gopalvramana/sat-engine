package com.satengine.pipeline.sympy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/**
 * Validates Haiku's narration output against known format bug classes.
 *
 * Three rules — all flag-only (non-blocking). Violations are added to
 * {@code reviewNotes} and the question is saved with
 * {@code status = "generated_flagged"} for human review.
 *
 * <ol>
 *   <li><b>stem_contamination</b> — answer choices "A. ", "B. ", "C. ", "D. "
 *       leaking into the {@code questionStem} field.</li>
 *   <li><b>latex_wrapper_missing</b> — LaTeX commands (\frac, \leq, etc.)
 *       appearing outside \(...\) wrappers. Conservative: only catches
 *       backslash-commands; numeric equations are not flagged (too many FPs).</li>
 *   <li><b>rationale_hygiene</b> — thinking-out-loud artifacts
 *       ("wait", "hmm", "actually", "let me see", …) in student-facing prose.</li>
 * </ol>
 */
@Slf4j
@Service
public class NarrationFormatValidator {

    /** Rule 1: answer choices leaking into the stem. */
    private static final Pattern STEM_CHOICE_LEAK =
            Pattern.compile("\\s[A-D]\\.\\s");

    /**
     * Rule 2: LaTeX backslash-commands. Conservative list — only commands
     * that unambiguously indicate math content. Numeric equations and
     * exponents are intentionally NOT matched to avoid false positives on
     * ordinary prose like "the student bought 3 items" or "5 = 2 + 3".
     */
    private static final Pattern LATEX_COMMAND =
            Pattern.compile("\\\\(frac|leq|geq|neq|cdot|sqrt|pm|times|div|le|ge)\\b");

    /** Matches \(...\) inline and \[...\] display blocks for stripping before Rule 2 check. */
    private static final Pattern LATEX_WRAPPER =
            Pattern.compile("\\\\\\(.*?\\\\\\)|\\\\\\[.*?\\\\\\]", Pattern.DOTALL);

    /** Rule 3: thinking-out-loud artifacts. */
    private static final Pattern HYGIENE = Pattern.compile(
            "\\b(wait|hmm|let me (?:see|think|check)|i think)\\b"
            + "|that['\u2019]s not"
            + "|\\boh[,!\\s]"
            // "actually" only flags when thinking-out-loud (sentence-start);
            // mid-sentence uses like "which is actually represented by" or "the line actually
            // crosses" are clarifying language. Lookbehinds cover common mid-sentence contexts.
            + "|(?<!is )(?<!was )(?<!are )(?<!which )(?<!that )(?<!and )"
            + "(?<!the )(?<!line )(?<!tion )(?<!from )(?<!this )\\bactually\\b",
            Pattern.CASE_INSENSITIVE
    );

    /**
     * Validates the parsed Haiku narration and returns a list of violation
     * labels. Empty list = clean. Labels are of the form
     * {@code rule_name:field_path}.
     */
    public List<String> validate(JsonNode narration) {
        List<String> violations = new ArrayList<>();
        if (narration == null || narration.isMissingNode()) {
            return violations;
        }

        // Rule 1: stem contamination — only applies to questionStem
        String stem = narration.path("questionStem").asText("");
        if (!stem.isEmpty() && STEM_CHOICE_LEAK.matcher(stem).find()) {
            violations.add("stem_contamination:questionStem");
        }

        // Rules 2 & 3 on student-facing prose fields
        checkText(stem, "questionStem", violations);
        checkText(narration.path("explanationShort").asText(""),
                  "explanationShort", violations);
        checkText(narration.path("coreConcept").asText(""),
                  "coreConcept", violations);

        JsonNode steps = narration.path("explanationSteps");
        if (steps.isArray()) {
            for (int i = 0; i < steps.size(); i++) {
                String content = steps.get(i).path("content").asText("");
                checkText(content, "explanationSteps[" + i + "].content", violations);
            }
        }

        // Rule 3 only on distractorRationale values (per-letter map)
        JsonNode drs = narration.path("distractorRationale");
        if (drs.isObject()) {
            drs.fields().forEachRemaining(entry -> {
                String text = entry.getValue().asText("");
                if (!text.isEmpty() && HYGIENE.matcher(text).find()) {
                    violations.add("rationale_hygiene:distractorRationale." + entry.getKey());
                }
            });
        }

        return violations;
    }

    /** Apply Rule 2 (LaTeX wrapper) and Rule 3 (hygiene) to a single text field. */
    private void checkText(String text, String field, List<String> violations) {
        if (text == null || text.isEmpty()) return;

        // Rule 2: strip \(...\) regions, then scan for naked LaTeX commands
        String stripped = LATEX_WRAPPER.matcher(text).replaceAll("");
        if (LATEX_COMMAND.matcher(stripped).find()) {
            violations.add("latex_wrapper_missing:" + field);
        }

        // Rule 3: thinking-out-loud artifacts
        if (HYGIENE.matcher(text).find()) {
            violations.add("rationale_hygiene:" + field);
        }
    }

    // ── Auto-fixer ────────────────────────────────────────────────────────────

    /**
     * Attempt to repair {@code latex_wrapper_missing} violations in-place on
     * the parsed Haiku narration {@link ObjectNode}.
     *
     * <p>Only {@code explanationSteps[N].content} fields are repaired — those
     * are the fields where Haiku most commonly drops the {@code \(...\)} wrapper
     * around a trailing equation (e.g. {@code "Divide both sides by 4: \frac{46}{4} = \frac{23}{2}"}).
     *
     * <p>Two fix strategies are tried in order:
     * <ol>
     *   <li><b>Colon split</b> — if the content contains {@code ": "} before the
     *       first bare LaTeX command, keep the prose prefix and wrap only the
     *       math suffix in {@code \(...\)}.</li>
     *   <li><b>Full wrap</b> — if the content starts with a math token
     *       ({@code \}, digit, or a single variable letter followed by space/=),
     *       wrap the entire field.</li>
     * </ol>
     *
     * The method is idempotent and never corrupts already-clean fields.
     * Re-run {@link #validate(JsonNode)} after calling this to confirm repairs.
     */
    public void autoFix(ObjectNode narration) {
        if (narration == null) return;

        JsonNode steps = narration.path("explanationSteps");
        if (!steps.isArray()) return;

        ArrayNode stepsArray = (ArrayNode) steps;
        for (int i = 0; i < stepsArray.size(); i++) {
            JsonNode stepNode = stepsArray.get(i);
            if (!stepNode.isObject()) continue;
            ObjectNode step = (ObjectNode) stepNode;

            String content = step.path("content").asText("");
            if (content.isEmpty()) continue;

            // Only attempt fix if this field actually has a naked LaTeX command
            String stripped = LATEX_WRAPPER.matcher(content).replaceAll("");
            if (!LATEX_COMMAND.matcher(stripped).find()) continue;

            String fixed = attemptFix(content);
            if (!fixed.equals(content)) {
                step.put("content", fixed);
                log.debug("autoFix repaired explanationSteps[{}].content", i);
            }
        }
    }

    /**
     * Try to wrap bare LaTeX in a single content string.
     *
     * @return the fixed string, or the original if no safe fix was found.
     */
    private String attemptFix(String text) {
        // Strategy 1: split on the LAST ": " that precedes the first bare LaTeX command.
        // e.g. "Divide both sides by 4: \frac{46}{4} = \frac{23}{2}"
        //   → "Divide both sides by 4: \(\frac{46}{4} = \frac{23}{2}\)"
        int firstBareLatex = findFirstBareLatexPos(text);
        if (firstBareLatex > 0) {
            // Look backward from firstBareLatex for a ": " split
            int colonIdx = text.lastIndexOf(": ", firstBareLatex);
            if (colonIdx >= 0) {
                String prose = text.substring(0, colonIdx + 1); // includes ":"
                String math  = text.substring(colonIdx + 1).stripLeading();
                // Only wrap if the math portion actually contains the bare LaTeX
                String strippedMath = LATEX_WRAPPER.matcher(math).replaceAll("");
                if (LATEX_COMMAND.matcher(strippedMath).find()) {
                    return prose + " \\(" + math + "\\)";
                }
            }
        }

        // Strategy 2: entire content appears to be a math expression
        // (starts with \command, a digit, or "x =" / "y =" style)
        String trimmed = text.trim();
        if (trimmed.startsWith("\\") ||
            trimmed.matches("^[0-9].*") ||
            trimmed.matches("^[a-zA-Z]\\s*[=+\\-].*")) {
            String strippedAll = LATEX_WRAPPER.matcher(trimmed).replaceAll("");
            if (LATEX_COMMAND.matcher(strippedAll).find()) {
                return "\\(" + trimmed + "\\)";
            }
        }

        return text; // could not fix safely — leave for human review
    }

    /**
     * Returns the index of the first bare (unwrapped) LaTeX command in {@code text},
     * or -1 if all LaTeX commands are properly wrapped.
     */
    private int findFirstBareLatexPos(String text) {
        // Walk through \(...\) blocks and find the first \command outside them
        java.util.regex.Matcher wrapperMatcher = LATEX_WRAPPER.matcher(text);
        // Build a list of wrapped ranges to skip
        List<int[]> wrappedRanges = new ArrayList<>();
        while (wrapperMatcher.find()) {
            wrappedRanges.add(new int[]{wrapperMatcher.start(), wrapperMatcher.end()});
        }

        java.util.regex.Matcher cmdMatcher = LATEX_COMMAND.matcher(text);
        while (cmdMatcher.find()) {
            int pos = cmdMatcher.start();
            boolean insideWrapper = wrappedRanges.stream()
                    .anyMatch(r -> pos >= r[0] && pos < r[1]);
            if (!insideWrapper) return pos;
        }
        return -1;
    }
}
