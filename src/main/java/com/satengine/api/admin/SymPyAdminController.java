package com.satengine.api.admin;

import com.fasterxml.jackson.annotation.JsonRawValue;
import com.satengine.admin.PipelineJobService;
import com.satengine.domain.sympy.*;
import com.satengine.dto.SymPyQuestionResponse;
import com.satengine.pipeline.sympy.MathObjectService;
import com.satengine.pipeline.sympy.SymPyGenerateStage;
import com.satengine.pipeline.sympy.SymPyPromoteService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.concurrent.CompletableFuture;

@RestController
@RequestMapping("/api/admin/sympy")
@RequiredArgsConstructor
public class SymPyAdminController {

    private final SymPyQuestionRepository       sympyRepo;
    private final SymPyQuestionAnswerRepository answerRepo;
    private final SymPyGenerateStage            sympyGenerateStage;
    private final SymPyPromoteService           sympyPromoteService;
    private final PipelineJobService            pipelineJobService;
    private final MathObjectService             mathObjectService;

    /** GET /api/admin/sympy/questions?status=generated|flagged|approved|rejected|all */
    @GetMapping("/questions")
    public List<SymPyQuestionResponse> list(
            @RequestParam(defaultValue = "all") String status,
            @RequestParam(required = false)     String skillKey,
            @RequestParam(required = false)     Integer difficulty) {

        List<SymPyQuestion> questions = fetchFiltered(status, skillKey, difficulty);
        return questions.stream().map(this::toResponse).toList();
    }

    /** GET /api/admin/sympy/questions/{id} */
    @GetMapping("/questions/{id}")
    public ResponseEntity<SymPyQuestionResponse> get(@PathVariable UUID id) {
        return sympyRepo.findById(id)
                .map(q -> ResponseEntity.ok(toResponse(q)))
                .orElse(ResponseEntity.notFound().build());
    }

