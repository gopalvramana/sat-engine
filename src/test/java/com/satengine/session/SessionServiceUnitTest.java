package com.satengine.session;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionAnswer;
import com.satengine.domain.question.QuestionAnswerRepository;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.domain.session.Session;
import com.satengine.domain.session.SessionAnswer;
import com.satengine.domain.session.SessionAnswerRepository;
import com.satengine.domain.session.SessionRepository;
import com.satengine.domain.session.SessionService;
import com.satengine.dto.CreateSessionRequest;
import com.satengine.dto.SessionResponse;
import com.satengine.dto.SubmitAnswerRequest;
import com.satengine.exception.DuplicateAnswerException;
import com.satengine.exception.InvalidRequestException;
import com.satengine.exception.ResourceNotFoundException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.*;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Pure unit tests for SessionService business logic.
 *
 * All dependencies are mocked — no database or Spring context required.
 * Runs in milliseconds.
 *
 * Covers:
 *  - createSession: persists correct fields, serialises bandCounts, null bandCounts
 *  - submitAnswer: correct/wrong, case-insensitive, trim, blank guard, duplicate guard,
 *                  session not found, question answer not found, typed exceptions
 *  - getNextQuestion: session not found throws ResourceNotFoundException
 *  - getSessionStatus: correct/answered counts, totalQuestions from JSON,
 *                      malformed JSON falls back to 0, session not found
 *  - difficultyToBand: all 7 boundary values
 */
@ExtendWith(MockitoExtension.class)
class SessionServiceUnitTest {

    @Mock private SessionRepository        sessionRepository;
    @Mock private SessionAnswerRepository  sessionAnswerRepository;
    @Mock private QuestionRepository       questionRepository;
    @Mock private QuestionAnswerRepository questionAnswerRepository;

    private SessionService service;

