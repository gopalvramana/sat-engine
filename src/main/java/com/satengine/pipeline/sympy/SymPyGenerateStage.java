package com.satengine.pipeline.sympy;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.sympy.SymPyQuestion;
import com.satengine.domain.sympy.SymPyQuestionAnswer;
import com.satengine.domain.sympy.SymPyQuestionAnswerRepository;
import com.satengine.domain.sympy.SymPyQuestionRepository;
import com.satengine.pipeline.claude.ClaudeClient;
import com.satengine.pipeline.claude.NarrationPromptLibrary;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;

/**
 * SymPy pipeline generation stage.
 *
 * Flow per question:
 *  1. Python math_engine.py → MathObject (SymPy-verified math)
 *  2. Duplicate param_hash check → skip if already saved
 *  3. Answer-slot assignment (deterministic Fisher-Yates, Java)
 *  4. Haiku narration → questionStem + explanationShort + explanationSteps
 *  5. Sonnet cross-verify (soft) → flag if disagrees; never blocks save
 *  6. Save to sympy_questions + sympy_question_answers
 *
 * All questions land in sympy_questions — zero changes to the production questions table.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SymPyGenerateStage {

    private static final String HAIKU_MODEL  = "claude-haiku-4-5-20251001";
    private static final String SONNET_MODEL = "claude-sonnet-4-6";
    private static final int    MAX_RETRIES  = 3;

    // Skill → domain mapping (SAT taxonomy)
    private static final Map<String, String> SKILL_DOMAIN = Map.ofEntries(
            Map.entry("linear_eq_one_var",          "algebra"),
            Map.entry("linear_eq_word_problems",    "algebra"),
            Map.entry("systems_linear_eq",          "algebra"),
            Map.entry("linear_functions",           "algebra"),
            Map.entry("linear_eq_two_var",          "algebra"),
            Map.entry("quadratic_equations",        "algebra"),
            Map.entry("percentages",                "problem_solving_data_analysis"),
            Map.entry("ratios_rates",               "problem_solving_data_analysis"),
            Map.entry("proportional_relationships", "problem_solving_data_analysis"),
            Map.entry("pythagorean_theorem",        "geometry_trigonometry"),
            Map.entry("area_2d",                    "geometry_trigonometry"),
            Map.entry("coordinate_geometry",        "geometry_trigonometry"),
            Map.entry("circles",                    "geometry_trigonometry"),
            Map.entry("volume_3d",                  "geometry_trigonometry"),
            Map.entry("plane_geometry",             "geometry_trigonometry"),
            Map.entry("data_analysis",              "problem_solving_data_analysis"),
            Map.entry("statistics",                 "problem_solving_data_analysis"),
            Map.entry("sequences_series",           "advanced_math"),
            Map.entry("exponents_radicals",         "advanced_math"),
            Map.entry("complex_numbers",            "advanced_math"),
            Map.entry("polynomials",                "advanced_math"),
            Map.entry("probability",                "problem_solving_data_analysis"),
            Map.entry("two_way_tables",             "problem_solving_data_analysis"),
            Map.entry("linear_inequalities",        "algebra"),
            Map.entry("absolute_value",             "algebra"),
            Map.entry("special_triangles",          "geometry_trigonometry"),
            Map.entry("trigonometry",               "geometry_trigonometry"),
            Map.entry("quadratic_functions",        "advanced_math"),
            Map.entry("scatterplot_analysis",       "problem_solving_data_analysis"),
            Map.entry("equivalent_expressions",     "advanced_math"),
            Map.entry("nonlinear_equations",         "advanced_math")
    );

    // Skill → human-readable name
    private static final Map<String, String> SKILL_NAME = Map.ofEntries(
            Map.entry("linear_eq_one_var",          "Linear equations in one variable"),
            Map.entry("linear_eq_word_problems",    "Linear equation word problems"),
            Map.entry("systems_linear_eq",          "Systems of linear equations"),
            Map.entry("linear_functions",           "Linear functions"),
            Map.entry("linear_eq_two_var",          "Linear equations in two variables"),
            Map.entry("quadratic_equations",        "Quadratic equations"),
            Map.entry("percentages",                "Percentages"),
            Map.entry("ratios_rates",               "Ratios and rates"),
            Map.entry("proportional_relationships", "Proportional relationships"),
            Map.entry("pythagorean_theorem",        "Pythagorean theorem"),
            Map.entry("area_2d",                    "Area and volume"),
            Map.entry("coordinate_geometry",        "Coordinate geometry"),
            Map.entry("circles",                    "Circles"),
            Map.entry("volume_3d",                  "Volume — 3D shapes"),
            Map.entry("plane_geometry",             "Plane geometry"),
            Map.entry("data_analysis",              "Data analysis"),
            Map.entry("statistics",                 "Statistics (mean, median, IQR, std dev)"),
            Map.entry("sequences_series",           "Sequences and series"),
            Map.entry("exponents_radicals",         "Exponents and radicals"),
            Map.entry("complex_numbers",            "Complex numbers"),
            Map.entry("polynomials",                "Polynomial operations"),
            Map.entry("probability",                "Probability"),
            Map.entry("two_way_tables",             "Two-way tables"),
            Map.entry("linear_inequalities",        "Linear inequalities"),
            Map.entry("absolute_value",             "Absolute value equations and inequalities"),
            Map.entry("special_triangles",          "Special triangles (30-60-90, 45-45-90)"),
            Map.entry("trigonometry",               "Trigonometry (sin, cos, tan)"),
            Map.entry("quadratic_functions",        "Quadratic functions"),
            Map.entry("scatterplot_analysis",       "Scatterplots and line of best fit"),
            Map.entry("equivalent_expressions",     "Equivalent expressions"),
            Map.entry("nonlinear_equations",         "Nonlinear equations in one variable")
    );

    // Skill code suffix for external IDs
    private static final Map<String, String> SKILL_CODE = Map.ofEntries(
            Map.entry("linear_eq_one_var",          "LEQ"),
            Map.entry("linear_eq_word_problems",    "LWP"),
            Map.entry("systems_linear_eq",          "SLE"),
            Map.entry("linear_functions",           "LFN"),
            Map.entry("linear_eq_two_var",          "L2V"),
            Map.entry("quadratic_equations",        "QEQ"),
            Map.entry("percentages",                "PCT"),
            Map.entry("ratios_rates",               "RAT"),
            Map.entry("proportional_relationships", "PRP"),
            Map.entry("pythagorean_theorem",        "PYT"),
            Map.entry("area_2d",                    "ARA"),
            Map.entry("coordinate_geometry",        "CGE"),
            Map.entry("circles",                    "CIR"),
            Map.entry("volume_3d",                  "VOL"),
            Map.entry("plane_geometry",             "PLG"),
            Map.entry("data_analysis",              "DAT"),
            Map.entry("statistics",                 "STA"),
            Map.entry("sequences_series",           "SEQ"),
            Map.entry("exponents_radicals",         "EXR"),
            Map.entry("complex_numbers",            "CMX"),
            Map.entry("polynomials",                "POL"),
            Map.entry("probability",                "PRB"),
            Map.entry("two_way_tables",             "TWT"),
            Map.entry("linear_inequalities",        "LIN"),
            Map.entry("absolute_value",             "ABV"),
            Map.entry("special_triangles",          "SPT"),
            Map.entry("trigonometry",               "TRG"),
            Map.entry("quadratic_functions",        "QFN"),
            Map.entry("scatterplot_analysis",       "SCA"),
            Map.entry("equivalent_expressions",     "EXP"),
            Map.entry("nonlinear_equations",         "NLE")
    );

    private final MathObjectService          mathObjectService;
    private final ClaudeClient               claudeClient;
    private final SymPyQuestionRepository    sympyRepo;
    private final SymPyQuestionAnswerRepository answerRepo;
    private final ObjectMapper               objectMapper;
    private final com.satengine.pipeline.claude.ExampleLoader exampleLoader;
    private final NarrationFormatValidator   formatValidator;

    /**
     * Generate {@code count} questions for the given skill and difficulty.
     *
     * @param skill      skill key (null = round-robin all skills)
     * @param difficulty 1–3 (SAT taxonomy: 1=Easy, 2=Medium, 3=Hard; clamped to 3 in Python)
     * @param count      number of questions to attempt
     * @param pool       pool tag: "diagnostic" | "drill" | "test" | "reference" (null defaults to "drill")
     */
    public void run(String skill, int difficulty, int count, String pool) {
        run(skill, difficulty, count, pool, null);
    }

    /**
     * Generate with an optional template pin (for targeted testing of specific template types).
     *
     * @param forceTemplate if non-null, pins generation to a specific template within the skill
     */
    public void run(String skill, int difficulty, int count, String pool, String forceTemplate) {
        run(skill, difficulty, count, pool, forceTemplate, null);
    }

    /**
     * Full generate: skill + difficulty + optional template + optional variant.
     *
     * Code paths:
     *   A) forceTemplate + forceVariant  → generate exactly 1 question of that variant
     *   B) forceTemplate only            → iterate all variants of that template (1 per variant)
     *   C) neither                       → generate `count` questions, rotating templates each time
     *
     * In paths A and B, `count` is ignored — the number of questions is determined by
     * the variant list (or 1 for a single variant).
     *
     * @param forceTemplate if non-null, pins generation to a specific template
     * @param forceVariant  if non-null, generates exactly 1 question of that variant
     */
    public void run(String skill, int difficulty, int count, String pool,
                    String forceTemplate, String forceVariant) {
        final String resolvedPool = (pool != null && !pool.isBlank()) ? pool : "drill";
        log.info("SymPy generate: skill={} difficulty={} count={} template={} variant={}",
                 skill, difficulty, count, forceTemplate, forceVariant);

        Set<String> excludeParams    = new HashSet<>();
        Set<String> excludeScenarios = new HashSet<>();

        // Pre-load existing param hashes
        if (skill == null) {
            for (String s : SKILL_CODE.keySet()) {
                excludeParams.addAll(sympyRepo.findParamHashesBySkillKey(s));
            }
        } else {
            excludeParams.addAll(sympyRepo.findParamHashesBySkillKey(skill));
            sympyRepo.findRecentScenarioTagsForSkill(skill, 20).forEach(excludeScenarios::add);
        }

        // ── Path A: single variant ────────────────────────────────────────────
        if (forceTemplate != null && !forceTemplate.isBlank()
                && forceVariant != null && !forceVariant.isBlank()) {
            log.info("Path A: single variant — template={} variant={}", forceTemplate, forceVariant);
            generateOne(skill, difficulty, resolvedPool, forceTemplate, forceVariant,
                        excludeParams, excludeScenarios);
            return;
        }

        // ── Path B: all variants of a template ───────────────────────────────
        if (forceTemplate != null && !forceTemplate.isBlank()) {
            List<String> variants = resolveVariants(skill, difficulty, forceTemplate);
            log.info("Path B: all variants — template={} variants={}", forceTemplate, variants);
            for (String v : variants) {
                generateOne(skill, difficulty, resolvedPool, forceTemplate, v,
                            excludeParams, excludeScenarios);
            }
            return;
        }

        // ── Path C: classic batch (count questions, rotating templates) ───────
        log.info("Path C: classic batch — count={}", count);
        int saved = 0, attempts = 0;
        List<String> skillRotation = (skill == null)
                ? new java.util.ArrayList<>(SKILL_CODE.keySet()) : null;

        while (saved < count && attempts < count * MAX_RETRIES) {
            attempts++;
            String currentSkill = (skillRotation != null)
                    ? skillRotation.get(saved % skillRotation.size()) : skill;
            boolean ok = generateOne(currentSkill, difficulty, resolvedPool,
                                     null, null, excludeParams, excludeScenarios);
            if (ok) saved++;
        }
        log.info("SymPy generate complete: {}/{} questions saved", saved, count);
        if (saved < count)
            log.warn("{} questions could not be generated after {} attempts",
                     count - saved, attempts);
    }

    /**
     * Generates and saves a single question.  Returns true on success, false on
     * duplicate/error (caller decides whether to retry).
     */
    private boolean generateOne(String skill, int difficulty, String pool,
                                 String forceTemplate, String forceVariant,
                                 Set<String> excludeParams, Set<String> excludeScenarios) {
        try {
            List<MathObject> batch = mathObjectService.generate(
                    skill, difficulty, 1, excludeParams, excludeScenarios,
                    forceTemplate, forceVariant, Set.of());

            if (batch.isEmpty()) {
                log.warn("math_engine returned empty batch for template={} variant={}",
                         forceTemplate, forceVariant);
                return false;
            }

            MathObject mo = batch.get(0);
            mathObjectService.validate(mo);

            if (mathObjectService.isDuplicateParameters(mo.skill(), mo.paramHash())) {
                log.debug("Duplicate params skill={} hash={}", mo.skill(), mo.paramHash());
                excludeParams.add(mo.paramHash());
                return false;
            }

            String[] slots = new String[4];
            String correctLetter;
            if ("mcq".equals(mo.questionType())) {
                String extIdPreview = nextExternalId(mo.skill());
                correctLetter = mathObjectService.assignAnswerSlot(mo, extIdPreview, slots);
            } else {
                correctLetter = null;
                Arrays.fill(slots, null);
            }

            String narrationJson = narrate(mo, slots, correctLetter);
            JsonNode narration   = objectMapper.readTree(narrationJson);

            if (mo.exactStem() != null && !mo.exactStem().isBlank()) {
                ((com.fasterxml.jackson.databind.node.ObjectNode) narration)
                        .put("questionStem", mo.exactStem());
                log.debug("exactStem applied for {} — Haiku stem discarded", mo.skill());
            }

            List<String> formatFlags = formatValidator.validate(narration);
            if (!formatFlags.isEmpty()) {
                // Attempt auto-repair before flagging for human review
                boolean hasLatexViolation = formatFlags.stream()
                        .anyMatch(f -> f.startsWith("latex_wrapper_missing"));
                if (hasLatexViolation) {
                    formatValidator.autoFix((com.fasterxml.jackson.databind.node.ObjectNode) narration);
                    formatFlags = formatValidator.validate(narration); // re-check after fix
                }
                if (!formatFlags.isEmpty()) {
                    log.warn("Format validator FLAGGED (after autoFix): skill={} tpl={} violations={}",
                             mo.skill(),
                             mo.params() != null ? mo.params().getOrDefault("tpl", "?") : "?",
                             formatFlags);
                } else {
                    log.info("Format validator autoFixed latex wrappers: skill={} tpl={}",
                             mo.skill(),
                             mo.params() != null ? mo.params().getOrDefault("tpl", "?") : "?");
                }
            }

            String reviewNotes = null;
            for (int cvTry = 0; cvTry < 2; cvTry++) {
                try {
                    reviewNotes = crossVerify(mo, narration, slots, correctLetter);
                    break;
                } catch (Exception e) {
                    if (cvTry == 0 && e.getMessage() != null && e.getMessage().contains("529")) {
                        log.warn("Cross-verify overloaded (529), retrying in 8s...");
                        try { Thread.sleep(8_000); } catch (InterruptedException ie) {
                            Thread.currentThread().interrupt();
                        }
                    } else {
                        reviewNotes = "cross_verify_failed: " + e.getMessage();
                        log.warn("Cross-verify failed, flagging: {}", e.getMessage());
                        break;
                    }
                }
            }

            if (!formatFlags.isEmpty()) {
                String formatNote = "format_violations: " + String.join(",", formatFlags);
                reviewNotes = (reviewNotes == null) ? formatNote : reviewNotes + " | " + formatNote;
            }

            saveQuestion(mo, narration, slots, correctLetter, reviewNotes, pool);

            excludeParams.add(mo.paramHash());
            if (mo.scenarioTag() != null) excludeScenarios.add(mo.scenarioTag());

            log.info("saved {} d{} tpl={} variant={} {}",
                     mo.skill(), mo.difficulty(),
                     mo.params() != null ? mo.params().getOrDefault("tpl", "?") : "?",
                     forceVariant != null ? forceVariant : "-",
                     reviewNotes != null ? "(flagged)" : "");
            return true;

        } catch (MathTemplateException e) {
            log.error("MathTemplateException template={} variant={}: {}",
                      forceTemplate, forceVariant, e.getMessage());
            return false;
        } catch (Exception e) {
            log.error("Unexpected error template={} variant={}: {}",
                      forceTemplate, forceVariant, e.getMessage(), e);
            return false;
        }
    }

    /**
     * Fetch variant list for a template from Python, falling back to empty list on error.
     * Used by Path B to iterate variants without hardcoding them in Java.
     */
    private List<String> resolveVariants(String skill, int difficulty, String template) {
        try {
            String json = mathObjectService.listVariants(skill, difficulty, template);
            com.fasterxml.jackson.databind.JsonNode node = objectMapper.readTree(json);
            // Response format: {"variants": ["v1","v2",...]}
            com.fasterxml.jackson.databind.JsonNode arr = node.path("variants");
            if (arr.isArray()) {
                List<String> variants = new java.util.ArrayList<>();
                arr.forEach(v -> variants.add(v.asText()));
                return variants;
            }
            // Fallback: single-question, no variant filter
            log.warn("Unexpected variants response for {}/{}: {}", skill, template, json);
            return List.of((String) null);
        } catch (Exception e) {
            log.warn("Could not fetch variants for {}/{}: {}", skill, template, e.getMessage());
            return List.of((String) null);
        }
    }

    // ── Narration (Haiku) ─────────────────────────────────────────────────────

    private String narrate(MathObject mo, String[] slots, String correctLetter) {
        String examplesBlock = exampleLoader.buildExamplesBlock(mo.skill(), mo.difficulty());

        String userMsg = "mcq".equals(mo.questionType())
                ? NarrationPromptLibrary.buildNarrationPrompt(
                        mo, slots[0], slots[1], slots[2], slots[3], correctLetter, objectMapper,
                        examplesBlock)
                : NarrationPromptLibrary.buildSprNarrationPrompt(mo, objectMapper, examplesBlock);

        // Fix 1: 2048 tokens — 1024 was truncating multi-field JSON responses
        String raw = claudeClient.call(
                HAIKU_MODEL, 2048,
                NarrationPromptLibrary.NARRATION_SYSTEM,
                userMsg);

        raw = extractJsonObject(raw);
        // Fix 2: repair unescaped LaTeX backslashes before Jackson parse
        raw = fixJsonEscapes(raw);
        return raw;
    }

    // ── Cross-verify (Sonnet) ─────────────────────────────────────────────────

    /**
     * Deep cross-verify with Sonnet: checks math correctness + 3 quality gates.
     *
     * Flags (sets reviewNotes) when ANY of:
     *   agrees              = false  → math is wrong
     *   stem_matches_intent = false  → stem asks for wrong quantity
     *   is_ambiguous        = true   → multiple valid interpretations possible
     *   answer_leaked       = true   → correct answer visible in stem/choices
     *
     * Returns a non-null review note string if any flag fires; null if all pass.
     */
    private String crossVerify(MathObject mo, JsonNode narration,
                                String[] slots, String correctLetter) {
        String questionStem = narration.path("questionStem").asText("");
        if (questionStem.isBlank()) return null;

        String prompt = NarrationPromptLibrary.buildCrossVerifyPrompt(
                questionStem, mo.verifiedAnswer(),
                slots[0], slots[1], slots[2], slots[3], correctLetter,
                mo.questionContext());

        String raw = claudeClient.call(
                SONNET_MODEL, 512,
                NarrationPromptLibrary.CROSS_VERIFY_SYSTEM,
                prompt);

        raw = extractJsonObject(raw);

        JsonNode resp;
        try {
            resp = objectMapper.readTree(raw);
        } catch (Exception e) {
            log.warn("Could not parse cross-verify response: {}", raw);
            return null;
        }

        boolean agrees           = resp.path("agrees").asBoolean(true);
        boolean stemMatchIntent  = resp.path("stem_matches_intent").asBoolean(true);
        boolean isAmbiguous      = resp.path("is_ambiguous").asBoolean(false);
        boolean answerLeaked     = resp.path("answer_leaked").asBoolean(false);
        String  reasoning        = resp.path("reasoning").asText("");

        List<String> flags = new java.util.ArrayList<>();
        if (!agrees)          flags.add("math_wrong");
        if (!stemMatchIntent) flags.add("stem_intent_mismatch");
        if (isAmbiguous)      flags.add("ambiguous");
        if (answerLeaked)     flags.add("answer_leaked");

        if (!flags.isEmpty()) {
            log.warn("Cross-verify FLAGGED {}: skill={} tpl={} flags={} reason={}",
                     flags, mo.skill(),
                     mo.params() != null ? mo.params().getOrDefault("tpl", "?") : "?",
                     flags, reasoning);
            return String.join("|", flags) + ": " + reasoning;
        }
        return null;
    }

    /**
     * Extracts a JSON object from a raw LLM response.
     * Handles: leading/trailing whitespace, markdown code fences anywhere in the
     * response, and reasoning text before the JSON block.
     */
    private static String extractJsonObject(String raw) {
        raw = raw.strip();
        // Look for a ```json ... ``` block anywhere in the response
        int fenceIdx = raw.indexOf("```");
        if (fenceIdx >= 0) {
            int nlIdx = raw.indexOf('\n', fenceIdx);
            if (nlIdx >= 0) {
                int endFence = raw.indexOf("```", nlIdx + 1);
                if (endFence > nlIdx) {
                    return raw.substring(nlIdx + 1, endFence).strip();
                }
            }
        }
        // Fall back: find the outermost { ... } object
        int braceStart = raw.indexOf('{');
        int braceEnd   = raw.lastIndexOf('}');
        if (braceStart >= 0 && braceEnd > braceStart) {
            return raw.substring(braceStart, braceEnd + 1).strip();
        }
        return raw;
    }

    /**
     * Repairs unescaped LaTeX backslashes in JSON emitted by Haiku.
     * JSON only allows \", \\, \/, \b, \f, \n, \r, \t, \XXXX.
     * Any other \x (e.g. \cdot, \frac) is invalid — double the backslash so
     * Jackson sees \\cdot and preserves it as \cdot in the parsed string.
     */
    private static String fixJsonEscapes(String raw) {
        StringBuilder sb = new StringBuilder(raw.length() + 32);
        int len = raw.length();
        for (int i = 0; i < len; i++) {
            char ch = raw.charAt(i);
            if (ch != '\\') { sb.append(ch); continue; }
            if (i + 1 >= len) { sb.append("\\\\"); continue; }
            char next = raw.charAt(i + 1);
            switch (next) {
                case '"': case '\\': case '/':
                    sb.append(ch); sb.append(next); i++; break;
                case 'b': case 'n': case 'r': case 't': case 'f':
                    // Valid JSON whitespace escapes — BUT if the next char is a letter,
                    // the AI wrote a LaTeX command (\bar, \neq, \right, \text, \frac, …)
                    // not a whitespace char. Double the backslash so Jackson preserves
                    // the command literally.
                    if (i + 2 < len && Character.isLetter(raw.charAt(i + 2))) {
                        sb.append("\\\\"); // LaTeX command → double-escape, do NOT skip next char
                    } else {
                        sb.append(ch); sb.append(next); i++; // genuine JSON whitespace escape
                    }
                    break;
                case 'u':
                    if (i + 5 < len && raw.substring(i + 2, i + 6).matches("[0-9a-fA-F]{4}")) {
                        sb.append(ch); // valid \\uXXXX — keep, do not skip (loop will handle next chars)
                    } else {
                        sb.append("\\\\"); // invalid \\u — double the backslash
                    }
                    break;
                default:
                    // Invalid escape (e.g. \c in \cdot) — double it
                    sb.append("\\\\"); break;
            }
        }
        return sb.toString();
    }

    // ── Persist ───────────────────────────────────────────────────────────────

    @Transactional
    protected void saveQuestion(MathObject mo, JsonNode narration,
                                 String[] slots, String correctLetter,
                                 String reviewNotes, String pool) {
        String externalId = allocateExternalId(mo.skill());
        String status = reviewNotes != null ? "generated_flagged" : "generated";

        String mathObjectJson;
        try {
            mathObjectJson = objectMapper.writeValueAsString(mo);
        } catch (Exception e) {
            mathObjectJson = "{}";
        }

        String diagJson = null;
        if (mo.diagramSpec() != null) {
            try {
                diagJson = objectMapper.writeValueAsString(mo.diagramSpec());
            } catch (Exception e) {
                log.warn("Could not serialize diagramSpec: {}", e.getMessage());
            }
        }

        String stepsJson = null;
        JsonNode steps = narration.path("explanationSteps");
        if (!steps.isMissingNode() && !steps.isNull()) {
            try {
                stepsJson = objectMapper.writeValueAsString(steps);
            } catch (Exception ignored) {}
        }

        String coreConcept = narration.path("coreConcept").asText(null);

        String distractorRationaleJson = null;
        JsonNode dr = narration.path("distractorRationale");
        if (!dr.isMissingNode() && !dr.isNull() && dr.isObject()) {
            try { distractorRationaleJson = objectMapper.writeValueAsString(dr); } catch (Exception ignored) {}
        }

        String prerequisitesJson = null;
        JsonNode prereqNode = narration.path("prerequisites");
        if (!prereqNode.isMissingNode() && !prereqNode.isNull() && prereqNode.isArray()) {
            try { prerequisitesJson = objectMapper.writeValueAsString(prereqNode); } catch (Exception ignored) {}
        }

        String alternativeApproach = narration.path("alternativeApproach").asText(null);

        SymPyQuestion q = SymPyQuestion.builder()
                .externalId(externalId)
                .section("math")
                .domain(SKILL_DOMAIN.getOrDefault(mo.skill(), "algebra"))
                .skill(SKILL_NAME.getOrDefault(mo.skill(), mo.skill()))
                .skillKey(mo.skill())
                .scenarioTag(mo.scenarioTag())
                .difficulty((short) mo.difficulty())
                .questionType(mo.questionType())
                .questionStem(narration.path("questionStem").asText(""))
                .optionA("mcq".equals(mo.questionType()) ? slots[0] : null)
                .optionB("mcq".equals(mo.questionType()) ? slots[1] : null)
                .optionC("mcq".equals(mo.questionType()) ? slots[2] : null)
                .optionD("mcq".equals(mo.questionType()) ? slots[3] : null)
                .sprMin(mo.sprMin())
                .sprMax(mo.sprMax())
                .explanationShort(narration.path("explanationShort").asText(null))
                .explanationSteps(stepsJson)
                .coreConcept(coreConcept)
                .distractorRationale(distractorRationaleJson)
                .prerequisites(prerequisitesJson)
                .alternativeApproach(alternativeApproach)
                .diagram(diagJson)
                .mathObject(mathObjectJson)
                .paramHash(mo.paramHash())
                .reviewNotes(reviewNotes)
                .pool(pool)
                .status(status)
                .generatedAt(OffsetDateTime.now())
                .build();

        sympyRepo.save(q);

        // Save answer
        String answer = "mcq".equals(mo.questionType()) ? correctLetter : mo.verifiedAnswer();
        if (answer != null && !answer.isBlank()) {
            SymPyQuestionAnswer qa = SymPyQuestionAnswer.builder()
                    .question(q)
                    .correctAnswer(answer)
                    .build();
            answerRepo.save(qa);
        }
    }

    // ── External ID allocation ────────────────────────────────────────────────

    /**
     * Returns a preview externalId used as seed for answer-slot shuffle.
     * Does not touch the DB — actual allocation happens in saveQuestion().
     */
    private String nextExternalId(String skill) {
        String code   = SKILL_CODE.getOrDefault(skill, "UNK");
        String prefix = "SP-" + code + "-";
        int    next   = sympyRepo.findMaxSeqForPrefix(prefix + "%", prefix.length() + 1) + 1;
        return prefix + String.format("%03d", next);
    }

    /**
     * Allocates the next external ID atomically within a transaction.
     */
    private String allocateExternalId(String skill) {
        return nextExternalId(skill);
    }
}
