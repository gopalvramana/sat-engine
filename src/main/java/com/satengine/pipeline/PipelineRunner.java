package com.satengine.pipeline;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * CLI entry point for pipeline stages.
 *
 * ── GENERATE ──────────────────────────────────────────────────────────────
 *   # Fully automatic — domain picked randomly, skill auto-balanced per domain
 *   java -jar sat-engine.jar --job=generate --count=10
 *
 *   # Pin section only
 *   java -jar sat-engine.jar --job=generate --count=10 --section=math
 *   java -jar sat-engine.jar --job=generate --count=10 --section=reading_writing
 *
 *   # Pin domain (skill still auto-balanced within that domain)
 *   java -jar sat-engine.jar --job=generate --count=10 --domain=algebra
 *   java -jar sat-engine.jar --job=generate --count=5  --domain=algebra --difficulty=4
 *
 *   # Pin domain + explicit skill (overrides auto-balance)
 *   java -jar sat-engine.jar --job=generate --count=3 --domain=algebra --skill=linear_functions
 *   java -jar sat-engine.jar --job=generate --count=3 --domain=geometry_trigonometry --skill=pythagorean_theorem --difficulty=5
 *
 * ── AGENT REVIEW ──────────────────────────────────────────────────────────
 *   # Review all enriched (pending) questions
 *   java -jar sat-engine.jar --job=agent-review
 *
 *   # Re-review only questions that previously failed
 *   java -jar sat-engine.jar --job=agent-review --only-failed
 *
 * ── ENRICH ────────────────────────────────────────────────────────────────
 *   # Enrich reviewed questions (normal flow)
 *   java -jar sat-engine.jar --job=enrich
 *
 *   # Re-enrich all approved questions (after prompt improvement)
 *   java -jar sat-engine.jar --job=enrich --include-approved
 *
 *   # Re-enrich one domain only (test new prompt before full run)
 *   java -jar sat-engine.jar --job=enrich --include-approved --domain=algebra
 *
 *   # Re-enrich one section only
 *   java -jar sat-engine.jar --job=enrich --include-approved --section=math
 *
 *   # Enrich a single question by ID (any status)
 *   java -jar sat-engine.jar --job=enrich --id=MATH-GEO-010
 *
 * ── VISUAL CHECK ──────────────────────────────────────────────────────────
 *   # Check all animated geometry questions
 *   java -jar sat-engine.jar --job=visual-check
 *
 *   # Auto-patch fixable issues (missing labels, bad offsets)
 *   java -jar sat-engine.jar --job=visual-check --fix
 *
 *   # Check (and optionally fix) a single question
 *   java -jar sat-engine.jar --job=visual-check --id=MATH-GEO-004
 *   java -jar sat-engine.jar --job=visual-check --fix --id=MATH-GEO-004
 *
 * ── FLAGS ─────────────────────────────────────────────────────────────────
 * --count       Number of questions to generate (default: 10)
 * --section     math | reading_writing  (default: random)
 * --domain      Key from sat_taxonomy.json, e.g. algebra, geometry_trigonometry
 *               (default: random within section)
 * --skill       Canonical skill key, e.g. linear_functions, pythagorean_theorem
 *               When omitted, GenerateStage auto-picks the least-covered skill
 *               within the domain for even distribution across all 66+ skills.
 *               Skill is injected into the generation prompt and saved to skill_key.
 * --difficulty  1–7 integer (default: random 2–6)
 *
 * Normal API server startup (no --job flag): all stages are skipped.
 */
@Slf4j
@Component
@Order(10)
@RequiredArgsConstructor
public class PipelineRunner implements ApplicationRunner {

    private final GenerateStage     generateStage;
    private final AgentReviewStage  agentReviewStage;
    private final EnrichStage       enrichStage;
    private final VisualCheckStage  visualCheckStage;

    @Override
    public void run(ApplicationArguments args) {
        if (!args.containsOption("job")) return;

        List<String> jobs = args.getOptionValues("job");
        if (jobs == null || jobs.isEmpty()) {
            log.warn("--job flag provided but no value given. Use --job=generate|agent-review|enrich");
            return;
        }

        String job = jobs.get(0).toLowerCase().strip();

        switch (job) {
            case "generate"      -> runGenerate(args);
            case "agent-review"  -> runAgentReview(args);
            case "enrich"        -> runEnrich(args);
            case "visual-check"  -> runVisualCheck(args);
            default -> log.warn("Unknown --job value: '{}'. Valid: generate, agent-review, enrich, visual-check", job);
        }

        // Exit after pipeline job — don't start web server
        System.exit(0);
    }

    private void runGenerate(ApplicationArguments args) {
        int     count      = intArg(args, "count", 10);
        String  section    = stringArg(args, "section", null);
        String  domain     = stringArg(args, "domain", null);
        String  skill      = stringArg(args, "skill", null);
        Integer difficulty = args.containsOption("difficulty") ? intArg(args, "difficulty", 4) : null;
        generateStage.run(count, section, domain, skill, difficulty);
    }

    private void runEnrich(ApplicationArguments args) {
        String id = stringArg(args, "id", null);
        if (id != null) {
            enrichStage.runById(id);
            return;
        }
        boolean includeApproved = args.containsOption("include-approved");
        String  section         = stringArg(args, "section", null);
        String  domain          = stringArg(args, "domain",  null);
        enrichStage.run(includeApproved, section, domain);
    }

    private void runAgentReview(ApplicationArguments args) {
        boolean onlyFailed = args.containsOption("only-failed");
        agentReviewStage.run(onlyFailed);
    }

    private void runVisualCheck(ApplicationArguments args) {
        boolean fix    = args.containsOption("fix");
        String  onlyId = stringArg(args, "id", null);
        visualCheckStage.run(fix, onlyId);
    }

    private int intArg(ApplicationArguments args, String key, int defaultValue) {
        List<String> vals = args.getOptionValues(key);
        if (vals == null || vals.isEmpty()) return defaultValue;
        try { return Integer.parseInt(vals.get(0)); }
        catch (NumberFormatException e) { return defaultValue; }
    }

    private String stringArg(ApplicationArguments args, String key, String defaultValue) {
        List<String> vals = args.getOptionValues(key);
        if (vals == null || vals.isEmpty()) return defaultValue;
        return vals.get(0);
    }
}
