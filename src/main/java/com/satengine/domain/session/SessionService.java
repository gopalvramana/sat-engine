package com.satengine.domain.session;

import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.dto.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class SessionService {

    private final SessionRepository sessionRepository;
    private final SessionAnswerRepository sessionAnswerRepository;
    private final QuestionRepository questionRepository;
    private final QuestionAnswerRepository questionAnswerRepository;

    @Transactional
    public Session createSession(CreateSessionRequest req) {
        Session session = Session.builder()
                .sessionType(req.sessionType())
                .section(req.section())
                .status("active")
                .build();
        return sessionRepository.save(session);
    }

    @Transactional(readOnly = true)
    public Optional<QuestionResponse> getNextQuestion(UUID sessionId) {
        List<UUID> answeredIds = sessionAnswerRepository.findAnsweredQuestionIds(sessionId);

        Session session = sessionRepository.findById(sessionId)
                .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));

        Optional<Question> next = answeredIds.isEmpty()
                ? questionRepository.findNextQuestionNoExclusions("practice", session.getSection())
                : questionRepository.findNextQuestion("practice", session.getSection(), answeredIds);

        return next.map(QuestionResponse::from);
    }

    @Transactional
    public AnswerFeedback submitAnswer(UUID sessionId, SubmitAnswerRequest req) {
        // Guard: session must exist
        sessionRepository.findById(sessionId)
                .orElseThrow(() -> new RuntimeException("Session not found: " + sessionId));

        // Guard: cannot answer the same question twice in a session
        sessionAnswerRepository.findBySessionIdAndQuestionId(sessionId, req.questionId())
                .ifPresent(a -> {
                    throw new RuntimeException("Already answered question " + req.questionId() + " in this session");
                });

        // Retrieve correct answer (server-side only, never sent to client before submission)
        QuestionAnswer answer = questionAnswerRepository.findByQuestionId(req.questionId())
                .orElseThrow(() -> new RuntimeException("Answer not found for question: " + req.questionId()));

        boolean isCorrect = answer.getCorrectAnswer()
                .equalsIgnoreCase(req.studentAnswer().trim());

        // Persist the student's answer
        SessionAnswer sessionAnswer = SessionAnswer.builder()
                .sessionId(sessionId)
                .questionId(req.questionId())
                .studentAnswer(req.studentAnswer())
                .isCorrect(isCorrect)
                .timeSpentSeconds(req.timeSpentSeconds())
                .build();
        sessionAnswerRepository.save(sessionAnswer);

        // Retrieve question for explanation fields
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
