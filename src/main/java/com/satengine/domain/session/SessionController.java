package com.satengine.domain.session;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.dto.*;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@Slf4j
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
            @Valid @RequestBody CreateSessionRequest request,
            HttpSession httpSession
    ) {
        UUID userId = resolveUserId(httpSession);
        Session session = sessionService.createSession(userId, request);
        int total = computeTotal(session.getDomainBandCounts());
        log.info("session created id={} userId={} total={} section={}",
                session.getId(), userId, total, session.getSection());
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
    public ResponseEntity<SessionResponse> getSession(
            @PathVariable UUID id,
            HttpSession httpSession
    ) {
        UUID userId = requireAuth(httpSession);
        sessionService.requireOwnership(id, userId);
        SessionResponse response = sessionService.getSessionStatus(id);
        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/sessions/{id}/next
     * Return the next unanswered question for this session.
     * Returns 204 No Content when the question pool is exhausted.
     */
    @GetMapping("/{id}/next")
    public ResponseEntity<QuestionResponse> getNextQuestion(
            @PathVariable UUID id,
            HttpSession httpSession
    ) {
        UUID userId = requireAuth(httpSession);
        sessionService.requireOwnership(id, userId);
        log.debug("next question requested session={}", id);
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
            @Valid @RequestBody SubmitAnswerRequest request,
            HttpSession httpSession
    ) {
        UUID userId = requireAuth(httpSession);
        sessionService.requireOwnership(id, userId);
        AnswerFeedback feedback = sessionService.submitAnswer(id, request);
        log.info("answer submitted session={} question={} correct={}",
                id, request.questionId(), feedback.isCorrect());
        return ResponseEntity.ok(feedback);
    }

    /**
     * Returns the userId from the HTTP session, or throws 401 if not authenticated.
     */
    private UUID requireAuth(HttpSession httpSession) {
        String userIdStr = (String) httpSession.getAttribute("userId");
        if (userIdStr == null) {
            log.warn("unauthenticated session API request");
            throw new org.springframework.web.server.ResponseStatusException(
                    org.springframework.http.HttpStatus.UNAUTHORIZED, "Not authenticated");
        }
        try {
            return UUID.fromString(userIdStr);
        } catch (IllegalArgumentException e) {
            log.warn("malformed userId in session: {}", userIdStr);
            throw new org.springframework.web.server.ResponseStatusException(
                    org.springframework.http.HttpStatus.UNAUTHORIZED, "Not authenticated");
        }
    }

    /** Extract userId UUID from HTTP session, or null if not logged in. */
    private UUID resolveUserId(HttpSession httpSession) {
        String userIdStr = (String) httpSession.getAttribute("userId");
        if (userIdStr == null) return null;
        try { return UUID.fromString(userIdStr); } catch (Exception e) { return null; }
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
