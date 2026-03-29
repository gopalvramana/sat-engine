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
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.Random;

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
            "geometry_trigonometry", 0.70, "problem_solving_data", 0.60,
            "algebra", 0.20, "advanced_math", 0.15
    );
    private static final List<String> ARTIFACT_PHRASES = List.of(
            "wait,", "wait —", "wait—", "let me recalculate", "let me re-read",
            "let me verify", "let me rewrite", "let me use", "let me try",
            "let me reconsider", "hmm,", "hmm.", "actually,", "actually—",
            "rechecking", "doesn't yield", "doesn't work", "i need to reconsider"
    );

    private final Random random = new Random();

    // ─── Public entry point ────────────────────────────────────────────────

    public void run(int count, String sectionArg, Integer difficultyArg) {
        log.info("═".repeat(60));
        log.info(" Generate Stage  count={} section={} difficulty={}", count, sectionArg, difficultyArg);
        log.info("═".repeat(60));

        int success = 0, failed = 0;
        // Cache next seq per domain within this run
        Map<String, Integer> seqCache = new java.util.HashMap<>();

        for (int i = 1; i <= count; i++) {
            String section    = pickSection(sectionArg);
            String domain     = pickDomain(section);
            int    difficulty = difficultyArg != null ? difficultyArg : pickDifficulty();
            String qtype      = pickQuestionType(section);
            boolean hasDiagram   = pickHasDiagram(section, domain);
            String  diagramType  = hasDiagram ? pickDiagramType() : null;

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

            JsonNode generated = generateWithRetry(section, domain, null, difficulty, qtype, hasDiagram, diagramType, i, count, externalId);
            if (generated == null) {
                failed++;
                continue;
            }

            saveQuestion(generated, externalId, section, domain, difficulty, qtype);
            seqCache.put(domain, seq + 1);
            success++;
        }

        log.info("─".repeat(60));
        log.info(" Results: {} saved  {} failed", success, failed);
    }

    // ─── Core generation logic ─────────────────────────────────────────────

    private JsonNode generateWithRetry(String section, String domain, String skill,
                                        int difficulty, String qtype,
                                        boolean hasDiagram, String diagramType,
                                        int i, int total, String externalId) {
        for (int attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
            try {
                String userPrompt = PromptLibrary.buildGenerateUserPrompt(
                        section, domain, skill, difficulty, qtype, hasDiagram, diagramType);
                String raw = claudeClient.call(GENERATE_MODEL, MAX_TOKENS, PromptLibrary.GENERATE_SYSTEM, userPrompt, TEMPERATURE);
                String fixed = fixLatexEscapes(extractJson(raw));
                JsonNode data = objectMapper.readTree(fixed);

                if (hasArtifacts(data)) {
                    if (attempt <= MAX_RETRIES) {
                        log.warn("[{}/{}] {} AI artifacts detected (attempt {}) — retrying...", i, total, externalId, attempt);
                        continue;
                    }
                    log.warn("[{}/{}] {} Artifacts persist after {} retries — accepting anyway", i, total, externalId, MAX_RETRIES);
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
    public void saveQuestion(JsonNode data, String externalId, String section, String domain, int difficulty, String qtype) {
        String correctAnswer = data.path("correctAnswer").asText(null);

        Question q = Question.builder()
                .externalId(externalId)
                .section(section)
                .domain(domain)
                .skill(data.path("skill").asText(null))
                .difficulty((short) difficulty)
                .questionType(qtype)
                .questionStem(data.path("questionStem").asText(""))
                .optionA(nullIfEmpty(data.path("optionA").asText(null)))
                .optionB(nullIfEmpty(data.path("optionB").asText(null)))
                .optionC(nullIfEmpty(data.path("optionC").asText(null)))
                .optionD(nullIfEmpty(data.path("optionD").asText(null)))
                .sprMin(parseBigDecimal(data, "sprMin"))
                .sprMax(parseBigDecimal(data, "sprMax"))
                .explanationShort(data.path("explanationShort").asText(null))
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
     */
    String fixLatexEscapes(String raw) {
        StringBuilder out = new StringBuilder(raw.length() + 64);
        int i = 0, n = raw.length();
        while (i < n) {
            char ch = raw.charAt(i);
            if (ch == '\\' && i + 1 < n) {
                char next = raw.charAt(i + 1);
                if (next == '"' || next == '\\') {
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

    private boolean hasArtifacts(JsonNode data) {
        StringBuilder text = new StringBuilder();
        JsonNode steps = data.path("explanationSteps");
        if (steps.isArray()) {
            for (JsonNode step : steps) {
                text.append(step.path("content").asText("").toLowerCase()).append(" ");
                text.append(step.path("title").asText("").toLowerCase()).append(" ");
            }
        }
        text.append(data.path("trapExplanation").asText("").toLowerCase()).append(" ");
        JsonNode cc = data.path("coreConcept");
        if (!cc.isMissingNode()) text.append(cc.path("summary").asText("").toLowerCase());
        String t = text.toString();
        return ARTIFACT_PHRASES.stream().anyMatch(t::contains);
    }

    private String pickSection(String arg) {
        if (arg != null && !arg.isBlank()) return arg;
        return random.nextBoolean() ? "math" : "reading_writing";
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

    private String pickDiagramType() {
        return random.nextInt(100) < 60 ? "svg_programmatic" : "chartjs";
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

    private BigDecimal parseBigDecimal(JsonNode node, String field) {
        JsonNode n = node.path(field);
        if (n.isNull() || n.isMissingNode()) return null;
        try { return new BigDecimal(n.asText()); } catch (Exception e) { return null; }
    }

    private String toJsonString(JsonNode node) {
        if (node == null || node.isNull() || node.isMissingNode()) return null;
        if (node.isTextual()) return node.asText();
        try { return objectMapper.writeValueAsString(node); } catch (Exception e) { return null; }
    }
}
