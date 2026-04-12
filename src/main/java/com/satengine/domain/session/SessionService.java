package com.satengine.domain.session;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
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

    private final SessionRepository sessionRepository;
    private final SessionAnswerRepository sessionAnswerRepository;
    private final QuestionRepository questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;
    private final ObjectMapper objectMapper;

    /** Difficulty band → [min, max] difficulty values */
    private static final Map<String, int[]> BAND_RANGE = Map.of(
        "easy",   new int[]{1, 2},
        "medium", new int[]{3, 5},
        "hard",   new int[]{6, 7}
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

        log.info("dashboard computed userId={} sessions={} questions={} accuracy={} domains={}",
                userId, sessionsCompleted, questionsAnswered, accuracyPct, domainAccuracy.size());
        return new DashboardResponse(
                sessionsCompleted, questionsAnswered, accuracyPct, avgTimeSeconds, recentSessions,
                domainAccuracy);
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
            // Fallback: random
            Optional<Question> next = answeredIds.isEmpty()
                    ? questionRepository.findNextQuestionNoExclusions("practice", session.getSection())
                    : questionRepository.findNextQuestion("practice", session.getSection(), answeredIds);
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
            List<Question> answeredQuestions = questionRepository.findAllById(answeredIds);
            for (Question q : answeredQuestions) {
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
                    int[] range = BAND_RANGE.getOrDefault(band, new int[]{1, 7});
                    remaining.add(new Slot(domain, range[0], range[1]));
                }
            }
        }

        Collections.shuffle(remaining);

        for (Slot slot : remaining) {
            Optional<Question> q = answeredIds.isEmpty()
                ? questionRepository.findNextQuestionByDomainAndDifficultyNoExclusions(
                    "practice", session.getSection(), slot.domain(), slot.minDiff(), slot.maxDiff())
                : questionRepository.findNextQuestionByDomainAndDifficulty(
                    "practice", session.getSection(), slot.domain(), answeredIds, slot.minDiff(), slot.maxDiff());
            if (q.isPresent()) return q.map(QuestionResponse::from);
            log.debug("no question found for slot domain={} band={} (diff={}-{})",
                    slot.domain(), difficultyToBand((short) slot.minDiff()), slot.minDiff(), slot.maxDiff());
        }

        return Optional.empty();
    }

    private String difficultyToBand(short difficulty) {
        if (difficulty <= 2) return "easy";
        if (difficulty <= 5) return "medium";
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

        QuestionAnswer answer = questionAnswerRepository.findByQuestionId(req.questionId())
                .orElseThrow(() -> new ResourceNotFoundException("Answer for question", req.questionId()));

        boolean isCorrect = answer.getCorrectAnswer()
                .equalsIgnoreCase(req.studentAnswer().trim());

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

        Question question = questionRepository.findById(req.questionId())
                .orElseThrow(() -> new ResourceNotFoundException("Question", req.questionId()));

        return new AnswerFeedback(
                req.questionId(),
                isCorrect,
                answer.getCorrectAnswer(),
                question.getExplanationShort(),
                question.getExplanationSteps()
        );
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
