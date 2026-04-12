package com.satengine.pipeline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.pipeline.claude.ClaudeClient;
import com.satengine.pipeline.claude.PromptLibrary;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Slf4j
@Service
@RequiredArgsConstructor
public class GenerateStage {

    private final QuestionRepository questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final ClaudeClient claudeClient;
    private final ObjectMapper objectMapper;

    private static final String GENERATE_MODEL = "claude-haiku-4-5-20251001";
    private static final int    MAX_TOKENS      = 4000;
    private static final double TEMPERATURE     = 0.8;
    private static final int    MAX_RETRIES     = 2;

    private static final Map<String, String> SECTION_CODES = Map.of(
            "math", "MATH", "reading_writing", "RW"
    );
    private static final Map<String, String> DOMAIN_CODES = Map.of(
            "algebra", "ALG", "advanced_math", "ADV",
            "problem_solving_data", "PS", "geometry_trigonometry", "GEO",
            "information_ideas", "INF", "craft_structure", "CRF",
            "expression_ideas", "EXP", "standard_english", "ENG"
    );
    private static final Map<String, Integer> MATH_DOMAIN_WEIGHTS = Map.of(
            "algebra", 35, "advanced_math", 35, "problem_solving_data", 15, "geometry_trigonometry", 15
    );
    private static final Map<String, Integer> RW_DOMAIN_WEIGHTS = Map.of(
            "information_ideas", 26, "craft_structure", 28, "expression_ideas", 20, "standard_english", 26
    );
    private static final int[] DIFFICULTY_WEIGHTS = {0, 5, 15, 20, 25, 20, 10, 5}; // index = difficulty 1-7
    private static final Map<String, Double> DIAGRAM_PROBS = Map.of(
            "geometry_trigonometry", 1.00,  // every geometry question needs a figure
            "problem_solving_data",  0.70,  // most data questions need a chart/graph
            "algebra",               0.25,  // coordinate planes, function graphs
            "advanced_math",         0.20   // function graphs, occasionally
    );
    /** Jaccard word-overlap threshold above which a generated stem is considered a duplicate. */
    private static final double DUPLICATE_THRESHOLD = 0.85;

    private static final List<String> ARTIFACT_PHRASES = List.of(
            "wait,", "wait —", "wait—", "let's recheck", "let me recheck",
            "let me recalculate", "let me re-read", "let me re-examine",
            "let me verify", "let me rewrite", "let me use", "let me try",
            "let me reconsider", "let me recompute", "let me re-examine",
            "hmm,", "hmm.", "actually,", "actually—", "actually ",
            "rechecking", "re-checking", "doesn't yield", "doesn't work",
            "i need to reconsider", "more likely", "intended answer",
            "clean answer", "let me rethink"
    );

    private final Random random = new Random();

    /** domain key → ordered list of skill keys, loaded from sat_taxonomy.json at startup */
    private final Map<String, List<String>> taxonomySkills = new HashMap<>();

    @PostConstruct
    void loadTaxonomy() {
        try {
            JsonNode root = objectMapper.readTree(
                    new ClassPathResource("taxonomy/sat_taxonomy.json").getInputStream());
            for (JsonNode section : root.path("sections")) {
                for (JsonNode domain : section.path("domains")) {
                    String domainKey = domain.path("key").asText();
                    List<String> skills = new ArrayList<>();
                    for (JsonNode skill : domain.path("skills")) {
                        skills.add(skill.path("key").asText());
                    }
                    taxonomySkills.put(domainKey, skills);
                }
            }
            int total = taxonomySkills.values().stream().mapToInt(List::size).sum();
            log.info("Taxonomy loaded: {} domains, {} total skills", taxonomySkills.size(), total);
        } catch (Exception e) {
            log.error("Failed to load sat_taxonomy.json — skill balancing disabled: {}", e.getMessage());
        }
    }

