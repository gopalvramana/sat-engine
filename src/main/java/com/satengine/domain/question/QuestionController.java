package com.satengine.domain.question;

import com.satengine.dto.QuestionResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/questions")
@RequiredArgsConstructor
public class QuestionController {

    private final QuestionService questionService;

    /**
     * GET /api/questions
     * Optional query params: section, domain, difficulty
     */
    @GetMapping
    public ResponseEntity<List<QuestionResponse>> listQuestions(
            @RequestParam(required = false) String section,
            @RequestParam(required = false) String domain,
            @RequestParam(required = false) Integer difficulty
    ) {
        List<QuestionResponse> questions = questionService.getQuestions(section, domain, difficulty);
        return ResponseEntity.ok(questions);
    }

    /**
     * GET /api/questions/count
     * Returns available question counts per domain for the session builder.
     * Query params: section (optional), minDifficulty (default 1), maxDifficulty (default 7)
     */
    /**
     * GET /api/questions/count
     * Returns available question counts per domain, broken down by difficulty band.
     * Response: { byDomain: { algebra: { easy:8, medium:15, hard:7, total:30 }, ... }, total: 65 }
     */
    @GetMapping("/count")
    public ResponseEntity<Map<String, Object>> getQuestionCounts(
            @RequestParam(required = false) String section
    ) {
        List<Object[]> rows = questionService.getCountsByDomain(section);
        Map<String, Map<String, Integer>> byDomain = new HashMap<>();
        int grandTotal = 0;
        for (Object[] row : rows) {
            String domain = (String) row[0];
            int easy   = ((Number) row[1]).intValue();
            int medium = ((Number) row[2]).intValue();
            int hard   = ((Number) row[3]).intValue();
            int total  = ((Number) row[4]).intValue();
            Map<String, Integer> bands = new HashMap<>();
            bands.put("easy", easy);
            bands.put("medium", medium);
            bands.put("hard", hard);
            bands.put("total", total);
            byDomain.put(domain, bands);
            grandTotal += total;
        }
        Map<String, Object> result = new HashMap<>();
        result.put("byDomain", byDomain);
        result.put("total", grandTotal);
        return ResponseEntity.ok(result);
    }

    /**
     * GET /api/questions/{id}
     * Returns a single question without the correct answer.
     */
    @GetMapping("/{id}")
    public ResponseEntity<QuestionResponse> getQuestion(@PathVariable UUID id) {
        QuestionResponse question = questionService.getQuestion(id);
        return ResponseEntity.ok(question);
    }
}
