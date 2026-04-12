package com.satengine.api.gap;

import com.satengine.dto.GapAnalysisRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/gaps")
@RequiredArgsConstructor
public class GapAnalysisController {

    private final GapAnalysisService gapAnalysisService;

    /**
     * POST /api/gaps/analyze
     * Takes a question ID + the student's wrong answer, calls Claude to generate
     * diagnostic probe questions and gap lessons, returns them as raw JSON.
     */
    @PostMapping(value = "/analyze", produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<String> analyze(@RequestBody GapAnalysisRequest request) {
        String truncatedAnswer = request.studentAnswer() != null
                ? request.studentAnswer().substring(0, Math.min(10, request.studentAnswer().length()))
                : "null";
        log.info("gap analysis requested questionId={} studentAnswer={}", request.questionId(), truncatedAnswer);
        String json = gapAnalysisService.analyze(request.questionId(), request.studentAnswer());
        return ResponseEntity.ok(json);
    }
}
