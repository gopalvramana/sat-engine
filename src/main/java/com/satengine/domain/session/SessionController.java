package com.satengine.domain.session;

import com.satengine.dto.*;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/sessions")
@RequiredArgsConstructor
public class SessionController {

    private final SessionService sessionService;

    /**
     * POST /api/sessions
     * Create a new practice session. Returns session status including the new session ID.
     */
    @PostMapping
    public ResponseEntity<SessionResponse> createSession(
            @Valid @RequestBody CreateSessionRequest request
    ) {
        Session session = sessionService.createSession(request);
        // Build a minimal SessionResponse immediately after creation (0 answers so far)
        SessionResponse response = new SessionResponse(
                session.getId(),
                session.getSessionType(),
                session.getSection(),
                session.getStatus(),
                session.getStartedAt(),
                0,
                0
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
}
