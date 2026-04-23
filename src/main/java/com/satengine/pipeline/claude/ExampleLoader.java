package com.satengine.pipeline.claude;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Loads SAT-style few-shot examples from JSON files in
 * src/main/resources/narration/examples/<skill>.json
 *
 * Examples are filtered by difficulty tier (medium = d3, hard = d4-d5)
 * and injected into the Haiku narration prompt to calibrate phrasing style
 * and difficulty level.
 *
 * Files are loaded once and cached in memory — no file I/O per question.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ExampleLoader {

    private static final int MAX_EXAMPLES = 3; // inject at most 3 to keep prompt focused

    private final ObjectMapper objectMapper;

    // Cache: "skillKey:tier" → list of example maps
    private final Map<String, List<Map<String, Object>>> cache = new ConcurrentHashMap<>();

    /**
     * Returns up to 3 formatted example strings for the given skill and difficulty.
     * Returns empty string if no examples are available (e.g. easy questions, missing file).
     */
    public String buildExamplesBlock(String skillKey, int difficulty) {
        String tier = difficultyTier(difficulty);
        if (tier == null) return ""; // difficultyTier returns null only if difficulty < 1

        List<Map<String, Object>> examples = loadExamples(skillKey, tier);
        if (examples.isEmpty()) return "";

        StringBuilder sb = new StringBuilder();
        sb.append("\n## SAT Style Examples (").append(tier).append(" difficulty — ").append(skillKey.replace("_", " ")).append(")\n");
        sb.append("Study these examples for authentic SAT phrasing, question framing, and difficulty calibration.\n");
        sb.append("Do NOT copy these questions — use them only as style and difficulty guides.\n\n");

        int count = 0;
        for (Map<String, Object> ex : examples) {
            if (count >= MAX_EXAMPLES) break;
            count++;

            sb.append("Example ").append(count).append(":\n");

            // Stem
            Object stem = ex.get("stem");
            if (stem != null) sb.append("  Stem: ").append(stem).append("\n");

            // Type + correct answer
            Object type    = ex.get("type");
            Object correct = ex.get("correct");
            if (type != null && correct != null) {
                sb.append("  Type: ").append(type).append(" | Correct: ").append(correct).append("\n");
            }

            // Key SAT phrases
            Object phrases = ex.get("sat_key_phrases");
            if (phrases instanceof List<?> list && !list.isEmpty()) {
                sb.append("  SAT phrases: ").append(String.join(", ", list.stream()
                        .map(Object::toString).toList())).append("\n");
            }

            // Why this difficulty
            Object why = ex.get("why_this_difficulty");
            if (why != null) sb.append("  Difficulty note: ").append(why).append("\n");

            // One distractor rationale to show error-catching principle
            Object dr = ex.get("distractor_rationales");
            if (dr instanceof Map<?, ?> drMap && !drMap.isEmpty()) {
                Map.Entry<?, ?> first = drMap.entrySet().iterator().next();
                sb.append("  Example distractor (").append(first.getKey()).append("): ")
                  .append(first.getValue()).append("\n");
            }

            sb.append("\n");
        }

        return sb.toString();
    }

    // ── Private helpers ───────────────────────────────────────────────────────

    private List<Map<String, Object>> loadExamples(String skillKey, String tier) {
        String cacheKey = skillKey + ":" + tier;
        return cache.computeIfAbsent(cacheKey, k -> readAndFilter(skillKey, tier));
    }

    private List<Map<String, Object>> readAndFilter(String skillKey, String tier) {
        String path = "narration/examples/" + skillKey + ".json";
        ClassPathResource resource = new ClassPathResource(path);

        if (!resource.exists()) {
            log.debug("No example file for skill '{}' at {}", skillKey, path);
            return List.of();
        }

        try (InputStream is = resource.getInputStream()) {
            List<Map<String, Object>> all = objectMapper.readValue(
                    is, new TypeReference<List<Map<String, Object>>>() {});

            // Filter by difficulty tier and shuffle so we get variety across runs
            List<Map<String, Object>> filtered = all.stream()
                    .filter(ex -> tier.equals(ex.get("difficulty")))
                    .collect(java.util.stream.Collectors.toCollection(ArrayList::new));

            Collections.shuffle(filtered, new Random());
            log.debug("Loaded {} '{}' examples for skill '{}'", filtered.size(), tier, skillKey);
            return Collections.unmodifiableList(filtered);

        } catch (Exception e) {
            log.warn("Failed to load examples for skill '{}': {}", skillKey, e.getMessage());
            return List.of();
        }
    }

    /**
     * Maps numeric difficulty to tier string.
     *
     * Aligned with SAT 3-level taxonomy (Easy / Medium / Hard):
     *   d1 → "easy"
     *   d2 → "medium"
     *   d3 → "hard"
     *
     * All three levels get few-shot examples so Haiku calibrates SAT phrasing
     * correctly at every difficulty. Example JSON files must contain entries
     * for all three tiers: "easy", "medium", "hard".
     */
    private static String difficultyTier(int d) {
        if (d <= 1) return "easy";
        if (d == 2) return "medium";
        return "hard";
    }
}
