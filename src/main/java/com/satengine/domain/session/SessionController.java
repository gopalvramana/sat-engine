package com.satengine.domain.session;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.dto.*;
import com.satengine.dto.SessionAnswerDetail;
import com.satengine.dto.SessionQuestionResponse;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
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
     * GET /api/sessions
     * List all sessions for the authenticated user.
     */
    @GetMapping
    public ResponseEntity<List<SessionResponse>> listSessions(HttpSession httpSession) {
        UUID userId = requireAuth(httpSession);
        return ResponseEntity.ok(sessionService.listSessionsForUser(userId));
    }

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
     * GET /api/sessions/{id}/answers
     * Return all submitted answers for a session (for review after completion).
     */
    @GetMapping("/{id}/answers")
    public ResponseEntity<List<SessionAnswerDetail>> getSessionAnswers(
            @PathVariable UUID id,
            HttpSession httpSession
    ) {
        UUID userId = requireAuth(httpSession);
        sessionService.requireOwnership(id, userId);
        return ResponseEntity.ok(sessionService.getSessionAnswers(id));
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
     * GET /api/sessions/active
     * Returns the most recent active session for the user (for resume detection).
     * Returns 204 if no active session exists.
     */
    @GetMapping("/active")
    public ResponseEntity<SessionResponse> getActiveSession(HttpSession httpSession) {
        UUID userId = requireAuth(httpSession);
        return sessionService.getActiveSessionForUser(userId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.noContent().build());
    }

    /**
     * GET /api/sessions/{id}/questions
     * Returns all pre-queued questions for the session in position order.
     * Pre-selects and caches them on first call; includes existing answers for resume.
     */
    @GetMapping("/{id}/questions")
    public ResponseEntity<List<SessionQuestionResponse>> getSessionQuestions(
            @PathVariable UUID id,
            HttpSession httpSession
    ) {
        UUID userId = requireAuth(httpSession);
        sessionService.requireOwnership(id, userId);
        return ResponseEntity.ok(sessionService.getSessionQuestions(id));
    }

    /**
     * PATCH /api/sessions/{id}/questions/{questionId}/mark
     * Toggle the "marked for review" flag on a session question.
     */
    @PatchMapping("/{id}/questions/{questionId}/mark")
    public ResponseEntity<Map<String, Boolean>> toggleMark(
            @PathVariable UUID id,
            @PathVariable UUID questionId,
            HttpSession httpSession
    ) {
        UUID userId = requireAuth(httpSession);
        sessionService.requireOwnership(id, userId);
        boolean marked = sessionService.toggleMark(id, questionId);
        return ResponseEntity.ok(Map.of("marked", marked));
    }

    /**
     * POST /api/sessions/{id}/complete
     * Mark the session as completed (called when student submits the session).
     */
    @PostMapping("/{id}/complete")
    public ResponseEntity<Void> completeSession(
            @PathVariable UUID id,
            HttpSession httpSession
    ) {
        UUID userId = requireAuth(httpSession);
        sessionService.requireOwnership(id, userId);
        sessionService.completeSession(id);
        return ResponseEntity.noContent().build();
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