    /** PATCH /api/admin/sympy/questions/{id}/approve */
    @PatchMapping("/questions/{id}/approve")
    @Transactional
    public ResponseEntity<Void> approve(@PathVariable UUID id) {
        sympyRepo.findById(id).ifPresent(q -> {
            q.setStatus("approved");
            sympyRepo.save(q);
        });
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/sympy/questions/{id}/reject */
    @PatchMapping("/questions/{id}/reject")
    @Transactional
    public ResponseEntity<Void> reject(@PathVariable UUID id) {
        sympyRepo.findById(id).ifPresent(q -> {
            q.setStatus("rejected");
            sympyRepo.save(q);
        });
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/sympy/questions/{id}/pending — revert to generated */
    @PatchMapping("/questions/{id}/pending")
    @Transactional
    public ResponseEntity<Void> revert(@PathVariable UUID id) {
        sympyRepo.findById(id).ifPresent(q -> {
            q.setStatus("generated");
            sympyRepo.save(q);
        });
        return ResponseEntity.noContent().build();
    }

    /**
     * GET /api/admin/sympy/variants?skill=linear_eq_two_var&difficulty=3[&template=function_shift]
     *
     * Returns JSON: {"template": ["v1","v2",...], ...} (all templates at that difficulty)
     * or {"variants": ["v1","v2",...]} when template is specified.
     *
     * Currently supported for: linear_eq_two_var
     */
    @GetMapping("/variants")
    public ResponseEntity<String> variants(
            @RequestParam String skill,
            @RequestParam(defaultValue = "3") int difficulty,
            @RequestParam(required = false) String template) {
        try {
            String json = mathObjectService.listVariants(skill, difficulty, template);
            return ResponseEntity.ok()
                    .header("Content-Type", "application/json")
                    .body(json);
        } catch (Exception e) {
            return ResponseEntity.badRequest()
                    .header("Content-Type", "application/json")
                    .body("{\"error\":\"" + e.getMessage().replace("\"", "'") + "\"}");
        }
    }

    /** POST /api/admin/sympy/generate?skill=circles&difficulty=3&count=5&pool=drill&template=T&variant=V
     *  When pool=diagnostic: ignores skill+difficulty+template, runs d3+d4 for all skills. */
    @PostMapping("/generate")
    public ResponseEntity<Map<String, Object>> generate(
            @RequestParam(required = false) String skill,
            @RequestParam(defaultValue = "3") int difficulty,
            @RequestParam(defaultValue = "3") int count,
            @RequestParam(defaultValue = "drill") String pool,
            @RequestParam(required = false) String template,
            @RequestParam(required = false) String variant) {

        if ("diagnostic".equalsIgnoreCase(pool)) {
            String jobId = pipelineJobService.startDiagnosticBatch(count);
            return ResponseEntity.accepted().body(Map.of(
                "status",     "started",
                "jobId",      jobId,
                "skill",      "all",
                "difficulty", "d3+d4",
                "count",      count * 2,
                "pool",       "diagnostic"
            ));
        }

        String jobId = pipelineJobService.startSympyJob(skill, difficulty, count, pool, template, variant);
        return ResponseEntity.accepted().body(Map.of(
            "status",   "started",
            "jobId",    jobId,
            "skill",    skill != null ? skill : "all",
            "difficulty", difficulty,
            "count",    count,
            "pool",     pool,
            "template", template != null ? template : "",
            "variant",  variant  != null ? variant  : ""
        ));
    }

    /** PATCH /api/admin/sympy/questions/{id}/approve-and-promote — approve + copy to production */
    @PatchMapping("/questions/{id}/approve-and-promote")
    @Transactional
    public ResponseEntity<Map<String, Object>> approveAndPromote(@PathVariable UUID id) {
        return sympyRepo.findById(id).map(q -> {
            // Override pool if provided via request param (optional)
            q.setStatus("approved");
            sympyRepo.save(q);
            UUID productionId = sympyPromoteService.promote(id);
            return ResponseEntity.ok(Map.<String, Object>of(
                "sympyId",       id,
                "productionId",  productionId,
                "externalId",    q.getExternalId(),
                "status",        "promoted"
            ));
        }).orElse(ResponseEntity.notFound().build());
    }

    /** PATCH /api/admin/sympy/questions/{id}/pool — override pool tag before approval */
    @PatchMapping("/questions/{id}/pool")
    @Transactional
    public ResponseEntity<Void> updatePool(@PathVariable UUID id,
                                           @RequestParam String pool) {
        sympyRepo.findById(id).ifPresent(q -> {
            q.setPool(pool);
            sympyRepo.save(q);
        });
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/sympy/questions/{id}/stem — manually fix question stem */
    @PatchMapping("/questions/{id}/stem")
    @Transactional
    public ResponseEntity<Void> updateStem(@PathVariable UUID id,
                                           @RequestBody Map<String, String> body) {
        String newStem = body.get("questionStem");
        if (newStem == null || newStem.isBlank()) return ResponseEntity.badRequest().build();
        sympyRepo.findById(id).ifPresent(q -> {
            q.setQuestionStem(newStem.trim());
            sympyRepo.save(q);
        });
        return ResponseEntity.noContent().build();
    }

    /** GET /api/admin/sympy/stats — counts by status + skill */
    @GetMapping("/stats")
    public Map<String, Object> stats() {
        List<Object[]> bySkill  = sympyRepo.countBySkillKey();
        long total    = sympyRepo.count();
        List<SymPyQuestion> all2 = sympyRepo.findAll();
        // Active = non-reference pool
        List<SymPyQuestion> active = all2.stream()
                .filter(q -> !"reference".equals(q.getPool())).toList();

        long approved      = active.stream().filter(q -> "approved".equals(q.getStatus())).count();
        long flagged       = active.stream().filter(q -> "generated_flagged".equals(q.getStatus())).count();
        long rejected      = active.stream().filter(q -> "rejected".equals(q.getStatus())).count();
        long promoted      = all2.stream().filter(q -> "promoted".equals(q.getStatus())).count();
        long reference     = all2.stream().filter(q -> "reference".equals(q.getPool())).count();
        long pendingReview = active.stream()
                .filter(q -> "generated".equals(q.getStatus()) || "generated_flagged".equals(q.getStatus())).count();
        long activeTotal   = active.size();

        List<Map<String, Object>> skillCounts = new ArrayList<>();
        for (Object[] row : bySkill) {
            skillCounts.add(Map.of(
                "skillKey", row[0] != null ? row[0] : "unknown",
                "count",    row[1]
            ));
        }

        return Map.of(
            "total",        total,
            "activeTotal",  activeTotal,
            "pendingReview",pendingReview,
            "approved",     approved,
            "flagged",      flagged,
            "rejected",     rejected,
            "promoted",     promoted,
            "reference",    reference,
            "bySkill",      skillCounts
        );
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private List<SymPyQuestion> fetchFiltered(String status, String skillKey, Integer difficulty) {
        List<SymPyQuestion> all = sympyRepo.findAll();
        return all.stream()
                .filter(q -> "all".equalsIgnoreCase(status) || q.getStatus().equals(status))
                .filter(q -> skillKey == null  || skillKey.equals(q.getSkillKey()))
                .filter(q -> difficulty == null || q.getDifficulty() == difficulty.shortValue())
                .sorted(Comparator.comparing(SymPyQuestion::getGeneratedAt,
                        Comparator.nullsLast(Comparator.reverseOrder())))
                .toList();
    }

    private SymPyQuestionResponse toResponse(SymPyQuestion q) {
        String correctAnswer = answerRepo.findByQuestionId(q.getId())
                .map(SymPyQuestionAnswer::getCorrectAnswer)
                .orElse(null);

        return SymPyQuestionResponse.builder()
                .id(q.getId())
                .externalId(q.getExternalId())
                .status(q.getStatus())
                .section(q.getSection())
                .domain(q.getDomain())
                .skill(q.getSkill())
                .skillKey(q.getSkillKey())
                .scenarioTag(q.getScenarioTag())
                .difficulty(q.getDifficulty())
                .questionType(q.getQuestionType())
                .questionStem(q.getQuestionStem())
                .optionA(q.getOptionA())
                .optionB(q.getOptionB())
                .optionC(q.getOptionC())
                .optionD(q.getOptionD())
                .correctAnswer(correctAnswer)
                .sprMin(q.getSprMin())
                .sprMax(q.getSprMax())
                .explanationShort(q.getExplanationShort())
                .explanationSteps(q.getExplanationSteps())
                .coreConcept(q.getCoreConcept())
                .distractorRationale(q.getDistractorRationale())
                .prerequisites(q.getPrerequisites())
                .alternativeApproach(q.getAlternativeApproach())
                .diagram(q.getDiagram())
                .mathObject(q.getMathObject())
                .paramHash(q.getParamHash())
                .reviewNotes(q.getReviewNotes())
                .pool(q.getPool())
                .generatedAt(q.getGeneratedAt())
                .build();
    }
}
