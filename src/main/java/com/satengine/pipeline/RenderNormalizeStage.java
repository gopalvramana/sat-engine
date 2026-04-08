package com.satengine.pipeline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.regex.*;

/**
 * Scans text fields of newly-generated questions and fixes math rendering issues:
 *
 *   Problem: Claude sometimes emits  $4 < h \leq 7$  (digit-starting $...$  with spaces).
 *            The processText() renderer regex only accepts digit-starting tokens WITHOUT
 *            spaces (to avoid matching currency like "$5 per hour").  As a result such
 *            expressions render as raw text in the browser.
 *
 *   Fix:     Convert any $...$ that looks like math (contains LaTeX commands or operators)
 *            to \(...\) so the renderer handles it unambiguously.
 *
 * Default scope: questions with status=generated (newly generated, not yet reviewed).
 *
 * Usage:
 *   --job=render-normalize                           fix newly generated questions
 *   --job=render-normalize --dry-run                 scan only, no DB writes
 *   --job=render-normalize --all                     scan all questions regardless of status
 *   --job=render-normalize --section=math            scope to a section
 *   --job=render-normalize --domain=algebra          scope to a domain
 *   --job=render-normalize --id=MATH-ALG-031         single question (any status)
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RenderNormalizeStage {

    private final QuestionRepository questionRepository;
    private final ObjectMapper       objectMapper;

    // Matches any $...$ token (lazy, single-line content)
    private static final Pattern DOLLAR_MATH = Pattern.compile("\\$([^$\\\\]|\\\\.)+?\\$");

    // Operators / LaTeX commands that prove the content is math, not currency
    private static final Pattern MATH_INDICATORS = Pattern.compile(
            "[\\\\<>=+\\-*/^_{}\\[\\]|≤≥±∈∉∀∃→←↔~]"
    );

    public void run(boolean dryRun, boolean allStatuses, String section, String domain, String onlyId) {
        List<Question> queue;

        if (onlyId != null) {
            queue = questionRepository.findByExternalId(onlyId)
                    .map(List::of)
                    .orElseThrow(() -> new IllegalArgumentException("Not found: " + onlyId));
        } else if (allStatuses) {
            // --all: scan everything, optionally scoped
            if (section != null && domain != null) {
                queue = questionRepository.findBySectionAndDomain(section, domain);
            } else if (section != null) {
                queue = questionRepository.findBySection(section);
            } else if (domain != null) {
                queue = questionRepository.findAll().stream()
                        .filter(q -> domain.equals(q.getDomain())).toList();
            } else {
                queue = questionRepository.findAll();
            }
        } else {
            // Default: only newly generated questions
            String status = QuestionStatus.GENERATED.lower();
            if (section != null && domain != null) {
                queue = questionRepository.findByStatusAndSectionAndDomain(status, section, domain);
            } else if (section != null) {
                queue = questionRepository.findByStatusAndSection(status, section);
            } else if (domain != null) {
                queue = questionRepository.findByStatusAndDomain(status, domain);
            } else {
                queue = questionRepository.findByStatus(status);
            }
        }

        log.info("═".repeat(60));
        log.info(" RenderNormalize  questions={}  dryRun={}  all={}  section={}  domain={}",
                queue.size(), dryRun, allStatuses,
                section != null ? section : "all", domain != null ? domain : "all");
        log.info("═".repeat(60));

        int fixed = 0, clean = 0;
        for (Question q : queue) {
            boolean changed = normalizeQuestion(q, dryRun);
            if (changed) fixed++; else clean++;
        }

        log.info("─".repeat(60));
        log.info(" Results: {} fixed  {} already clean  dryRun={}", fixed, clean, dryRun);
    }

    @Transactional
    boolean normalizeQuestion(Question q, boolean dryRun) {
        List<String> changes = new ArrayList<>();

        // ── Simple string fields ─────────────────────────────────────
        String newStem     = fix(q.getQuestionStem(),     "questionStem",     changes);
        String newShort    = fix(q.getExplanationShort(), "explanationShort", changes);
        String newPassage  = fix(q.getPassageText(),      "passageText",      changes);
        String newTrap     = fix(q.getTrapExplanation(),  "trapExplanation",  changes);
        String newA        = fix(q.getOptionA(),          "optionA",          changes);
        String newB        = fix(q.getOptionB(),          "optionB",          changes);
        String newC        = fix(q.getOptionC(),          "optionC",          changes);
        String newD        = fix(q.getOptionD(),          "optionD",          changes);

        // ── explanationSteps (JSON array) ────────────────────────────
        String newSteps = fixJsonSteps(q.getExplanationSteps(), "explanationSteps", changes);

        // ── alternativeApproach (JSON object with steps array) ───────
        String newAlt = fixAlternativeApproach(q.getAlternativeApproach(), changes);

        if (changes.isEmpty()) return false;

        log.info("[{}] {} rendering fix(es):", q.getExternalId(), changes.size());
        changes.forEach(c -> log.info("   • {}", c));

        if (!dryRun) {
            q.setQuestionStem(newStem);
            q.setExplanationShort(newShort);
            q.setPassageText(newPassage);
            q.setTrapExplanation(newTrap);
            q.setOptionA(newA);
            q.setOptionB(newB);
            q.setOptionC(newC);
            q.setOptionD(newD);
            if (newSteps != null) q.setExplanationSteps(newSteps);
            if (newAlt   != null) q.setAlternativeApproach(newAlt);
            questionRepository.save(q);
        }
        return true;
    }

    // ── Field-level normalizer ───────────────────────────────────────

    /** Fixes a plain string field. Returns the fixed string (or original if no change). */
    private String fix(String value, String fieldName, List<String> changes) {
        if (value == null || value.isBlank()) return value;
        String fixed = normalizeDollarMath(value);
        if (!fixed.equals(value)) {
            changes.add(fieldName + ": math delimiters normalized");
        }
        return fixed;
    }

    /** Replaces $...$ math tokens with \(...\) — leaves currency/prose alone. */
    String normalizeDollarMath(String text) {
        if (text == null) return null;
        Matcher m = DOLLAR_MATH.matcher(text);
        StringBuffer sb = new StringBuffer();
        while (m.find()) {
            String token = m.group();
            String inner = token.substring(1, token.length() - 1);
            if (isMathContent(inner)) {
                // Convert $...$ → \(...\)
                m.appendReplacement(sb, Matcher.quoteReplacement("\\(" + inner + "\\)"));
            } else {
                m.appendReplacement(sb, Matcher.quoteReplacement(token));
            }
        }
        m.appendTail(sb);
        return sb.toString();
    }

    /**
     * Returns true if the inner content of $...$ is math rather than currency/prose.
     * Mirror of the isMathContent() function in practice.js.
     */
    boolean isMathContent(String inner) {
        if (inner == null || inner.isBlank()) return false;
        if (MATH_INDICATORS.matcher(inner).find()) return true; // LaTeX or operators
        if (!inner.contains(" "))                  return true; // compact token: $3x$
        return false;                                            // spaced text, no operators → prose
    }

    // ── JSON field normalizers ───────────────────────────────────────

    private String fixJsonSteps(Object stepsRaw, String fieldName, List<String> changes) {
        if (stepsRaw == null) return null;
        try {
            JsonNode node = stepsRaw instanceof String s
                    ? objectMapper.readTree(s)
                    : objectMapper.valueToTree(stepsRaw);
            if (!node.isArray()) return null;

            boolean changed = false;
            ArrayNode arr = (ArrayNode) node;
            for (int i = 0; i < arr.size(); i++) {
                ObjectNode step = (ObjectNode) arr.get(i);
                changed |= fixTextField(step, "content", fieldName + "[" + i + "].content", changes);
                changed |= fixTextField(step, "math",    fieldName + "[" + i + "].math",    changes);
                changed |= fixTextField(step, "title",   fieldName + "[" + i + "].title",   changes);
            }
            return changed ? objectMapper.writeValueAsString(arr) : null;
        } catch (Exception e) {
            log.warn("Could not parse {}: {}", fieldName, e.getMessage());
            return null;
        }
    }

    private String fixAlternativeApproach(Object raw, List<String> changes) {
        if (raw == null) return null;
        try {
            JsonNode node = raw instanceof String s
                    ? objectMapper.readTree(s)
                    : objectMapper.valueToTree(raw);
            if (!node.isObject()) return null;

            boolean changed = false;
            ObjectNode obj = (ObjectNode) node;
            changed |= fixTextField(obj, "title", "alternativeApproach.title", changes);
            if (obj.has("steps") && obj.get("steps").isArray()) {
                ArrayNode steps = (ArrayNode) obj.get("steps");
                for (int i = 0; i < steps.size(); i++) {
                    ObjectNode step = (ObjectNode) steps.get(i);
                    changed |= fixTextField(step, "content", "altApproach.steps[" + i + "].content", changes);
                    changed |= fixTextField(step, "math",    "altApproach.steps[" + i + "].math",    changes);
                    changed |= fixTextField(step, "title",   "altApproach.steps[" + i + "].title",   changes);
                }
            }
            return changed ? objectMapper.writeValueAsString(obj) : null;
        } catch (Exception e) {
            log.warn("Could not parse alternativeApproach: {}", e.getMessage());
            return null;
        }
    }

    /** Fixes a text field inside an ObjectNode in-place. Returns true if changed. */
    private boolean fixTextField(ObjectNode node, String field, String label, List<String> changes) {
        if (!node.has(field) || node.get(field).isNull()) return false;
        String original = node.get(field).asText();
        String fixed    = normalizeDollarMath(original);
        if (fixed.equals(original)) return false;
        node.put(field, fixed);
        changes.add(label + ": math delimiters normalized");
        return true;
    }
}
