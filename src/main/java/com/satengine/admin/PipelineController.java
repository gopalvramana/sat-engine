package com.satengine.admin;

import com.satengine.domain.question.QuestionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * REST endpoints for the admin pipeline dashboard.
 * <p>
 * POST /admin/pipeline/run       — start a pipeline job
 * GET  /admin/pipeline/job/{id}  — poll job status + logs
 * GET  /admin/pipeline/stats     — question counts by domain/difficulty
 */
@RestController
@RequestMapping("/admin/pipeline")
@RequiredArgsConstructor
public class PipelineController {

    private final PipelineJobService pipelineJobService;
    private final QuestionRepository questionRepository;

    // ─── POST /admin/pipeline/run ──────────────────────────────────────────

    @PostMapping("/run")
    public ResponseEntity<Map<String, String>> run(@RequestBody RunRequest req) {
        String jobId = pipelineJobService.startJob(
                req.step(),
                req.domain(),
                req.section(),
                req.difficulty(),
                req.count() != null ? req.count() : 5,
                req.onlyFailed() != null && req.onlyFailed()
        );
        return ResponseEntity.ok(Map.of("jobId", jobId));
    }

    // ─── POST /admin/pipeline/run-all ─────────────────────────────────

    @PostMapping("/run-all")
    public ResponseEntity<Map<String, String>> runAll(@RequestBody RunRequest req) {
        String jobId = pipelineJobService.startAllJob(
                req.domain(),
                req.section(),
                req.difficulty(),
                req.count() != null ? req.count() : 5
        );
        return ResponseEntity.ok(Map.of("jobId", jobId));
    }

    // ─── GET /admin/pipeline/job/{jobId} ──────────────────────────────────

    @GetMapping("/job/{jobId}")
    public ResponseEntity<?> getJob(@PathVariable String jobId) {
        PipelineJobService.JobState state = pipelineJobService.getJob(jobId);
        if (state == null) {
            return ResponseEntity.notFound().build();
        }

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("jobId",  state.getJobId());
        body.put("step",   state.getStep());
        body.put("status", state.getStatus());
        body.put("logs",   state.getLogs());
        return ResponseEntity.ok(body);
    }

    // ─── GET /admin/pipeline/stats ─────────────────────────────────────────

    /**
     * Returns question counts per domain, broken into easy/medium/hard bands,
     * along with per-status totals for the stats bar.
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> stats() {
        // Domain breakdown (approved only, all sections)
        List<Object[]> rows = questionRepository.countByDomainAndDifficulty(null);

        List<Map<String, Object>> domainStats = rows.stream().map(row -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("domain", row[0]);
            m.put("easy",   toLong(row[1]));
            m.put("medium", toLong(row[2]));
            m.put("hard",   toLong(row[3]));
            m.put("total",  toLong(row[4]));
            return m;
        }).toList();

        // Status totals for the summary bar
        Map<String, Long> statusCounts = new HashMap<>();
        statusCounts.put("generated", questionRepository.countByStatus("generated"));
        statusCounts.put("reviewed",  questionRepository.countByStatus("reviewed"));
        statusCounts.put("enriched",  questionRepository.countByStatus("enriched"));
        statusCounts.put("approved",  questionRepository.countByStatus("approved"));

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("statusCounts", statusCounts);
        response.put("domainStats",  domainStats);
        return ResponseEntity.ok(response);
    }

    // ─── Helpers ──────────────────────────────────────────────────────────

    private long toLong(Object v) {
        if (v == null) return 0L;
        return ((Number) v).longValue();
    }

    // ─── Request DTO ──────────────────────────────────────────────────────

    public record RunRequest(
            String step,
            String domain,
            String section,
            String difficulty,
            Integer count,
            Boolean onlyFailed
    ) {}
}
