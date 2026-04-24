package com.satengine.domain.session;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.sympy.SatQuestion;
import com.satengine.domain.sympy.SatQuestionRepository;
import com.satengine.dto.*;
import com.satengine.exception.DuplicateAnswerException;
import com.satengine.exception.InvalidRequestException;
import com.satengine.exception.ResourceNotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class SessionService {

    private final SessionRepository    sessionRepository;
    private final SessionAnswerRepository sessionAnswerRepository;
    private final SatQuestionRepository satQuestionRepository;
    private final ObjectMapper         objectMapper;

    /** Difficulty band → [min, max] sat_questions difficulty values (1=Easy, 2=Medium, 3=Hard) */
    private static final Map<String, int[]> BAND_RANGE = Map.of(
        "easy",   new int[]{1, 1},
        "medium", new int[]{2, 2},
        "hard",   new int[]{3, 3}
    );

    // ── Dashboard ──────────────────────────────────────────────────────────

    @Transactional(readOnly = true)
    public DashboardResponse getDashboard(UUID userId) {
        // Aggregate stats across all user answers
        List<SessionAnswer> allAnswers = sessionAnswerRepository.findAllByUserId(userId);
        long questionsAnswered = allAnswers.size();
        long correct = allAnswers.stream().filter(a -> Boolean.TRUE.equals(a.getIsCorrect())).count();
        Integer accuracyPct = questionsAnswered > 0
                ? (int) Math.round(correct * 100.0 / questionsAnswered) : null;
        Integer avgTimeSeconds = allAnswers.stream()
                .map(SessionAnswer::getTimeSpentSeconds)
                .filter(Objects::nonNull)
                .mapToInt(Integer::intValue)
                .average()
                .isPresent()
                ? (int) allAnswers.stream()
                        .map(SessionAnswer::getTimeSpentSeconds)
                        .filter(Objects::nonNull)
                        .mapToInt(Integer::intValue)
                        .average().getAsDouble()
                : null;

        long sessionsCompleted = sessionRepository.countCompletedByUser(userId);

        // Recent sessions (last 10)
        List<Session> sessions = sessionRepository.findByUserIdOrderByStartedAtDesc(userId);
        // Group answers by session for per-session stats
        Map<UUID, List<SessionAnswer>> bySession = allAnswers.stream()
                .collect(Collectors.groupingBy(SessionAnswer::getSessionId));

        DateTimeFormatter fmt = DateTimeFormatter.ISO_OFFSET_DATE_TIME;
        List<DashboardResponse.RecentSession> recentSessions = sessions.stream()
                .filter(s -> bySession.containsKey(s.getId()))   // exclude 0-answer sessions
                .limit(10)
                .map(s -> {
                    List<SessionAnswer> sAnswers = bySession.getOrDefault(s.getId(), List.of());
                    int sCorrect = (int) sAnswers.stream().filter(a -> Boolean.TRUE.equals(a.getIsCorrect())).count();
                    Integer sAcc = sAnswers.isEmpty() ? null
                            : (int) Math.round(sCorrect * 100.0 / sAnswers.size());
                    return new DashboardResponse.RecentSession(
                            s.getId().toString(),
                            s.getSection(),
                            sAnswers.size(),
                            sCorrect,
                            sAcc,
                            s.getStartedAt() != null ? s.getStartedAt().format(fmt) : null
                    );
                })
                .toList();

        // Domain accuracy map: domain → accuracy pct
        Map<String, Integer> domainAccuracy = new LinkedHashMap<>();
        List<Object[]> domainRows = sessionAnswerRepository.getDomainAccuracyForUser(userId);
        for (Object[] row : domainRows) {
            String domain       = (String) row[0];
            long   domainTotal  = ((Number) row[1]).longValue();
            long   domainRight  = ((Number) row[2]).longValue();
            if (domainTotal > 0) {
                domainAccuracy.put(domain, (int) Math.round(domainRight * 100.0 / domainTotal));
            }
        }

        // Accuracy trend: last 7 sessions with answers, oldest first
        List<Integer> accuracyTrend = recentSessions.stream()
                .limit(7)
                .filter(s -> s.accuracyPct() != null)
                .map(DashboardResponse.RecentSession::accuracyPct)
                .collect(Collectors.collectingAndThen(
                        Collectors.toList(),
                        list -> { java.util.Collections.reverse(list); return list; }
                ));

        log.info("dashboard computed userId={} sessions={} questions={} accuracy={} domains={} trendLen={}",
                userId, sessionsCompleted, questionsAnswered, accuracyPct, domainAccuracy.size(), accuracyTrend.size());
        return new DashboardResponse(
                sessionsCompleted, questionsAnswered, accuracyPct, avgTimeSeconds, recentSessions,
                domainAccuracy, accuracyTrend);
    }

    // ── Session creation ───────────────────────────────────────────────────

    @Transactional
    public Session createSession(UUID userId, CreateSessionRequest req) {
        log.info("creating session userId={} section={} totalQuestions={}",
                userId, req.section(), req.domainBandCounts() != null
                        ? req.domainBandCounts().values().stream()
                               .flatMap(m -> m.values().stream())
                               .mapToInt(Integer::intValue).sum()
                        : 0);
        String bandCountsJson = null;
        if (req.domainBandCounts() != null && !req.domainBandCounts().isEmpty()) {
            try {
                bandCountsJson = objectMapper.writeValueAsString(req.domainBandCounts());
            } catch (Exception e) {
                log.error("Failed to serialize domainBandCounts userId={} error={}", userId, e.getMessage(), e);
                throw new InvalidRequestException("Invalid domainBandCounts format: " + e.getMessage());
            }
        }
        Session session = Session.builder()
                .userId(userId)
                .sessionType(req.sessionType())
                .section(req.section())
                .domainBandCounts(bandCountsJson)
                .status("active")
                .build();
        return sessionRepository.save(session);
    }

    @Transactional
    public Optional<QuestionResponse> getNextQuestion(UUID sessionId) {
        Session session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new ResourceNotFoundException("Session", sessionId));

        // Already completed — no more questions
        if ("completed".equals(session.getStatus())) {
            log.debug("next question requested on completed session={}", sessionId);
            return Optional.empty();
        }

        List<UUID> answeredIds = sessionAnswerRepository.findAnsweredQuestionIds(sessionId);

        log.debug("picking next question session={} answered={} domainBandCounts={}",
                sessionId, answeredIds.size(),
                session.getDomainBandCounts() != null ? "present" : "absent");

        Optional<QuestionResponse> result;
        if (session.getDomainBandCounts() != null) {
            result = getNextQuestionByBandQuota(session, answeredIds);
        } else {
            // Fallback: random approved question
            Optional<SatQuestion> next = answeredIds.isEmpty()
                    ? satQuestionRepository.findNextNoExclusions(session.getSection())
                    : satQuestionRepository.findNext(session.getSection(), answeredIds);
            result = next.map(QuestionResponse::from);
        }

        if (result.isEmpty()) {
            session.setStatus("completed");
            session.setCompletedAt(OffsetDateTime.now());
            sessionRepository.save(session);
            log.info("session completed session={} answered={}", sessionId, answeredIds.size());
        }
        return result;
    }

    /**
     * Pick next question using per-domain per-band quotas.
     * Builds a list of (domain, minDiff, maxDiff, remaining) slots,
     * shuffles them, and returns the first slot that has an available question.
     */
    private Optional<QuestionResponse> getNextQuestionByBandQuota(Session session, List<UUID> answeredIds) {
        // Parse quota map: { domain -> { band -> count } }
        Map<String, Map<String, Integer>> bandCounts;
        try {
            bandCounts = objectMapper.readValue(session.getDomainBandCounts(),
                    new TypeReference<Map<String, Map<String, Integer>>>() {});
        } catch (Exception e) {
            log.error("Failed to parse domainBandCounts for session={} — falling back to empty. error={}",
                    session.getId(), e.getMessage(), e);
            return Optional.empty();
        }

        // Count already-answered questions per domain per band
        Map<String, Map<String, Long>> answeredByDomainBand = new HashMap<>();
        if (!answeredIds.isEmpty()) {
            List<SatQuestion> answeredQuestions = satQuestionRepository.findAllById(answeredIds);
            for (SatQuestion q : answeredQuestions) {
                String band = difficultyToBand(q.getDifficulty());
                answeredByDomainBand
                    .computeIfAbsent(q.getDomain(), k -> new HashMap<>())
                    .merge(band, 1L, Long::sum);
            }
        }

        // Build list of slots that still have remaining quota
        record Slot(String domain, int minDiff, int maxDiff) {}
        List<Slot> remaining = new ArrayList<>();

        for (Map.Entry<String, Map<String, Integer>> domainEntry : bandCounts.entrySet()) {
            String domain = domainEntry.getKey();
            Map<String, Integer> bands = domainEntry.getValue();
            for (Map.Entry<String, Integer> bandEntry : bands.entrySet()) {
                String band  = bandEntry.getKey();
                int quota    = bandEntry.getValue();
                if (quota <= 0) continue;
                long answered = answeredByDomainBand
                    .getOrDefault(domain, Map.of())
                    .getOrDefault(band, 0L);
                if (answered < quota) {
                    int[] range = BAND_RANGE.getOrDefault(band, new int[]{1, 3});
                    remaining.add(new Slot(domain, range[0], range[1]));
                }
            }
        }

        Collections.shuffle(remaining);

        for (Slot slot : remaining) {
            Optional<SatQuestion> q = answeredIds.isEmpty()
                ? satQuestionRepository.findNextByDomainDiffNoExclusions(
                    session.getSection(), slot.domain(), slot.minDiff(), slot.maxDiff())
                : satQuestionRepository.findNextByDomainDiff(
                    session.getSection(), slot.domain(), answeredIds, slot.minDiff(), slot.maxDiff());
            if (q.isPresent()) return q.map(QuestionResponse::from);
            log.debug("no question found for slot domain={} band={} (diff={}-{})",
                    slot.domain(), difficultyToBand((short) slot.minDiff()), slot.minDiff(), slot.maxDiff());
        }

        return Optional.empty();
    }

    private String difficultyToBand(short difficulty) {
        if (difficulty <= 1) return "easy";
        if (difficulty == 2) return "medium";
        return "hard";
    }

    @Transactional
    public AnswerFeedback submitAnswer(UUID sessionId, SubmitAnswerRequest req) {
        sessionRepository.findById(sessionId)
                .orElseThrow(() -> new ResourceNotFoundException("Session", sessionId));

        if (req.studentAnswer() == null || req.studentAnswer().isBlank()) {
            throw new InvalidRequestException("studentAnswer must not be blank");
        }

        sessionAnswerRepository.findBySessionIdAndQuestionId(sessionId, req.questionId())
                .ifPresent(a -> {
                    throw new DuplicateAnswerException(sessionId, req.questionId());
                });

        SatQuestion satQ = satQuestionRepository.findById(req.questionId())
                .orElseThrow(() -> new ResourceNotFoundException("Question", req.questionId()));

        boolean isCorrect = satQ.getCorrectAnswer() != null &&
                satQ.getCorrectAnswer().equalsIgnoreCase(req.studentAnswer().trim());

        SessionAnswer sessionAnswer = SessionAnswer.builder()
                .sessionId(sessionId)
                .questionId(req.questionId())
                .studentAnswer(req.studentAnswer())
                .isCorrect(isCorrect)
                .timeSpentSeconds(req.timeSpentSeconds())
                .build();
        sessionAnswerRepository.save(sessionAnswer);
        log.info("answer recorded session={} question={} answer={} correct={} timeSecs={}",
                sessionId, req.questionId(),
                req.studentAnswer() != null
                        ? req.studentAnswer().substring(0, Math.min(10, req.studentAnswer().length()))
                        : "null",
                isCorrect, req.timeSpentSeconds());

        return new AnswerFeedback(
                req.questionId(),
                isCorrect,
                satQ.getCorrectAnswer(),
                satQ.getExplanationShort(),
                satQ.getRawExplanationSteps()
        );
    }

    /**
     * Verifies the session exists and belongs to the given user.
     * Throws 404 if the session doesn't exist (avoids leaking session existence to wrong users).
     * Throws 403 if the session belongs to a different user.
     */
    @Transactional(readOnly = true)
    public void requireOwnership(UUID sessionId, UUID userId) {
        Session session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new ResourceNotFoundException("Session", sessionId));
        if (!userId.equals(session.getUserId())) {
            log.warn("ownership violation session={} requestedBy={} owner={}",
                    sessionId, userId, session.getUserId());
            throw new org.springframework.web.server.ResponseStatusException(
                    org.springframework.http.HttpStatus.FORBIDDEN,
                    "Access denied to session " + sessionId);
        }
    }

    @Transactional(readOnly = true)
    public SessionResponse getSessionStatus(UUID sessionId) {
        Session session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new ResourceNotFoundException("Session", sessionId));

        List<SessionAnswer> answers = sessionAnswerRepository.findBySessionId(sessionId);
        long correct = answers.stream()
                .filter(a -> Boolean.TRUE.equals(a.getIsCorrect()))
                .count();

        int total = computeTotal(session.getDomainBandCounts());
        return new SessionResponse(
                session.getId(),
                session.getSessionType(),
                session.getSection(),
                session.getStatus(),
                session.getStartedAt(),
                answers.size(),
                (int) correct,
                total
        );
    }

    @Transactional(readOnly = true)
    public List<SessionResponse> listSessionsForUser(UUID userId) {
        return sessionRepository.findByUserIdOrderByStartedAtDesc(userId)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    private SessionResponse toResponse(Session session) {
        List<SessionAnswer> answers = sessionAnswerRepository.findBySessionId(session.getId());
        long correct = answers.stream()
                .filter(a -> Boolean.TRUE.equals(a.getIsCorrect()))
                .count();
        int total = computeTotal(session.getDomainBandCounts());
        return new SessionResponse(
                session.getId(),
                session.getSessionType(),
                session.getSection(),
                session.getStatus(),
                session.getStartedAt(),
                answers.size(),
                (int) correct,
                total
        );
    }

    @Transactional(readOnly = true)
    public List<com.satengine.dto.SessionAnswerDetail> getSessionAnswers(UUID sessionId) {
        List<SessionAnswer> answers = sessionAnswerRepository.findBySessionId(sessionId);
        if (answers.isEmpty()) return List.of();

        List<UUID> questionIds = answers.stream().map(SessionAnswer::getQuestionId).toList();

        Map<UUID, SatQuestion> questionMap = satQuestionRepository.findAllById(questionIds)
                .stream().collect(Collectors.toMap(SatQuestion::getId, q -> q));

        return answers.stream().map(sa -> {
            SatQuestion q = questionMap.get(sa.getQuestionId());
            return new com.satengine.dto.SessionAnswerDetail(
                    sa.getQuestionId(),
                    q != null ? q.getQuestionStem() : null,
                    q != null ? q.getDomain() : null,
                    q != null ? q.getSkillKey() : null,
                    q != null ? q.getDifficulty() : null,
                    q != null ? q.getQuestionType() : null,
                    q != null ? q.getOptionA() : null,
                    q != null ? q.getOptionB() : null,
                    q != null ? q.getOptionC() : null,
                    q != null ? q.getOptionD() : null,
                    q != null ? q.getCorrectAnswer() : null,
                    sa.getStudentAnswer(),
                    sa.getIsCorrect(),
                    sa.getTimeSpentSeconds(),
                    q != null ? q.getExplanationShort() : null,
                    q != null ? q.getRawExplanationSteps() : null,
                    q != null ? q.getCoreConcept() : null,
                    null,                               // choiceExplanations — not in sat_questions
                    q != null ? q.getAlternativeApproach() : null,
                    null,                               // animationJson — not in sat_questions
                    q != null ? q.getRawDiagram() : null,
                    null,                               // passageText — math only
                    null,                               // passageSource — math only
                    q != null ? q.getSkillKey() : null
            );
        }).toList();
    }

    private int computeTotal(String domainBandCountsJson) {
        if (domainBandCountsJson == null) return 0;
        try {
            Map<String, Map<String, Integer>> map = objectMapper.readValue(
                    domainBandCountsJson, new TypeReference<>() {});
            return map.values().stream()
                    .flatMap(bands -> bands.values().stream())
                    .mapToInt(Integer::intValue).sum();
        } catch (Exception e) {
            log.warn("Failed to parse domainBandCountsJson for total computation: {}", e.getMessage());
            return 0;
        }
    }
}