    /**
     * Picks the skill key with the fewest existing questions for this domain.
     * If all skills are equally covered (or taxonomy not loaded), picks randomly.
     * Falls back to null (let Claude decide) if domain has no skills in taxonomy.
     */
    private String pickLeastCoveredSkill(String domain) {
        List<String> allSkills = taxonomySkills.get(domain);
        if (allSkills == null || allSkills.isEmpty()) return null;

        // Build a count map from DB (skill_key → count)
        Map<String, Long> counts = new HashMap<>();
        try {
            questionRepository.countBySkillKeyForDomain(domain)
                    .forEach(row -> counts.put(
                            row[0] != null ? row[0].toString() : "",
                            row[1] != null ? ((Number) row[1]).longValue() : 0L));
        } catch (Exception e) {
            log.warn("Could not query skill counts for domain={}: {}", domain, e.getMessage());
        }

        // Find the minimum count across all skills (skills not in DB yet default to 0)
        long minCount = allSkills.stream()
                .mapToLong(s -> counts.getOrDefault(s, 0L))
                .min().orElse(0L);

        // Collect all skills tied at the minimum count, then pick randomly among them
        List<String> candidates = allSkills.stream()
                .filter(s -> counts.getOrDefault(s, 0L) == minCount)
                .collect(Collectors.toList());

        String chosen = candidates.get(random.nextInt(candidates.size()));
        log.debug("Skill balance domain={}: picked '{}' (count={}, {} candidates at min)",
                domain, chosen, minCount, candidates.size());
        return chosen;
    }

    // ─── Public entry point ────────────────────────────────────────────────

    /**
     * @param sectionArg   "math" | "reading_writing" | null (random)
     * @param domainArg    taxonomy domain key, e.g. "algebra" | null (weighted random)
     * @param skillKeyArg  canonical slug from sat_taxonomy.json, e.g. "linear_functions" | null
     * @param difficultyArg 1-7 | null (weighted random)
     */
    public void run(int count, String sectionArg, String domainArg, String skillKeyArg, Integer difficultyArg) {
        // Validate domain early — fail fast rather than generate garbage IDs
        if (domainArg != null && !domainArg.isBlank() && !DOMAIN_CODES.containsKey(domainArg)) {
            log.error("Unknown --domain value: '{}'. Valid domains: {}", domainArg, DOMAIN_CODES.keySet());
            throw new IllegalArgumentException("Unknown domain: '" + domainArg + "'. Valid: " + DOMAIN_CODES.keySet());
        }
        if (sectionArg != null && !sectionArg.isBlank() && !SECTION_CODES.containsKey(sectionArg)) {
            log.error("Unknown --section value: '{}'. Valid sections: {}", sectionArg, SECTION_CODES.keySet());
            throw new IllegalArgumentException("Unknown section: '" + sectionArg + "'. Valid: " + SECTION_CODES.keySet());
        }

        log.info("═".repeat(60));
        log.info(" Generate Stage  count={} section={} domain={} skill={} difficulty={}",
                count, sectionArg, domainArg, skillKeyArg, difficultyArg);
        log.info("═".repeat(60));

        int success = 0, failed = 0;
        // Cache next seq per domain within this run
        Map<String, Integer> seqCache = new java.util.HashMap<>();

        for (int i = 1; i <= count; i++) {
            // If domain is explicitly specified, infer section from it — never random-pick
            String  section    = (domainArg != null && !domainArg.isBlank())
                                     ? sectionForDomain(domainArg)
                                     : pickSection(sectionArg);
            // Use the explicitly requested domain, or fall back to weighted random
            String  domain     = (domainArg != null && !domainArg.isBlank()) ? domainArg : pickDomain(section);
            int     difficulty = difficultyArg != null ? difficultyArg : pickDifficulty();
            String  qtype      = pickQuestionType(section);
            boolean hasDiagram   = pickHasDiagram(section, domain);
            String  diagramType  = hasDiagram ? pickDiagramType(domain) : null;

            String sectionCode = SECTION_CODES.get(section);
            String domainCode  = DOMAIN_CODES.get(domain);
            String prefix      = sectionCode + "-" + domainCode + "-";

            int seq = seqCache.computeIfAbsent(domain, d -> {
                int maxSeq = questionRepository.findMaxSeqForPrefix(prefix, prefix + "%");
                return maxSeq + 1;
            });

            String externalId = prefix + String.format("%03d", seq);

            // Skip if already exists
            if (questionRepository.findByExternalId(externalId).isPresent()) {
                log.info("[{}/{}] {} already exists — skipping", i, count, externalId);
                seqCache.put(domain, seq + 1);
                success++;
                continue;
            }

            // If no skill specified, auto-pick the least-covered skill for even distribution
            String resolvedSkill = (skillKeyArg != null && !skillKeyArg.isBlank())
                    ? skillKeyArg
                    : pickLeastCoveredSkill(domain);

            // Build diversity context from existing questions in same domain+skill
            String diversityContext = buildDiversityContext(domain, resolvedSkill);

            JsonNode generated = generateWithRetry(section, domain, resolvedSkill, difficulty, qtype, hasDiagram, diagramType, diversityContext, i, count, externalId);
            if (generated == null) {
                failed++;
                continue;
            }

            saveQuestion(generated, externalId, section, domain, resolvedSkill, difficulty, qtype);
            seqCache.put(domain, seq + 1);
            success++;

            if (i < count) {
                try { Thread.sleep(200); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); }
            }
        }

