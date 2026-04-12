package com.satengine.domain.session;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

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

        return new DashboardResponse(
                sessionsCompleted, questionsAnswered, accuracyPct, avgTimeSeconds, recentSessions);
    }

    // ── Session creation ───────────────────────────────────────────────────

    @Transactional
    public Session createSession(UUID userId, CreateSessionRequest req) {
        String bandCountsJson = null;
        if (req.domainBandCounts() != null && !req.domainBandCounts().isEmpty()) {
            try {
                bandCountsJson = objectMapper.writeValueAsString(req.domainBandCounts());
            } catch (Exception e) { /* ignore */ }
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

    @Transactional(readOnly = true)
    public Optional<QuestionResponse> getNextQuestion(UUID sessionId) {
        Session session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));

        List<UUID> answeredIds = sessionAnswerRepository.findAnsweredQuestionIds(sessionId);

        if (session.getDomainBandCounts() != null) {
            return getNextQuestionByBandQuota(session, answeredIds);
        }

        // Fallback: random
        Optional<Question> next = answeredIds.isEmpty()
                ? questionRepository.findNextQuestionNoExclusions("practice", session.getSection())
                : questionRepository.findNextQuestion("practice", session.getSection(), answeredIds);
        return next.map(QuestionResponse::from);
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
                .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));

        sessionAnswerRepository.findBySessionIdAndQuestionId(sessionId, req.questionId())
                .ifPresent(a -> {
                    throw new RuntimeException("Already answered question " + req.questionId() + " in this session");
                });

        QuestionAnswer answer = questionAnswerRepository.findByQuestionId(req.questionId())
                .orElseThrow(() -> new RuntimeException("Answer not found for question: " + req.questionId()));

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

        Question question = questionRepository.findById(req.questionId())
                .orElseThrow(() -> new RuntimeException("Question not found: " + req.questionId()));

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
                .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));

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
        } catch (Exception e) { return 0; }
    }
}
