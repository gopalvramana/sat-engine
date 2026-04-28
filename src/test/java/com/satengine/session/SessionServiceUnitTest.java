package com.satengine.session;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.session.*;
import com.satengine.domain.sympy.SatQuestion;
import com.satengine.domain.sympy.SatQuestionRepository;
import com.satengine.dto.CreateSessionRequest;
import com.satengine.dto.SessionResponse;
import com.satengine.dto.SubmitAnswerRequest;
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
 * All dependencies are mocked — no database or Spring context required.
 */
@ExtendWith(MockitoExtension.class)
class SessionServiceUnitTest {

    @Mock private SessionRepository         sessionRepository;
    @Mock private SessionAnswerRepository   sessionAnswerRepository;
    @Mock private SessionQuestionRepository sessionQuestionRepository;
    @Mock private SatQuestionRepository     satQuestionRepository;

    private SessionService service;

    private static final UUID TEST_USER = UUID.randomUUID();

    @BeforeEach
    void setUp() {
        service = new SessionService(
                sessionRepository,
                sessionAnswerRepository,
                sessionQuestionRepository,
                satQuestionRepository,
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
            var req = new CreateSessionRequest("practice", "math", null, null, null);
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
            var req = new CreateSessionRequest("practice", "math", bands, null, null);

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
            var req = new CreateSessionRequest("practice", "math", null, null, null);
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
            var req = new CreateSessionRequest("practice", "math", null, null, null);
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
        @DisplayName("correct answer → isCorrect=true, correctAnswer returned")
        void correctAnswer_returnsTrue() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(any(), any()))
                    .thenReturn(Optional.empty());
            mockSatQuestion(questionId, "B");

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
            mockSatQuestion(questionId, "B");

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
            mockSatQuestion(questionId, "B");

            var fb = service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "b", null));

            assertThat(fb.isCorrect()).isTrue();
        }

        @Test
        @DisplayName("re-submission upserts existing answer (SAT free-navigation)")
        void resubmit_updatesExistingAnswer() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            var existing = SessionAnswer.builder()
                    .sessionId(sessionId).questionId(questionId)
                    .studentAnswer("A").isCorrect(false).build();
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(sessionId, questionId))
                    .thenReturn(Optional.of(existing));
            mockSatQuestion(questionId, "B");

            // Change answer from A to B
            var fb = service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "B", null));

            assertThat(fb.isCorrect()).isTrue();
            verify(sessionAnswerRepository).save(existing); // same object, updated
        }

        @Test
        @DisplayName("question not found → ResourceNotFoundException")
        void questionNotFound_throws() {
            var sessionId  = UUID.randomUUID();
            var questionId = UUID.randomUUID();
            mockSession(sessionId, null);
            when(sessionAnswerRepository.findBySessionIdAndQuestionId(any(), any()))
                    .thenReturn(Optional.empty());
            when(satQuestionRepository.findById(questionId)).thenReturn(Optional.empty());

            assertThatThrownBy(() -> service.submitAnswer(sessionId,
                    new SubmitAnswerRequest(questionId, "A", null)))
                    .isInstanceOf(ResourceNotFoundException.class)
                    .hasMessageContaining("not found");
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  difficultyToBand — d1=easy, d2=medium, d3=hard
    // ═══════════════════════════════════════════════════════════════

    @ParameterizedTest(name = "difficulty {0} → band \"{1}\"")
    @CsvSource({
            "1, easy",
            "2, medium",
            "3, hard"
    })
    @DisplayName("difficultyToBand — maps each difficulty value to correct band")
    void difficultyToBand_allValues(short difficulty, String expectedBand) {
        var exposed = new ExposedSessionService(
                sessionRepository, sessionAnswerRepository,
                sessionQuestionRepository, satQuestionRepository,
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

    private void mockSatQuestion(UUID questionId, String correctAnswer) {
        var q = new SatQuestion();
        q.setId(questionId);
        q.setCorrectAnswer(correctAnswer);
        when(satQuestionRepository.findById(questionId)).thenReturn(Optional.of(q));
    }

    private SessionAnswer answer(boolean correct) {
        var a = new SessionAnswer();
        a.setIsCorrect(correct);
        return a;
    }

    static class ExposedSessionService extends SessionService {
        ExposedSessionService(SessionRepository sr, SessionAnswerRepository sar,
                              SessionQuestionRepository sqr, SatQuestionRepository satQr,
                              ObjectMapper om) {
            super(sr, sar, sqr, satQr, om);
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
