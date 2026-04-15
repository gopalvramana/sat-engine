package com.satengine.admin;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.pipeline.GenerationMode;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.InputStream;
import java.util.ArrayList;
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
    private final ObjectMapper objectMapper;

    // ─── POST /admin/pipeline/run ──────────────────────────────────────────

    @PostMapping("/run")
    public ResponseEntity<Map<String, String>> run(@RequestBody RunRequest req) {
        GenerationMode mode = parseMode(req.mode());
        String jobId = pipelineJobService.startJob(
                req.step(),
                req.domain(),
                req.section(),
                req.difficulty(),
                req.count() != null ? req.count() : 5,
                req.onlyFailed() != null && req.onlyFailed(),
                mode
        );
        return ResponseEntity.ok(Map.of("jobId", jobId));
    }

    // ─── POST /admin/pipeline/sync ────────────────────────────────────────

    @PostMapping("/sync")
    public ResponseEntity<Map<String, String>> sync() {
        String jobId = pipelineJobService.startSyncJob();
        return ResponseEntity.ok(Map.of("jobId", jobId));
    }

    // ─── POST /admin/pipeline/run-all ─────────────────────────────────

    @PostMapping("/run-all")
    public ResponseEntity<Map<String, String>> runAll(@RequestBody RunRequest req) {
        GenerationMode mode = parseMode(req.mode());
        String jobId = pipelineJobService.startAllJob(
                req.domain(),
                req.section(),
                req.difficulty(),
                req.count() != null ? req.count() : 5,
                mode
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

    // ─── GET /admin/pipeline/spread ───────────────────────────────────────────

    /**
     * Returns skill-level spread data for the admin dashboard.
     * Merges taxonomy (all 66 skills) with live DB counts.
     * Each skill entry includes: usable/pending/failed counts per difficulty 1–7,
     * plus domain/section targets for progress calculation.
     */
    @GetMapping("/spread")
    public ResponseEntity<Map<String, Object>> spread() {
        // Load taxonomy to get canonical skill list
        Map<String, Map<String, Object>> skillMeta = new LinkedHashMap<>();
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("taxonomy/sat_taxonomy.json")) {
            if (is != null) {
                JsonNode root = objectMapper.readTree(is);
                for (JsonNode section : root.path("sections")) {
                    String sectionKey = section.path("key").asText();
                    // SAT targets per section for 10 full tests
                    int sectionTarget = "math".equals(sectionKey) ? 440 : 540;
                    for (JsonNode domain : section.path("domains")) {
                        String domainKey = domain.path("key").asText();
                        int numSkills = domain.path("skills").size();
                        // Domain share based on SAT weights
                        double domainShare = switch (domainKey) {
                            case "algebra", "advanced_math" -> 0.35;
                            case "problem_solving_data", "geometry_trigonometry" -> 0.15;
                            case "craft_structure" -> 0.28;
                            case "information_ideas" -> 0.26;
                            case "expression_ideas" -> 0.20;
                            case "standard_english" -> 0.26;
                            default -> 0.25;
                        };
                        int domainTarget = (int) (sectionTarget * domainShare);
                        int skillTarget = numSkills > 0 ? domainTarget / numSkills : 0;
                        for (JsonNode skill : domain.path("skills")) {
                            String skillKey = skill.path("key").asText();
                            Map<String, Object> meta = new LinkedHashMap<>();
                            meta.put("section", sectionKey);
                            meta.put("domain", domainKey);
                            meta.put("domainLabel", domain.path("label").asText());
                            meta.put("label", skill.path("label").asText());
                            meta.put("target", skillTarget);
                            meta.put("usable", new long[8]);   // index 0 unused; 1–7 by difficulty
                            meta.put("pending", new long[8]);
                            meta.put("failed", new long[8]);
                            skillMeta.put(sectionKey + "|" + domainKey + "|" + skillKey, meta);
                        }
                    }
                }
            }
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }

        // Merge DB counts
        try {
            for (Object[] row : questionRepository.countSpreadForDashboard()) {
                String sec   = row[0] != null ? row[0].toString() : "";
                String dom   = row[1] != null ? row[1].toString() : "";
                String sk    = row[2] != null ? row[2].toString() : "";
                int diff     = row[3] != null ? ((Number) row[3]).intValue() : 0;
                long usable  = row[4] != null ? ((Number) row[4]).longValue() : 0L;
                long pending = row[5] != null ? ((Number) row[5]).longValue() : 0L;
                long failed  = row[6] != null ? ((Number) row[6]).longValue() : 0L;
                String key = sec + "|" + dom + "|" + sk;
                Map<String, Object> meta = skillMeta.get(key);
                if (meta != null && diff >= 1 && diff <= 7) {
                    ((long[]) meta.get("usable"))[diff]  += usable;
                    ((long[]) meta.get("pending"))[diff] += pending;
                    ((long[]) meta.get("failed"))[diff]  += failed;
                }
            }
        } catch (Exception e) {
            // Return taxonomy structure with zero counts rather than failing
        }

        // Convert array fields to maps for clean JSON serialisation
        List<Map<String, Object>> skills = new java.util.ArrayList<>();
        for (Map.Entry<String, Map<String, Object>> entry : skillMeta.entrySet()) {
            String[] parts = entry.getKey().split("\\|");
            Map<String, Object> m = new LinkedHashMap<>(entry.getValue());
            m.put("skillKey", parts.length > 2 ? parts[2] : "");
            // Convert long[] arrays to {d1,d2,...,d7} maps
            long[] u = (long[]) m.remove("usable");
            long[] p = (long[]) m.remove("pending");
            long[] f = (long[]) m.remove("failed");
            Map<String, Long> usableMap = new LinkedHashMap<>();
            Map<String, Long> pendingMap = new LinkedHashMap<>();
            Map<String, Long> failedMap = new LinkedHashMap<>();
            long totalUsable = 0, totalPending = 0, totalFailed = 0;
            for (int d = 1; d <= 7; d++) {
                usableMap.put("d" + d, u[d]);
                pendingMap.put("d" + d, p[d]);
                failedMap.put("d" + d, f[d]);
                totalUsable += u[d]; totalPending += p[d]; totalFailed += f[d];
            }
            m.put("usable",  usableMap);
            m.put("pending", pendingMap);
            m.put("failed",  failedMap);
            m.put("totalUsable",  totalUsable);
            m.put("totalPending", totalPending);
            m.put("totalFailed",  totalFailed);
            skills.add(m);
        }

        return ResponseEntity.ok(Map.of("skills", skills));
    }

    // ─── GET /admin/pipeline/pool-spread ─────────────────────────────────────

    /**
     * Returns per-skill question counts by pool (drill/diagnostic/test) vs targets from taxonomy.
     * drill count   = questions where pool IN ('drill','both')
     * diagnostic count = questions where pool = 'diagnostic'
     * test count    = questions where pool IN ('test','both')
     */
    @GetMapping("/pool-spread")
    public ResponseEntity<Map<String, Object>> poolSpread() {
        // Load taxonomy — get skills + poolTarget per skill
        record SkillMeta(String label, String domain, String domainLabel, String section,
                         int drillTarget, int diagnosticTarget, int testTarget) {}

        Map<String, SkillMeta> skillMeta = new LinkedHashMap<>();
        try (InputStream is = getClass().getClassLoader().getResourceAsStream("taxonomy/sat_taxonomy.json")) {
            if (is == null) return ResponseEntity.internalServerError().build();
            JsonNode root = objectMapper.readTree(is);
            for (JsonNode section : root.path("sections")) {
                String sectionKey = section.path("key").asText();
                for (JsonNode domain : section.path("domains")) {
                    String domainKey   = domain.path("key").asText();
                    String domainLabel = domain.path("label").asText();
                    for (JsonNode skill : domain.path("skills")) {
                        String skillKey = skill.path("key").asText();
                        JsonNode pt = skill.path("poolTarget");
                        skillMeta.put(skillKey, new SkillMeta(
                                skill.path("label").asText(),
                                domainKey, domainLabel, sectionKey,
                                pt.path("drill").asInt(0),
                                pt.path("diagnostic").asInt(0),
                                pt.path("test").asInt(0)
                        ));
                    }
                }
            }
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }

        // Load DB counts: skill_key, pool, count
        // We map pool values: 'both' counts toward drill AND test; 'drill' toward drill only; etc.
        Map<String, Long> drillCounts      = new HashMap<>();
        Map<String, Long> diagnosticCounts = new HashMap<>();
        Map<String, Long> testCounts       = new HashMap<>();
        try {
            for (Object[] row : questionRepository.countBySkillAndPoolApproved()) {
                String sk   = row[0] != null ? row[0].toString() : "";
                String pool = row[1] != null ? row[1].toString() : "";
                long   cnt  = row[2] != null ? ((Number) row[2]).longValue() : 0L;
                switch (pool) {
                    case "both"       -> { drillCounts.merge(sk, cnt, Long::sum);
                                          testCounts.merge(sk, cnt, Long::sum); }
                    case "drill"      -> drillCounts.merge(sk, cnt, Long::sum);
                    case "test"       -> testCounts.merge(sk, cnt, Long::sum);
                    case "diagnostic" -> diagnosticCounts.merge(sk, cnt, Long::sum);
                }
            }
        } catch (Exception e) {
            // Return taxonomy data with zero counts
        }

        // Build response
        List<Map<String, Object>> skills = new ArrayList<>();
        for (Map.Entry<String, SkillMeta> entry : skillMeta.entrySet()) {
            String sk = entry.getKey();
            SkillMeta m = entry.getValue();
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("skillKey",    sk);
            row.put("label",       m.label());
            row.put("domain",      m.domain());
            row.put("domainLabel", m.domainLabel());
            row.put("section",     m.section());
            row.put("drill",       Map.of("count", drillCounts.getOrDefault(sk, 0L),      "target", m.drillTarget()));
            row.put("diagnostic",  Map.of("count", diagnosticCounts.getOrDefault(sk, 0L), "target", m.diagnosticTarget()));
            row.put("test",        Map.of("count", testCounts.getOrDefault(sk, 0L),        "target", m.testTarget()));
            skills.add(row);
        }

        return ResponseEntity.ok(Map.of("skills", skills));
    }

    // ─── Helpers ──────────────────────────────────────────────────────────

    private long toLong(Object v) {
        if (v == null) return 0L;
        return ((Number) v).longValue();
    }

    private GenerationMode parseMode(String mode) {
        if (mode == null || mode.isBlank()) return GenerationMode.DRILL;
        return switch (mode.toUpperCase()) {
            case "DIAGNOSTIC" -> GenerationMode.DIAGNOSTIC;
            case "TEST"       -> GenerationMode.TEST;
            default           -> GenerationMode.DRILL;
        };
    }

    // ─── Request DTO ──────────────────────────────────────────────────────

    public record RunRequest(
            String step,
            String domain,
            String section,
            String difficulty,
            Integer count,
            Boolean onlyFailed,
            String mode
    ) {}
}
