package com.satengine.admin;

import com.satengine.pipeline.AgentReviewStage;
import com.satengine.pipeline.EnrichStage;
import com.satengine.pipeline.GenerateStage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedDeque;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

/**
 * Manages async pipeline jobs, capturing per-job SLF4J log output via
 * {@link JobLogAppender}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PipelineJobService {

    private final GenerateStage    generateStage;
    private final AgentReviewStage agentReviewStage;
    private final EnrichStage      enrichStage;

    /** Job state store. Entries are evicted when older than 1 hour. */
    private final ConcurrentHashMap<String, JobState> jobs = new ConcurrentHashMap<>();

    /** Max log lines per job to prevent memory leaks. */
    private static final int MAX_LOG_LINES = 500;

    /** Difficulty label → numeric value passed to GenerateStage */
    private static Integer mapDifficulty(String difficulty) {
        if (difficulty == null) return null;
        return switch (difficulty.toLowerCase()) {
            case "easy"   -> 2;
            case "medium" -> 4;
            case "hard"   -> 6;
            default       -> null;
        };
    }

    // ─── Public API ────────────────────────────────────────────────────────

    /**
     * Starts a pipeline job asynchronously.
     *
     * @param step        "generate" | "review" | "enrich"
     * @param domain      optional domain filter (e.g. "algebra")
     * @param section     optional section filter ("math" | "reading_writing")
     * @param difficulty  "easy" | "medium" | "hard" | null
     * @param count       number of questions (generate step only)
     * @param onlyFailed  re-review only failed questions (review step only)
     * @return jobId UUID string
     */
    /**
     * Runs all three steps sequentially (Generate → Review → Enrich) in one job.
     * Logs from all three stages stream into the same log buffer.
     */
    public String startAllJob(String domain, String section,
                              String difficulty, int count) {
        evictOldJobs();
        String jobId = UUID.randomUUID().toString();
        ConcurrentLinkedDeque<String> logDeque = new ConcurrentLinkedDeque<>();
        JobLogAppender.JOB_LOGS.put(jobId, logDeque);
        JobState state = new JobState(jobId, "all", "RUNNING", logDeque, Instant.now());
        jobs.put(jobId, state);

        Executor executor = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "pipeline-job-" + jobId.substring(0, 8));
            t.setDaemon(true);
            return t;
        });

        CompletableFuture.runAsync(() -> {
            MDC.put("pipelineJobId", jobId);
            try {
                log.info("══ Step 1/3 — Generate ══════════════════════════════");
                runStep("generate", domain, section, difficulty, count, false);
                log.info("══ Step 2/3 — Agent Review ══════════════════════════");
                runStep("review", domain, section, null, count, false);
                log.info("══ Step 3/3 — Enrich ════════════════════════════════");
                runStep("enrich", domain, section, null, count, false);
                log.info("══ Pipeline complete ════════════════════════════════");
                state.setStatus("DONE");
            } catch (Exception e) {
                log.error("Pipeline failed: {}", e.getMessage(), e);
                state.setStatus("FAILED");
            } finally {
                MDC.remove("pipelineJobId");
            }
        }, executor);

        return jobId;
    }

    public String startJob(String step, String domain, String section,
                           String difficulty, int count, boolean onlyFailed) {

        // Evict old jobs before accepting new ones
        evictOldJobs();

        String jobId = UUID.randomUUID().toString();
        ConcurrentLinkedDeque<String> logDeque = new ConcurrentLinkedDeque<>();

        // Register the deque in the appender's shared map BEFORE the job thread starts
        JobLogAppender.JOB_LOGS.put(jobId, logDeque);

        JobState state = new JobState(jobId, step, "RUNNING", logDeque, Instant.now());
        jobs.put(jobId, state);

        // Each job gets its own single-thread executor so MDC is isolated
        Executor executor = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "pipeline-job-" + jobId.substring(0, 8));
            t.setDaemon(true);
            return t;
        });

        CompletableFuture.runAsync(() -> {
            MDC.put("pipelineJobId", jobId);
            try {
                runStep(step, domain, section, difficulty, count, onlyFailed);
                state.setStatus("DONE");
            } catch (Exception e) {
                log.error("Job {} failed: {}", jobId, e.getMessage(), e);
                state.setStatus("FAILED");
            } finally {
                MDC.remove("pipelineJobId");
                // Keep the deque registered — caller reads it after DONE/FAILED
            }
        }, executor);

        return jobId;
    }

    public JobState getJob(String jobId) {
        return jobs.get(jobId);
    }

    // ─── Internal ─────────────────────────────────────────────────────────

    private void runStep(String step, String domain, String section,
                         String difficulty, int count, boolean onlyFailed) {
        switch (step.toLowerCase()) {
            case "generate" -> {
                Integer diff = mapDifficulty(difficulty);
                // domain null means all domains (GenerateStage handles weighted random)
                String domainArg  = (domain  != null && !domain.isBlank())  ? domain  : null;
                String sectionArg = (section != null && !section.isBlank()) ? section : null;
                generateStage.run(count, sectionArg, domainArg, null, diff);
            }
            case "review" -> {
                String domainArg  = (domain  != null && !domain.isBlank())  ? domain  : null;
                String sectionArg = (section != null && !section.isBlank()) ? section : null;
                agentReviewStage.run(onlyFailed, sectionArg, domainArg);
            }
            case "enrich" -> {
                String domainArg  = (domain  != null && !domain.isBlank())  ? domain  : null;
                String sectionArg = (section != null && !section.isBlank()) ? section : null;
                // difficulty and count not used by enrich
                enrichStage.run(false, sectionArg, domainArg);
            }
            default -> throw new IllegalArgumentException("Unknown step: " + step);
        }
    }

    /** Remove jobs older than 1 hour from both maps. */
    private void evictOldJobs() {
        Instant cutoff = Instant.now().minusSeconds(3600);
        jobs.entrySet().removeIf(e -> {
            if (e.getValue().getCreatedAt().isBefore(cutoff)) {
                JobLogAppender.JOB_LOGS.remove(e.getKey());
                return true;
            }
            return false;
        });
    }

    // ─── Inner state class ─────────────────────────────────────────────────

    public static class JobState {
        private final String jobId;
        private final String step;
        private volatile String status;
        private final ConcurrentLinkedDeque<String> logDeque;
        private final Instant createdAt;

        public JobState(String jobId, String step, String status,
                        ConcurrentLinkedDeque<String> logDeque, Instant createdAt) {
            this.jobId     = jobId;
            this.step      = step;
            this.status    = status;
            this.logDeque  = logDeque;
            this.createdAt = createdAt;
        }

        public String getJobId()    { return jobId; }
        public String getStep()     { return step; }
        public String getStatus()   { return status; }
        public Instant getCreatedAt() { return createdAt; }

        public void setStatus(String status) { this.status = status; }

        /** Returns snapshot of log lines, capped at MAX_LOG_LINES. */
        public List<String> getLogs() {
            List<String> all = new ArrayList<>(logDeque);
            if (all.size() > MAX_LOG_LINES) {
                return all.subList(all.size() - MAX_LOG_LINES, all.size());
            }
            return all;
        }

        /** Enforce cap: drop oldest lines when deque exceeds MAX_LOG_LINES. */
        public void capLogs(int maxLines) {
            while (logDeque.size() > maxLines) {
                logDeque.pollFirst();
            }
        }
    }
}