        log.info("─".repeat(60));
        log.info(" Results: {} saved  {} failed", success, failed);
    }

    // ─── Core generation logic ─────────────────────────────────────────────

    private String buildDiversityContext(String domain, String skillKey) {
        try {
            // Fetch ALL non-rejected questions in the domain (no skill filter, no limit)
            // so Claude sees every existing stem and can't accidentally duplicate any of them.
            List<Object[]> rows = questionRepository.findAllForDiversityContext(domain);
            return PromptLibrary.buildDiversityContext(rows, domain, skillKey);
        } catch (Exception e) {
            log.warn("Could not build diversity context for domain={} skill={}: {}", domain, skillKey, e.getMessage());
            return "";
        }
    }

    private static final String[] MCQ_LETTERS = {"A", "B", "C", "D"};

    private JsonNode generateWithRetry(String section, String domain, String skill,
                                        int difficulty, String qtype,
                                        boolean hasDiagram, String diagramType,
                                        String diversityContext,
                                        int i, int total, String externalId) {
        // For MCQ questions, pick a random target letter to prevent A/B bias
        String targetLetter = "mcq".equalsIgnoreCase(qtype)
                ? MCQ_LETTERS[new Random().nextInt(MCQ_LETTERS.length)]
                : null;

        for (int attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
            try {
                String userPrompt = PromptLibrary.buildGenerateUserPrompt(
                        section, domain, skill, difficulty, qtype, hasDiagram, diagramType,
                        diversityContext, targetLetter);
                String raw = claudeClient.call(GENERATE_MODEL, MAX_TOKENS, PromptLibrary.getGenerateSystem(section), userPrompt, TEMPERATURE);
                String fixed = fixLatexEscapes(extractJson(raw));
                JsonNode data = objectMapper.readTree(fixed);

                if (hasArtifacts(data)) {
                    if (attempt <= MAX_RETRIES) {
                        log.warn("[{}/{}] {} AI artifacts detected (attempt {}) — retrying...", i, total, externalId, attempt);
                        continue;
                    }
                    log.warn("[{}/{}] {} Artifacts persist after {} retries — accepting anyway", i, total, externalId, MAX_RETRIES);
                }

                String diagramFormatError = hasDiagram ? validateDiagramFormat(data) : null;
                if (diagramFormatError != null) {
                    if (attempt <= MAX_RETRIES) {
                        log.warn("[{}/{}] {} Bad diagram format: {} (attempt {}) — retrying...", i, total, externalId, diagramFormatError, attempt);
                        continue;
                    }
                    log.warn("[{}/{}] {} Diagram format invalid after retries — nulling diagram to prevent render errors", i, total, externalId);
                    // Strip the bad diagram rather than save garbage
                    if (data instanceof com.fasterxml.jackson.databind.node.ObjectNode on) {
                        on.putNull("diagram");
                    }
                }

                // MCQ uniqueness check — free structural validation, no extra API call
                if ("mcq".equalsIgnoreCase(qtype)) {
                    String uniquenessError = validateMcqUniqueness(data);
                    if (uniquenessError != null) {
                        if (attempt <= MAX_RETRIES) {
                            log.warn("[{}/{}] {} MCQ uniqueness failed: {} (attempt {}) — retrying...", i, total, externalId, uniquenessError, attempt);
                            continue;
                        }
                        log.warn("[{}/{}] {} MCQ uniqueness failed after {} retries — skipping", i, total, externalId, MAX_RETRIES);
                        return null;
                    }
                }

                // Hard duplicate check — reject and retry if stem is too similar to an existing one
                String generatedStem = data.path("questionStem").asText("");
                if (!generatedStem.isBlank() && isDuplicateStem(generatedStem, domain)) {
                    if (attempt <= MAX_RETRIES) {
                        log.warn("[{}/{}] {} Duplicate stem detected (attempt {}) — retrying...", i, total, externalId, attempt);
                        continue;
                    }
                    log.warn("[{}/{}] {} Duplicate persists after {} retries — skipping", i, total, externalId, MAX_RETRIES);
                    return null;
                }

                String diagramStr = hasDiagram ? (diagramType != null ? diagramType : "diagram") : "no diagram";
                log.info("[{}/{}] {} {} diff:{} {} {}", i, total, externalId, domain, difficulty, qtype, diagramStr);
                return data;

            } catch (Exception e) {
                log.error("[{}/{}] {} attempt {} error: {}", i, total, externalId, attempt, e.getMessage());
                if (attempt > MAX_RETRIES) {
                    log.error("[{}/{}] {} all retries exhausted — skipping", i, total, externalId);
                    return null;
                }
            }
        }
        return null;
    }

    @Transactional
    public void saveQuestion(JsonNode data, String externalId, String section, String domain,
                             String skillKey, int difficulty, String qtype) {
        String correctAnswer = data.path("correctAnswer").asText(null);

        // skill_key: prefer the explicit arg; fall back to whatever the model returned
        String resolvedSkillKey = (skillKey != null && !skillKey.isBlank())
                ? skillKey
                : nullIfEmpty(data.path("skillKey").asText(null));

        Question q = Question.builder()
                .externalId(externalId)
                .section(section)
                .domain(domain)
                .skill(data.path("skill").asText(null))
                .skillKey(resolvedSkillKey)
                .scenarioTag(nullIfEmpty(data.path("scenarioTag").asText(null)))
                .difficulty((short) difficulty)
                .questionType(qtype)
                .questionStem(data.path("questionStem").asText(""))
                .optionA(nullIfEmpty(sanitizeSingleLine(data.path("optionA").asText(null))))
                .optionB(nullIfEmpty(sanitizeSingleLine(data.path("optionB").asText(null))))
                .optionC(nullIfEmpty(sanitizeSingleLine(data.path("optionC").asText(null))))
                .optionD(nullIfEmpty(sanitizeSingleLine(data.path("optionD").asText(null))))
                .sprMin(parseSprBound(data, "sprMin", correctAnswer, true))
                .sprMax(parseSprBound(data, "sprMax", correctAnswer, false))
                .explanationShort(sanitizeSingleLine(data.path("explanationShort").asText(null)))
                .explanationSteps(toJsonString(data.path("explanationSteps")))
                .trapCategory(data.path("trapCategory").asText(null))
                .trapExplanation(data.path("trapExplanation").asText(null))
                .coreConcept(toJsonString(data.path("coreConcept")))
                .prerequisites(toJsonString(data.path("prerequisites")))
                .animation(toJsonString(data.path("animation")))
                .pool(data.path("pool").asText("both"))
                .passageText(nullIfEmpty(data.path("passageText").asText(null)))
                .passageSource(nullIfEmpty(data.path("passageSource").asText(null)))
                .diagram(toJsonString(data.path("diagram")))
                .calculatorOk("math".equals(section))
                .source("ai_generated")
                .status(QuestionStatus.GENERATED.lower())
                .generatedAt(OffsetDateTime.now())
                .build();

        questionRepository.save(q);

        if (correctAnswer != null && !correctAnswer.isBlank()) {
            QuestionAnswer qa = QuestionAnswer.builder()
                    .question(q)
                    .correctAnswer(correctAnswer)
                    .build();
            questionAnswerRepository.save(qa);
        }
    }

    // ─── Helpers ──────────────────────────────────────────────────────────

    /**
     * Validates MCQ option uniqueness using only the data Claude already returned — no extra API call.
     *
     * Checks performed (all free):
     * 1. All four option texts are distinct (normalised) — catches copy-paste duplicates.
     * 2. distractorErrors is present and covers exactly 3 wrong options — if Claude couldn't
     *    explain why an option is wrong, it may not actually be wrong.
     * 3. None of the distractor error texts contain red-flag phrases that suggest the option
     *    could also be correct ("also correct", "equivalent", "valid", "could be", "both").
     *
     * Returns null if everything looks fine, or a short error description to log.
     * Fails open (returns null) for any parsing issue so generation is never blocked by infra errors.
     */
    private String validateMcqUniqueness(JsonNode data) {
        try {
            String correct = data.path("correctAnswer").asText("").toUpperCase().trim();
            String[] letters = {"A", "B", "C", "D"};
            Map<String, String> options = new LinkedHashMap<>();
            options.put("A", normalizeOption(data.path("optionA").asText("")));
            options.put("B", normalizeOption(data.path("optionB").asText("")));
            options.put("C", normalizeOption(data.path("optionC").asText("")));
            options.put("D", normalizeOption(data.path("optionD").asText("")));

            // 1. All options must be present
            for (String l : letters) {
                if (options.get(l).isBlank()) return "option " + l + " is blank";
            }

            // 2. All four options must be distinct
            long distinctCount = options.values().stream().distinct().count();
            if (distinctCount < 4) return "duplicate options detected (" + distinctCount + " distinct out of 4)";

            // 3. distractorErrors must cover exactly the 3 wrong options
            JsonNode errors = data.path("distractorErrors");
            if (errors.isMissingNode() || errors.isNull()) {
                // Tolerate missing field — model may not always produce it
                log.debug("  distractorErrors missing — skipping distractor text check");
                return null;
            }
            List<String> errorKeys = new ArrayList<>();
            errors.fieldNames().forEachRemaining(errorKeys::add);
            if (errorKeys.size() != 3) {
                return "distractorErrors has " + errorKeys.size() + " entries (expected 3)";
            }
            // All three error keys must be wrong options (not the correct answer)
            for (String key : errorKeys) {
                if (key.equalsIgnoreCase(correct)) {
                    return "distractorErrors incorrectly includes the correct answer (" + correct + ")";
                }
            }

            // 4. Red-flag phrases in distractor explanations
            List<String> RED_FLAGS = List.of(
                "also correct", "equivalent", "could also be", "both are", "valid answer",
                "is also valid", "can also", "is correct too", "works as well"
            );
            for (String key : errorKeys) {
                String explanation = errors.path(key).asText("").toLowerCase();
                for (String flag : RED_FLAGS) {
                    if (explanation.contains(flag)) {
                        return "distractor " + key + " explanation contains red-flag phrase: \"" + flag + "\"";
                    }
                }
            }

            return null; // all checks passed
        } catch (Exception e) {
            log.debug("  validateMcqUniqueness error (skipping): {}", e.getMessage());
            return null; // fail open
        }
    }

    /** Normalises an option text for duplicate detection: lowercase, strip LaTeX/whitespace. */
    private String normalizeOption(String text) {
        if (text == null) return "";
        return text.toLowerCase()
                   .replaceAll("\\$|\\\\[a-zA-Z]+", " ") // strip LaTeX commands
                   .replaceAll("[^a-z0-9.\\-]", " ")
                   .replaceAll("\\s+", " ")
                   .trim();
    }

    /**
     * Returns true if {@code newStem} is a near-duplicate of any existing non-rejected
     * question in the same domain, using Jaccard word-set similarity.
     * Fails open (returns false) if the DB query fails, so generation is never
     * blocked by an infrastructure error.
     */
    private boolean isDuplicateStem(String newStem, String domain) {
        try {
            List<String> existingStems = questionRepository.findAllStemsForDomain(domain);
            Set<String> newWords = wordSet(normalizeStem(newStem));
            if (newWords.isEmpty()) return false;

            for (String existing : existingStems) {
                Set<String> existingWords = wordSet(normalizeStem(existing));
                double similarity = jaccardSimilarity(newWords, existingWords);
                if (similarity >= DUPLICATE_THRESHOLD) {
                    log.warn("  Duplicate detected (jaccard={:.2f}) against: \"{}\"",
                            similarity,
                            existing.length() > 80 ? existing.substring(0, 77) + "..." : existing);
                    return true;
                }
            }
            return false;
        } catch (Exception e) {
            log.warn("Duplicate stem check failed — skipping check: {}", e.getMessage());
            return false; // fail open
        }
    }

    /** Lowercases, strips LaTeX and punctuation, collapses whitespace. */
    private String normalizeStem(String stem) {
        if (stem == null) return "";
        return stem
                .toLowerCase()
                .replaceAll("\\\\[a-zA-Z]+", " ")   // \frac, \sqrt, \cdot …
                .replaceAll("[\\\\()\\[\\]{}^_$]", " ") // LaTeX delimiters
                .replaceAll("[^a-z0-9 ]", " ")          // strip remaining punctuation
                .replaceAll("\\s+", " ")
                .trim();
    }

    private Set<String> wordSet(String text) {
        if (text == null || text.isBlank()) return Set.of();
        return new HashSet<>(Arrays.asList(text.split(" ")));
    }

    private double jaccardSimilarity(Set<String> a, Set<String> b) {
        if (a.isEmpty() || b.isEmpty()) return 0.0;
        long intersection = a.stream().filter(b::contains).count();
        long union = Stream.concat(a.stream(), b.stream()).distinct().count();
        return (double) intersection / union;
    }

    private String extractJson(String raw) {
        raw = raw.strip();
        if (raw.startsWith("```")) {
            raw = raw.contains("\n") ? raw.substring(raw.indexOf('\n') + 1) : raw.substring(3);
        }
        if (raw.contains("```")) raw = raw.substring(0, raw.lastIndexOf("```"));
        raw = raw.strip();
        int start = raw.indexOf('{');
        int end   = raw.lastIndexOf('}');
        if (start != -1 && end > start) raw = raw.substring(start, end + 1);
        return raw;
    }

    /**
     * Port of fix_latex_escapes from generate_questions.py.
     * Claude writes single backslashes in LaTeX that are invalid in JSON.
     * This doubles every bare backslash that is not \\", \\\\, or \\uXXXX.
     *
     * Special case: \t, \n, \r, \b, \f are valid JSON escapes BUT also start
     * many LaTeX commands (\text, \theta, \neq, \nabla, \beta, \bar, \frac, etc.).
     * Disambiguation rule: if the character after the escape letter is [a-zA-Z],
     * it's a LaTeX command and must be doubled. Otherwise it's a real JSON escape.
     *
     * Examples:
     *   \text{cm}  → next after 't' is 'e' (letter) → double → \\text{cm}  ✓
     *   \t + space → next after 't' is ' ' (non-letter) → real tab → leave ✓
     *   \frac{1}{2}→ next after 'f' is 'r' (letter) → double → \\frac{1}{2} ✓
     *   \n + space → next after 'n' is ' ' (non-letter) → real newline → leave ✓
     */
    String fixLatexEscapes(String raw) {
        StringBuilder out = new StringBuilder(raw.length() + 64);
        int i = 0, n = raw.length();
        while (i < n) {
            char ch = raw.charAt(i);
            if (ch == '\\' && i + 1 < n) {
                char next = raw.charAt(i + 1);
                if (next == '"' || next == '\\') {
                    // Unambiguously valid JSON escapes — leave untouched
                    out.append(ch);
                    out.append(next);
                    i += 2;
                } else if ((next == 'n' || next == 't' || next == 'r' || next == 'b' || next == 'f')
                        && (i + 2 < n && Character.isLetter(raw.charAt(i + 2)))) {
                    // Looks like a JSON escape but followed by a letter → LaTeX command
                    // e.g. \text, \theta, \neq, \nabla, \beta, \bar, \frac
                    out.append("\\\\");
                    i += 1;
                } else if (next == 'n' || next == 't' || next == 'r' || next == 'b' || next == 'f') {
                    // Real JSON whitespace escape (\n, \t, \r, \b, \f) — leave untouched
                    out.append(ch);
                    out.append(next);
                    i += 2;
                } else if (next == 'u' && i + 5 <= n &&
                        raw.substring(i + 2, Math.min(i + 6, n)).chars().allMatch(c ->
                                (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F'))) {
                    out.append(raw, i, i + 6);
                    i += 6;
                } else {
                    out.append("\\\\");
                    i += 1;
                }
            } else {
                out.append(ch);
                i++;
            }
        }
        return out.toString();
    }

    /**
     * Validates the diagram uses the named-shape format the renderer expects.
     * Returns null if valid, or an error description if invalid.
     *
     * VALID:   svgConfig has a top-level "shape" field  (e.g. "triangle", "circle")
     *          OR diagram is null / chartjs
     * INVALID: svgConfig has raw "shapes" array or "elements" array without a named "shape"
     *          (Claude occasionally invents a raw pixel format — the renderer can't handle it reliably)
     */
    private String validateDiagramFormat(JsonNode data) {
        JsonNode diagram = data.path("diagram");
        if (diagram.isNull() || diagram.isMissingNode()) return null;

        String dtype = diagram.path("diagramType").asText(diagram.path("type").asText(""));
        String domain = data.path("domain").asText("");

        // Geometry must never use Chart.js — it produces scatter plots of triangles which is wrong
        if ("chartjs".equals(dtype) && "geometry_trigonometry".equals(domain)) {
            return "chartjs forbidden for geometry_trigonometry domain — use svg_programmatic";
        }
        if ("chartjs".equals(dtype)) return null; // chartjs valid for data/stats domains

        JsonNode cfg = diagram.path("svgConfig");
        if (cfg.isNull() || cfg.isMissingNode()) return "svgConfig missing";

        // Must have a named "shape" field
        if (cfg.path("shape").isMissingNode() || cfg.path("shape").asText("").isBlank()) {
            // Raw formats: "shapes" array or "elements" array without a named shape
            if (!cfg.path("shapes").isMissingNode())   return "raw 'shapes' array used — must use named shape";
            if (!cfg.path("elements").isMissingNode())  return "raw 'elements' array used — must use named shape";
            return "svgConfig missing 'shape' field";
        }
        return null; // valid
    }

    private boolean hasArtifacts(JsonNode data) {
        StringBuilder text = new StringBuilder();
        // Check all text fields that could contain AI reasoning leakage
        text.append(data.path("explanationShort").asText("").toLowerCase()).append(" ");
        text.append(data.path("trapExplanation").asText("").toLowerCase()).append(" ");
        JsonNode steps = data.path("explanationSteps");
        if (steps.isArray()) {
            for (JsonNode step : steps) {
                text.append(step.path("content").asText("").toLowerCase()).append(" ");
                text.append(step.path("title").asText("").toLowerCase()).append(" ");
                text.append(step.path("math").asText("").toLowerCase()).append(" ");
            }
        }
        JsonNode cc = data.path("coreConcept");
        if (!cc.isMissingNode()) {
            text.append(cc.path("summary").asText("").toLowerCase()).append(" ");
            text.append(cc.path("title").asText("").toLowerCase()).append(" ");
        }
        JsonNode prereqs = data.path("prerequisites");
        if (prereqs.isArray()) {
            for (JsonNode p : prereqs) {
                text.append(p.path("why").asText("").toLowerCase()).append(" ");
            }
        }
        String t = text.toString();
        return ARTIFACT_PHRASES.stream().anyMatch(t::contains);
    }

    private String pickSection(String arg) {
        if (arg != null && !arg.isBlank()) return arg;
        return random.nextBoolean() ? "math" : "reading_writing";
    }

    /** Deterministically maps a domain key to its section — no randomness. */
    private String sectionForDomain(String domain) {
        return MATH_DOMAIN_WEIGHTS.containsKey(domain) ? "math" : "reading_writing";
    }

    private String pickDomain(String section) {
        return "math".equals(section)
                ? weightedChoice(MATH_DOMAIN_WEIGHTS)
                : weightedChoice(RW_DOMAIN_WEIGHTS);
    }

    private int pickDifficulty() {
        int total = 0;
        for (int i = 1; i <= 7; i++) total += DIFFICULTY_WEIGHTS[i];
        int r = random.nextInt(total);
        int cum = 0;
        for (int i = 1; i <= 7; i++) {
            cum += DIFFICULTY_WEIGHTS[i];
            if (r < cum) return i;
        }
        return 4;
    }

    private String pickQuestionType(String section) {
        if (!"math".equals(section)) return "mcq";
        return random.nextInt(100) < 80 ? "mcq" : "spr";
    }

    private boolean pickHasDiagram(String section, String domain) {
        if (!"math".equals(section)) return false;
        double prob = DIAGRAM_PROBS.getOrDefault(domain, 0.0);
        return random.nextDouble() < prob;
    }

    /**
     * Geometry/trigonometry → always SVG (shapes, angles, triangles — never Chart.js)
     * Algebra / advanced_math → SVG for coordinate planes, function graphs; rarely Chart.js
     * Problem solving / data → mostly Chart.js (bar, histogram, scatter, box plot)
     * Reading/writing → SVG only (passage diagrams, tables)
     */
    private String pickDiagramType(String domain) {
        return switch (domain == null ? "" : domain) {
            case "geometry_trigonometry" -> "svg_programmatic";          // 100% SVG
            case "algebra"              -> random.nextInt(100) < 80
                                            ? "svg_programmatic"         // 80% SVG coordinate planes
                                            : "chartjs";
            case "advanced_math"        -> random.nextInt(100) < 85
                                            ? "svg_programmatic"         // 85% SVG function graphs
                                            : "chartjs";
            case "problem_solving_data" -> random.nextInt(100) < 20
                                            ? "svg_programmatic"         // 20% SVG, 80% Chart.js
                                            : "chartjs";
            default                     -> "svg_programmatic";
        };
    }

    private String weightedChoice(Map<String, Integer> weights) {
        int total = weights.values().stream().mapToInt(Integer::intValue).sum();
        int r = random.nextInt(total);
        int cum = 0;
        for (Map.Entry<String, Integer> e : weights.entrySet()) {
            cum += e.getValue();
            if (r < cum) return e.getKey();
        }
        return weights.keySet().iterator().next();
    }

    private String nullIfEmpty(String v) {
        return (v == null || v.isBlank() || "null".equals(v)) ? null : v;
    }

    /**
     * Strips newlines and trims for fields that must be single-line:
     * options, explanationShort, passageSource, skill label.
     * questionStem and passageText keep newlines — they're used for
     * display-math line breaks and multi-line passages.
     */
    private String sanitizeSingleLine(String v) {
        if (v == null) return null;
        return v.replace('\n', ' ').replace('\r', ' ').replaceAll(" {2,}", " ").trim();
    }

    private BigDecimal parseBigDecimal(JsonNode node, String field) {
        JsonNode n = node.path(field);
        if (n.isNull() || n.isMissingNode()) return null;
        try { return new BigDecimal(n.asText()); } catch (Exception e) { return null; }
    }

    /**
     * Parse sprMin/sprMax and guarantee the correct answer falls within [min, max].
     * If Claude returned a range that excludes the answer (e.g. min=0, max=999 but answer=-12),
     * clamp the bound so the answer is always valid.
     */
    private BigDecimal parseSprBound(JsonNode node, String field, String answer, boolean isMin) {
        BigDecimal bound = parseBigDecimal(node, field);
        if (answer == null || answer.isBlank()) return bound;
        BigDecimal answerVal;
        try { answerVal = new BigDecimal(answer.trim()); } catch (Exception e) { return bound; }

        if (isMin) {
            BigDecimal defaultMin = new BigDecimal("-9999");
            if (bound == null) return defaultMin;
            // If answer < min, expand min to cover the answer with a little headroom
            return bound.compareTo(answerVal) > 0 ? answerVal.subtract(BigDecimal.ONE) : bound;
        } else {
            BigDecimal defaultMax = new BigDecimal("9999");
            if (bound == null) return defaultMax;
            // If answer > max, expand max
            return bound.compareTo(answerVal) < 0 ? answerVal.add(BigDecimal.ONE) : bound;
        }
    }

    private String toJsonString(JsonNode node) {
        if (node == null || node.isNull() || node.isMissingNode()) return null;
        if (node.isTextual()) return node.asText();
        try { return objectMapper.writeValueAsString(node); } catch (Exception e) { return null; }
    }
}
