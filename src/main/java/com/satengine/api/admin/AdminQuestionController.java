package com.satengine.api.admin;

import com.satengine.dto.AdminQuestionResponse;
import com.satengine.pipeline.EnrichAnimationStage;
import com.satengine.pipeline.EnrichChoiceExplanationsStage;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/admin/questions")
@RequiredArgsConstructor
public class AdminQuestionController {

    private final AdminQuestionService          adminService;
    private final EnrichChoiceExplanationsStage choiceEnrichStage;
    private final EnrichAnimationStage           animationStage;

    /** GET /api/admin/questions          → all questions
     *  GET /api/admin/questions?status=enriched  → filter by status */
    @GetMapping
    public List<AdminQuestionResponse> list(
            @RequestParam(defaultValue = "all") String status) {
        return adminService.getByStatus(status);
    }

    /** PATCH /api/admin/questions/{id}/approve */
    @PatchMapping("/{id}/approve")
    public ResponseEntity<Void> approve(@PathVariable UUID id) {
        adminService.approve(id);
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/questions/{id}/reject */
    @PatchMapping("/{id}/reject")
    public ResponseEntity<Void> reject(@PathVariable UUID id) {
        adminService.reject(id);
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/questions/{id}/pending — revert to enriched (pending) */
    @PatchMapping("/{id}/pending")
    public ResponseEntity<Void> revertToPending(@PathVariable UUID id) {
        adminService.revertToPending(id);
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/questions/{id}/answer — body: {"correctAnswer":"C"} */
    @PatchMapping("/{id}/answer")
    public ResponseEntity<Void> fixAnswer(
            @PathVariable UUID id,
            @RequestBody Map<String, String> body) {
        String answer = body.get("correctAnswer");
        if (answer == null || answer.isBlank())
            return ResponseEntity.badRequest().build();
        adminService.fixAnswer(id, answer);
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/questions/{id}/pool — body: {"pool":"practice"} */
    @PatchMapping("/{id}/pool")
    public ResponseEntity<Void> updatePool(
            @PathVariable UUID id,
            @RequestBody Map<String, String> body) {
        String pool = body.get("pool");
        if (pool == null || pool.isBlank())
            return ResponseEntity.badRequest().build();
        adminService.updatePool(id, pool);
        return ResponseEntity.noContent().build();
    }

    /** POST /api/admin/questions/enrich-choices — backfill choiceExplanations for all MCQ questions missing it */
    @PostMapping("/enrich-choices")
    public ResponseEntity<Map<String, Object>> enrichChoices() {
        int count = choiceEnrichStage.runBackfill();
        return ResponseEntity.ok(Map.of("enriched", count));
    }

    /** POST /api/admin/questions/{id}/enrich-choices — enrich a single question */
    @PostMapping("/{id}/enrich-choices")
    public ResponseEntity<Void> enrichChoicesById(@PathVariable UUID id) {
        String externalId = adminService.getExternalId(id);
        choiceEnrichStage.runById(externalId);
        return ResponseEntity.noContent().build();
    }

    /** POST /api/admin/questions/enrich-animations — backfill animation frames for all eligible questions */
    @PostMapping("/enrich-animations")
    public ResponseEntity<Map<String, Object>> enrichAnimations() {
        int count = animationStage.runBackfill();
        return ResponseEntity.ok(Map.of("animated", count));
    }

    /** POST /api/admin/questions/reenrich-animations — force re-enrich ALL eligible questions */
    @PostMapping("/reenrich-animations")
    public ResponseEntity<Map<String, Object>> reenrichAnimations() {
        int count = animationStage.runReenrichAll();
        return ResponseEntity.ok(Map.of("animated", count));
    }

    /** POST /api/admin/questions/{id}/enrich-animations — animate a single question */
    @PostMapping("/{id}/enrich-animations")
    public ResponseEntity<Void> enrichAnimationsById(@PathVariable UUID id) {
        String externalId = adminService.getExternalId(id);
        animationStage.runById(externalId);
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/questions/{id}/animation — directly set animation JSON
     *  Body: the raw animation object {"eligible":true,"width":280,"frames":[...]} */
    @PatchMapping("/{id}/animation")
    public ResponseEntity<Void> updateAnimation(
            @PathVariable UUID id,
            @RequestBody String animationJson) {
        adminService.updateAnimation(id, animationJson);
        return ResponseEntity.noContent().build();
    }

    /** PATCH /api/admin/questions/{id}/fields — patch any text field
     *  Allowed keys: optionA, optionB, optionC, optionD,
     *                questionStem, explanationShort, trapExplanation, passageText
     *  Body: { "optionB": "9" } */
    @PatchMapping("/{id}/fields")
    public ResponseEntity<Void> patchFields(
            @PathVariable UUID id,
            @RequestBody Map<String, String> fields) {
        if (fields == null || fields.isEmpty())
            return ResponseEntity.badRequest().build();
        adminService.patchFields(id, fields);
        return ResponseEntity.noContent().build();
    }
}
