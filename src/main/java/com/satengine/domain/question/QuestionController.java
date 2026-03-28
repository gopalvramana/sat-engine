package com.satengine.domain.question;

import com.satengine.dto.QuestionResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
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
     * GET /api/questions/{id}
     * Returns a single question without the correct answer.
     */
    @GetMapping("/{id}")
    public ResponseEntity<QuestionResponse> getQuestion(@PathVariable UUID id) {
        QuestionResponse question = questionService.getQuestion(id);
        return ResponseEntity.ok(question);
    }
}