    // Shared test user ID — passed to every createSession call
    private static final UUID TEST_USER = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        service = new SessionService(
                sessionRepository,
                sessionAnswerRepository,
                questionRepository,
                questionAnswerRepository,
                new ObjectMapper());
    }

    // ═══════════════════════════════════════════════════════════════
    //  createSession
    // ═══════════════════════════════════════════════════════════════

    @Nested
    @DisplayName("createSession")
    class CreateSessionTests {

        @Test
        @DisplayName("persists session with correct sessionType and section")
        void savesCorrectFields() {
            var req = new CreateSessionRequest("practice", "math", null);
            var saved = Session.builder()
                    .id(UUID.randomUUID())
                    .sessionType("practice")
                    .section("math")
                    .status("active")
                    .build();
            when(sessionRepository.save(any())).thenReturn(saved);

            var result = service.createSession(TEST_USER, req);

            assertThat(result.getSessionType()).isEqualTo("practice");
            assertThat(result.getSection()).isEqualTo("math");
            assertThat(result.getStatus()).isEqualTo("active");
            verify(sessionRepository).save(any(Session.class));
        }

        @Test
        @DisplayName("domainBandCounts serialised to JSON and stored on the entity")
        void bandCountsSerialised() {
            var bands = Map.of("algebra", Map.of("easy", 2, "medium", 3));
            var req = new CreateSessionRequest("practice", "math", bands);

            var captor = ArgumentCaptor.forClass(Session.class);
            when(sessionRepository.save(captor.capture()))
                    .thenAnswer(inv -> inv.getArgument(0));

            service.createSession(TEST_USER, req);

            String json = captor.getValue().getDomainBandCounts();
            assertThat(json).isNotNull().contains("algebra").contains("easy");
        }

        @Test
        @DisplayName("null domainBandCounts stores null (not empty JSON string)")
        void nullBandCounts_storesNull() {
            var req = new CreateSessionRequest("practice", "math", null);
            var captor = ArgumentCaptor.forClass(Session.class);
            when(sessionRepository.save(captor.capture()))
                    .thenAnswer(inv -> inv.getArgument(0));

            service.createSession(TEST_USER, req);

            assertThat(captor.getValue().getDomainBandCounts()).isNull();
        }

        @Test
        @DisplayName("stores the userId on the session entity")
        void storesUserId() {
            UUID userId = UUID.randomUUID();
            var req = new CreateSessionRequest("practice", "math", null);
            var captor = ArgumentCaptor.forClass(Session.class);
            when(sessionRepository.save(captor.capture()))
                    .thenAnswer(inv -> inv.getArgument(0));

            service.createSession(userId, req);

            assertThat(captor.getValue().getUserId()).isEqualTo(userId);
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  getSessionStatus
    // ═══════════════════════════════════════════════════════════════

    @Nested
    @DisplayName("getSessionStatus")
    class GetSessionStatusTests {

        @Test
        @DisplayName("totalQuestions=0 when session has no domainBandCounts")
        void noBandCounts_totalIsZero() {
            var sessionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionId(sessionId)).thenReturn(List.of());

            SessionResponse resp = service.getSessionStatus(sessionId);

            assertThat(resp.totalQuestions()).isEqualTo(0);
        }

        @Test
        @DisplayName("totalQuestions sums all band counts across multiple domains")
        void bandCounts_totalSumsCorrectly() throws Exception {
            var sessionId = UUID.randomUUID();
            // algebra: easy=2, medium=3  +  geometry: hard=1  =  total 6
            String bandJson = new ObjectMapper().writeValueAsString(Map.of(
                    "algebra",               Map.of("easy", 2, "medium", 3),
                    "geometry_trigonometry", Map.of("hard", 1)));
            mockSession(sessionId, bandJson);
            when(sessionAnswerRepository.findBySessionId(sessionId)).thenReturn(List.of());

            assertThat(service.getSessionStatus(sessionId).totalQuestions()).isEqualTo(6);
        }

        @Test
        @DisplayName("malformed domainBandCounts JSON falls back to totalQuestions=0 (no exception)")
        void malformedBandJson_totalIsZero() {
            var sessionId = UUID.randomUUID();
            mockSession(sessionId, "{not valid json{{");
            when(sessionAnswerRepository.findBySessionId(sessionId)).thenReturn(List.of());

            // Must not throw — graceful fallback
            assertThat(service.getSessionStatus(sessionId).totalQuestions()).isEqualTo(0);
        }

        @Test
        @DisplayName("questionsAnswered and correctCount derived from answer list")
        void countsDerivedFromAnswers() {
            var sessionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionId(sessionId))
                    .thenReturn(List.of(answer(true), answer(true), answer(false)));

            SessionResponse resp = service.getSessionStatus(sessionId);

            assertThat(resp.questionsAnswered()).isEqualTo(3);
            assertThat(resp.correctCount()).isEqualTo(2);
        }

        @Test
        @DisplayName("session not found → ResourceNotFoundException")
        void sessionNotFound_throws() {
            var missingId = UUID.randomUUID();
            when(sessionRepository.findById(missingId)).thenReturn(Optional.empty());

            assertThatThrownBy(() -> service.getSessionStatus(missingId))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessageContaining("not found");
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  getNextQuestion
    // ═══════════════════════════════════════════════════════════════

    @Nested
    @DisplayName("getNextQuestion")
    class GetNextQuestionTests {

        @Test
        @DisplayName("session not found → ResourceNotFoundException")
        void sessionNotFound_throws() {
            var missingId = UUID.randomUUID();
            when(sessionRepository.findById(missingId)).thenReturn(Optional.empty());

            assertThatThrownBy(() -> service.getNextQuestion(missingId))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessageContaining("not found");
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  submitAnswer
    // ═══════════════════════════════════════════════════════════════

    @Nested
    @DisplayName("submitAnswer")
    class SubmitAnswerTests {

        @Test
        @DisplayName("session not found → ResourceNotFoundException")
        void sessionNotFound_throws() {
            var missingId = UUID.randomUUID();
            when(sessionRepository.findById(missingId)).thenReturn(Optional.empty());

            assertThatThrownBy(() -> service.submitAnswer(missingId,
                    new SubmitAnswerRequest(UUID.randomUUID(), "A", null)))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessageContaining("not found");
        }

        @Test
        @DisplayName("blank studentAnswer → InvalidRequestException")
        void blankAnswer_throws() {
            var sessionId = UUID.randomUUID();
            mockSession(sessionId, null);

            assertThatThrownBy(() -> service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(UUID.randomUUID(), "   ", null)))
                    .isInstanceOf(InvalidRequestException.class)
                    .hasMessageContaining("studentAnswer");
        }

        @Test
        @DisplayName("null studentAnswer → InvalidRequestException")
        void nullAnswer_throws() {
            var sessionId = UUID.randomUUID();
            mockSession(sessionId, null);

            assertThatThrownBy(() -> service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(UUID.randomUUID(), null, null)))
                    .isInstanceOf(InvalidRequestException.class);
        }

        @Test
        @DisplayName("already answered → DuplicateAnswerException")
        void alreadyAnswered_throws() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(sessionId, questionId))
                    .thenReturn(Optional.of(new SessionAnswer()));

            assertThatThrownBy(() -> service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "A", null)))
                    .isInstanceOf(DuplicateAnswerException.class)
                    .hasMessageContainingAll("already answered");
        }

        @Test
        @DisplayName("correct answer → isCorrect=true, correctAnswer returned")
        void correctAnswer_returnsTrue() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(any(), any()))
                    .thenReturn(Optional.empty());
            mockAnswer(questionId, "B");
            mockQuestion(questionId);

            var fb = service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "B", null));

            assertThat(fb.isCorrect()).isTrue();
            assertThat(fb.correctAnswer()).isEqualTo("B");
        }

        @Test
        @DisplayName("wrong answer → isCorrect=false, correctAnswer revealed")
        void wrongAnswer_returnsFalse() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(any(), any()))
                    .thenReturn(Optional.empty());
            mockAnswer(questionId, "B");
            mockQuestion(questionId);

            var fb = service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "A", null));

            assertThat(fb.isCorrect()).isFalse();
            assertThat(fb.correctAnswer()).isEqualTo("B");
        }

        @Test
        @DisplayName("answer comparison is case-insensitive")
        void caseInsensitiveComparison() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(any(), any()))
                    .thenReturn(Optional.empty());
            mockAnswer(questionId, "B");
            mockQuestion(questionId);

            var fb = service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "b", null));

            assertThat(fb.isCorrect()).isTrue();
        }

        @Test
        @DisplayName("answer is trimmed before comparison — '  B  ' matches 'B'")
        void answerTrimmed() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(any(), any()))
                    .thenReturn(Optional.empty());
            mockAnswer(questionId, "B");
            mockQuestion(questionId);

            var fb = service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "  B  ", null));

            assertThat(fb.isCorrect()).isTrue();
        }

        @Test
        @DisplayName("answer record not found in DB → ResourceNotFoundException")
        void answerRecordMissing_throws() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(any(), any()))
                    .thenReturn(Optional.empty());
            when(questionAnswerRepository.findByQuestionId(questionId))
                    .thenReturn(Optional.empty());

            assertThatThrownBy(() -> service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "A", null)))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessageContaining("not found");
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  difficultyToBand — all 7 boundary values
    // ═══════════════════════════════════════════════════════════════

    @ParameterizedTest(name = "difficulty {0} → band \"{1}\"")
    @CsvSource({
            "1, easy",
            "2, easy",
            "3, medium",
            "4, medium",
            "5, medium",
            "6, hard",
            "7, hard"
    })
    @DisplayName("difficultyToBand — maps each difficulty value to correct band")
    void difficultyToBand_allValues(short difficulty, String expectedBand) {
        var exposed = new ExposedSessionService(
                sessionRepository, sessionAnswerRepository,
                questionRepository, questionAnswerRepository,
                new ObjectMapper());

        assertThat(exposed.exposeDifficultyToBand(difficulty)).isEqualTo(expectedBand);
    }

    // ═══════════════════════════════════════════════════════════════
    //  HELPERS
    // ═══════════════════════════════════════════════════════════════

    private void mockSession(UUID sessionId, String bandCountsJson) {
        var session = Session.builder()
                .id(sessionId)
                .sessionType("practice")
                .section("math")
                .status("active")
                .domainBandCounts(bandCountsJson)
                .build();
        when(sessionRepository.findById(sessionId)).thenReturn(Optional.of(session));
    }

    private void mockAnswer(UUID questionId, String correctAnswer) {
        var qa = new QuestionAnswer();
        qa.setCorrectAnswer(correctAnswer);
        when(questionAnswerRepository.findByQuestionId(questionId)).thenReturn(Optional.of(qa));
    }

    private void mockQuestion(UUID questionId) {
        var q = new Question();
        q.setId(questionId);
        when(questionRepository.findById(questionId)).thenReturn(Optional.of(q));
    }

    private SessionAnswer answer(boolean correct) {
        var a = new SessionAnswer();
        a.setIsCorrect(correct);
        return a;
    }

    /**
     * Thin subclass that exposes the private difficultyToBand method for boundary testing.
     */
    static class ExposedSessionService extends SessionService {
        ExposedSessionService(SessionRepository sr, SessionAnswerRepository sar,
                              QuestionRepository qr, QuestionAnswerRepository qar,
                              ObjectMapper om) {
            super(sr, sar, qr, qar, om);
        }

        String exposeDifficultyToBand(short d) {
            try {
                var m = SessionService.class.getDeclaredMethod("difficultyToBand", short.class);
                m.setAccessible(true);
                return (String) m.invoke(this, d);
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
    }
}
