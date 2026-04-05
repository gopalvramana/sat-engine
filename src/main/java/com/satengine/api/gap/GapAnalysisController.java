package com.satengine.api.gap;

import com.satengine.dto.GapAnalysisRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

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
        String json = gapAnalysisService.analyze(request.questionId(), request.studentAnswer());
        return ResponseEntity.ok(json);
    }
}
