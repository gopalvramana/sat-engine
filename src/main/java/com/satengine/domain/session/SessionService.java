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

    @Transactional
    public Session createSession(CreateSessionRequest req) {
        String domainCountsJson = null;
        if (req.domainCounts() != null && !req.domainCounts().isEmpty()) {
            try {
                domainCountsJson = objectMapper.writeValueAsString(req.domainCounts());
            } catch (Exception e) { /* ignore */ }
        }
        String domainDifficultiesJson = null;
        if (req.domainDifficulties() != null && !req.domainDifficulties().isEmpty()) {
            try {
                domainDifficultiesJson = objectMapper.writeValueAsString(req.domainDifficulties());
            } catch (Exception e) { /* ignore */ }
        }
        Session session = Session.builder()
                .sessionType(req.sessionType())
                .section(req.section())
                .domainCounts(domainCountsJson)
                .domainDifficulties(domainDifficultiesJson)
                .status("active")
                .build();
        return sessionRepository.save(session);
    }

    @Transactional(readOnly = true)
    public Optional<QuestionResponse> getNextQuestion(UUID sessionId) {
        Session session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));

        List<UUID> answeredIds = sessionAnswerRepository.findAnsweredQuestionIds(sessionId);

        // ── Domain-quota mode ──────────────────────────────────────────
        if (session.getDomainCounts() != null) {
            return getNextQuestionByQuota(session, answeredIds);
        }

        // ── Random mode (legacy) ───────────────────────────────────────
        Optional<Question> next = answeredIds.isEmpty()
                ? questionRepository.findNextQuestionNoExclusions("practice", session.getSection())
                : questionRepository.findNextQuestion("practice", session.getSection(), answeredIds);

        return next.map(QuestionResponse::from);
    }

    /** Pick the next question respecting per-domain quotas. */
    private Optional<QuestionResponse> getNextQuestionByQuota(Session session, List<UUID> answeredIds) {
        // Parse quota map from JSON
        Map<String, Integer> quotas;
        try {
            quotas = objectMapper.readValue(session.getDomainCounts(),
                    new TypeReference<Map<String, Integer>>() {});
        } catch (Exception e) {
            return Optional.empty();
        }

        // Count already-answered questions per domain
        Map<String, Long> answeredByDomain = new HashMap<>();
        if (!answeredIds.isEmpty()) {
            List<Question> answeredQuestions = questionRepository.findAllById(answeredIds);
            answeredByDomain = answeredQuestions.stream()
                    .collect(Collectors.groupingBy(Question::getDomain, Collectors.counting()));
        }

        // Find domains that still have remaining quota — randomize order for variety
        final Map<String, Long> finalAnswered = answeredByDomain;
        List<String> remainingDomains = quotas.entrySet().stream()
                .filter(e -> e.getValue() > 0
                        && finalAnswered.getOrDefault(e.getKey(), 0L) < e.getValue())
                .map(Map.Entry::getKey)
                .collect(Collectors.toList());

        Collections.shuffle(remainingDomains);

        // Parse per-domain difficulty ranges (optional)
        Map<String, Map<String, Integer>> diffRanges = new HashMap<>();
        if (session.getDomainDifficulties() != null) {
            try {
                diffRanges = objectMapper.readValue(session.getDomainDifficulties(),
                        new TypeReference<Map<String, Map<String, Integer>>>() {});
            } catch (Exception ignored) {}
        }
        final Map<String, Map<String, Integer>> finalDiffRanges = diffRanges;

        // Try each remaining domain until we find a question
        for (String domain : remainingDomains) {
            Map<String, Integer> range = finalDiffRanges.getOrDefault(domain, Map.of("min", 1, "max", 7));
            int minDiff = range.getOrDefault("min", 1);
            int maxDiff = range.getOrDefault("max", 7);
            Optional<Question> q = answeredIds.isEmpty()
                    ? questionRepository.findNextQuestionByDomainAndDifficultyNoExclusions("practice", session.getSection(), domain, minDiff, maxDiff)
                    : questionRepository.findNextQuestionByDomainAndDifficulty("practice", session.getSection(), domain, answeredIds, minDiff, maxDiff);
            if (q.isPresent()) return q.map(QuestionResponse::from);
        }

        return Optional.empty(); // all quotas exhausted or no questions available
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

        return new SessionResponse(
                session.getId(),
                session.getSessionType(),
                session.getSection(),
                session.getStatus(),
                session.getStartedAt(),
                answers.size(),
                (int) correct
        );
    }
}
