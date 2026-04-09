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
 * ═══════════════════════════════════════════════════════════════════════════
 * PIPELINE WORKFLOW
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *   Step 1  generate          → status: generated
 *   Step 2  render-normalize  → fixes $...$ math notation  (generated only)
 *   Step 3  agent-review      → automated QA               (generated → reviewed)
 *   Step 4  enrich            → pedagogy + animation        (reviewed  → enriched)
 *   Step 5  visual-check      → geometry diagram QA         (geometry only)
 *   Step 6  [validate.html]   → human approve/reject        (enriched  → approved/rejected)
 *
 *   Human review happens LAST so reviewers see the fully enriched question —
 *   solution steps, animations, choice explanations — and can catch any issues
 *   introduced during enrichment.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * ── GENERATE ──────────────────────────────────────────────────────────────
 *   java -jar sat-engine.jar --job=generate --count=10
 *   java -jar sat-engine.jar --job=generate --section=math --count=10
 *   java -jar sat-engine.jar --job=generate --section=reading_writing --count=10
 *   java -jar sat-engine.jar --job=generate --domain=algebra --count=10
 *   java -jar sat-engine.jar --job=generate --domain=algebra --difficulty=4 --count=5
 *   java -jar sat-engine.jar --job=generate --domain=algebra --skill=linear_functions --count=3
 *
 * ── RENDER NORMALIZE ──────────────────────────────────────────────────────
 *   # Default: fix newly generated questions (status=generated)
 *   java -jar sat-engine.jar --job=render-normalize
 *
 *   # Dry-run: report issues without writing to DB
 *   java -jar sat-engine.jar --job=render-normalize --dry-run
 *
 *   # Scope to section or domain (matches what you just generated)
 *   java -jar sat-engine.jar --job=render-normalize --section=math
 *   java -jar sat-engine.jar --job=render-normalize --domain=algebra
 *
 *   # Scan entire question bank (one-time backfill, any status)
 *   java -jar sat-engine.jar --job=render-normalize --all
 *   java -jar sat-engine.jar --job=render-normalize --all --dry-run
 *
 *   # Fix a single question (any status)
 *   java -jar sat-engine.jar --job=render-normalize --id=MATH-ALG-031
 *
 * ── AGENT REVIEW ──────────────────────────────────────────────────────────
 *   # Review all generated questions
 *   java -jar sat-engine.jar --job=agent-review
 *
 *   # Scope to section or domain (match what you just generated)
 *   java -jar sat-engine.jar --job=agent-review --section=reading_writing
 *   java -jar sat-engine.jar --job=agent-review --domain=algebra
 *   java -jar sat-engine.jar --job=agent-review --section=math --domain=algebra
 *
 *   # Re-review only questions that previously failed
 *   java -jar sat-engine.jar --job=agent-review --only-failed
 *   java -jar sat-engine.jar --job=agent-review --only-failed --domain=algebra
 *
 * ── ENRICH ────────────────────────────────────────────────────────────────
 *   java -jar sat-engine.jar --job=enrich
 *   java -jar sat-engine.jar --job=enrich --section=math
 *   java -jar sat-engine.jar --job=enrich --domain=algebra
 *   java -jar sat-engine.jar --job=enrich --include-approved
 *   java -jar sat-engine.jar --job=enrich --include-approved --domain=algebra
 *   java -jar sat-engine.jar --job=enrich --id=MATH-GEO-010
 *
 * ── VISUAL CHECK ──────────────────────────────────────────────────────────
 *   java -jar sat-engine.jar --job=visual-check
 *   java -jar sat-engine.jar --job=visual-check --fix
 *   java -jar sat-engine.jar --job=visual-check --fix --id=MATH-GEO-004
 *
 * ── FLAGS ─────────────────────────────────────────────────────────────────
 * --count       Number of questions to generate (default: 10)
 * --section     math | reading_writing
 * --domain      e.g. algebra, geometry_trigonometry, standard_english
 * --skill       Canonical skill key — overrides auto-balance within domain
 * --difficulty  1–7 integer (default: random 2–6)
 * --only-failed Re-review only previously failed questions
 * --include-approved  Re-enrich already-approved questions
 * --all         render-normalize: scan all statuses (default: generated only)
 * --dry-run     render-normalize: report without writing to DB
 * --fix         visual-check: auto-patch fixable diagram issues
 * --id          Target a single question by externalId
 *
 * Normal API server startup (no --job flag): all stages are skipped.
 */
@Slf4j
@Component
@Order(10)
@RequiredArgsConstructor
public class PipelineRunner implements ApplicationRunner {

    private final GenerateStage          generateStage;
    private final AgentReviewStage       agentReviewStage;
    private final EnrichStage            enrichStage;
    private final VisualCheckStage       visualCheckStage;
    private final RenderNormalizeStage   renderNormalizeStage;

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
            case "generate"          -> runGenerate(args);
            case "agent-review"      -> runAgentReview(args);
            case "enrich"            -> runEnrich(args);
            case "visual-check"      -> runVisualCheck(args);
            case "render-normalize"  -> runRenderNormalize(args);
            default -> log.warn("Unknown --job value: '{}'. Valid: generate, agent-review, enrich, visual-check, render-normalize", job);
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
        String  section    = stringArg(args, "section", null);
        String  domain     = stringArg(args, "domain",  null);
        agentReviewStage.run(onlyFailed, section, domain);
    }

    private void runVisualCheck(ApplicationArguments args) {
        boolean fix    = args.containsOption("fix");
        String  onlyId = stringArg(args, "id", null);
        visualCheckStage.run(fix, onlyId);
    }

    private void runRenderNormalize(ApplicationArguments args) {
        boolean dryRun     = args.containsOption("dry-run");
        boolean allStatuses = args.containsOption("all");
        String  section    = stringArg(args, "section", null);
        String  domain     = stringArg(args, "domain",  null);
        String  onlyId     = stringArg(args, "id",      null);
        renderNormalizeStage.run(dryRun, allStatuses, section, domain, onlyId);
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
