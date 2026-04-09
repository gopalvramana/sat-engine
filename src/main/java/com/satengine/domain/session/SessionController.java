package com.satengine.domain.session;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.dto.*;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/sessions")
@RequiredArgsConstructor
public class SessionController {

    private final SessionService sessionService;
    private final ObjectMapper objectMapper;

    /**
     * POST /api/sessions
     * Create a new practice session. Returns session status including the new session ID.
     */
    @PostMapping
    public ResponseEntity<SessionResponse> createSession(
            @Valid @RequestBody CreateSessionRequest request
    ) {
        Session session = sessionService.createSession(request);
        int total = computeTotal(session.getDomainBandCounts());
        SessionResponse response = new SessionResponse(
                session.getId(),
                session.getSessionType(),
                session.getSection(),
                session.getStatus(),
                session.getStartedAt(),
                0,
                0,
                total
        );
        return ResponseEntity.status(201).body(response);
    }

    /**
     * GET /api/sessions/{id}
     * Return current session status with answer counts.
     */
    @GetMapping("/{id}")
    public ResponseEntity<SessionResponse> getSession(@PathVariable UUID id) {
        SessionResponse response = sessionService.getSessionStatus(id);
        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/sessions/{id}/next
     * Return the next unanswered question for this session.
     * Returns 204 No Content when the question pool is exhausted.
     */
    @GetMapping("/{id}/next")
    public ResponseEntity<QuestionResponse> getNextQuestion(@PathVariable UUID id) {
        return sessionService.getNextQuestion(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.noContent().build());
    }

    /**
     * POST /api/sessions/{id}/answers
     * Submit an answer; returns immediate feedback including the correct answer.
     */
    @PostMapping("/{id}/answers")
    public ResponseEntity<AnswerFeedback> submitAnswer(
            @PathVariable UUID id,
            @Valid @RequestBody SubmitAnswerRequest request
    ) {
        AnswerFeedback feedback = sessionService.submitAnswer(id, request);
        return ResponseEntity.ok(feedback);
    }

    /** Sum all band counts from the stored JSON string, or 0 if none. */
    private int computeTotal(String domainBandCountsJson) {
        if (domainBandCountsJson == null) return 0;
        try {
            Map<String, Map<String, Integer>> map = objectMapper.readValue(
                    domainBandCountsJson, new TypeReference<>() {});
            return map.values().stream()
                    .flatMap(bands -> bands.values().stream())
                    .mapToInt(Integer::intValue).sum();
        } catch (Exception e) { return 0; }
    }
}
