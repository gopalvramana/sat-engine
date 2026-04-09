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
    @GetMapping("/count")
    public ResponseEntity<Map<String, Object>> getQuestionCounts(
            @RequestParam(required = false) String section,
            @RequestParam(defaultValue = "1") int minDifficulty,
            @RequestParam(defaultValue = "7") int maxDifficulty
    ) {
        List<Object[]> rows = questionService.getCountsByDomain(section, minDifficulty, maxDifficulty);
        Map<String, Integer> byDomain = new HashMap<>();
        int total = 0;
        for (Object[] row : rows) {
            String domain = (String) row[0];
            int count = ((Number) row[1]).intValue();
            byDomain.put(domain, count);
            total += count;
        }
        Map<String, Object> result = new HashMap<>();
        result.put("byDomain", byDomain);
        result.put("total", total);
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
