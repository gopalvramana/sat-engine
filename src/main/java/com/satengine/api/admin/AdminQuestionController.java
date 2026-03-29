package com.satengine.api.admin;

import com.satengine.dto.AdminQuestionResponse;
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

    private final AdminQuestionService adminService;

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
}
