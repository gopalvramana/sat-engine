package com.satengine;

import com.satengine.TestDataHelper;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.http.*;
import org.springframework.test.context.ActiveProfiles;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.*;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * All REST API integration tests in one class.
 *
 * ONE @SpringBootTest context + ONE PostgreSQL container (static = class-scoped).
 * Using @Nested groups to keep session and question tests logically separate.
 *
 * Each test method cleans its own data via @AfterEach → full isolation
 * without the cross-class container lifecycle problem.
 */
@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class IntegrationTest {

    @Container
    @ServiceConnection
    static final PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("pgvector/pgvector:pg16")
                    .withDatabaseName("satengine_test")
                    .withUsername("test_user")
                    .withPassword("test_pass");

    @Autowired TestRestTemplate rest;
    @Autowired TestDataHelper data;

    // ══════════════════════════════════════════════════════════════
    //  SESSION API TESTS
    // ══════════════════════════════════════════════════════════════

    @Nested
    @DisplayName("Session API")
    class SessionApiTests {

        @AfterEach void cleanUp() { data.deleteAllTestData(); }

        // ── CREATE SESSION ────────────────────────────────────────

        @Test
        @DisplayName("POST /api/sessions — happy path returns 201 with session id")
        void createSession_happyPath() {
            var r = rest.postForEntity("/api/sessions",
                    Map.of("sessionType", "practice", "section", "math"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(r.getBody()).containsKey("id");
            assertThat(r.getBody().get("status")).isEqualTo("active");
            assertThat(r.getBody().get("questionsAnswered")).isEqualTo(0);
        }

        @Test
        @DisplayName("POST /api/sessions — missing sessionType → 400")
        void createSession_missingSessionType() {
            var r = rest.postForEntity("/api/sessions",
                    Map.of("section", "math"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
            assertThat(r.getBody().get("error").toString()).contains("sessionType");
        }

        @Test
        @DisplayName("POST /api/sessions — blank sessionType → 400")
        void createSession_blankSessionType() {
            var body = new HashMap<String, Object>();
            body.put("sessionType", "   ");
            body.put("section", "math");
            var r = rest.postForEntity("/api/sessions", body, Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        }

        @Test
        @DisplayName("POST /api/sessions — no section allowed (null = any)")
        void createSession_noSection_allowed() {
            var r = rest.postForEntity("/api/sessions",
                    Map.of("sessionType", "practice"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        }

        @Test
        @DisplayName("POST /api/sessions — domainBandCounts sets totalQuestions correctly")
        void createSession_domainBandCounts_total() {
            // easy:2 + medium:3 + hard:1 = 6
            var r = rest.postForEntity("/api/sessions", Map.of(
                    "sessionType", "practice", "section", "math",
                    "domainBandCounts", Map.of("algebra", Map.of("easy", 2, "medium", 3, "hard", 1))
            ), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            assertThat(r.getBody().get("totalQuestions")).isEqualTo(6);
        }

        // ── GET SESSION ───────────────────────────────────────────

        @Test
        @DisplayName("GET /api/sessions/{id} — returns status")
        void getSession_returnsStatus() {
            String id = createSession("math");
            var r = rest.getForEntity("/api/sessions/" + id, Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody().get("id")).isEqualTo(id);
            assertThat(r.getBody().get("questionsAnswered")).isEqualTo(0);
        }

        @Test
        @DisplayName("GET /api/sessions/{id} — nonexistent → 404")
        void getSession_notFound() {
            var r = rest.getForEntity("/api/sessions/" + UUID.randomUUID(), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        }

        @Test
        @DisplayName("GET /api/sessions/malformed-uuid — malformed UUID → 400")
        void getSession_malformedUuid_returns400() {
            var r = rest.getForEntity("/api/sessions/not-a-uuid", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
            assertThat(r.getBody().get("error").toString()).contains("id");
        }

        // ── NEXT QUESTION ─────────────────────────────────────────

        @Test
        @DisplayName("GET /api/sessions/{id}/next — returns question when pool has questions")
        void nextQuestion_returnsQuestion() {
            data.insertMcqQuestion("IT-MCQ-001", "math", "algebra", 2, "B");
            String id = createSession("math");
            var r = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody().get("questionStem")).isNotNull();
        }

        @Test
        @DisplayName("GET /api/sessions/{id}/next — correct answer NOT in response")
        void nextQuestion_noCorrectAnswerExposed() {
            data.insertMcqQuestion("IT-MCQ-002", "math", "algebra", 2, "B");
            String id = createSession("math");
            var r = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody()).doesNotContainKey("correctAnswer");
            @SuppressWarnings("unchecked")
            boolean leaks = ((Set<Object>) r.getBody().keySet()).stream()
                    .map(k -> k.toString().toLowerCase())
                    .anyMatch(k -> k.contains("correct") && k.contains("answer"));
            assertThat(leaks).isFalse();
        }

        @Test
        @DisplayName("GET /api/sessions/{id}/next — empty pool → 204")
        void nextQuestion_emptyPool_204() {
            String id = createSession("math");
            var r = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        }

        @Test
        @DisplayName("GET /api/sessions/{id}/next — all answered → 204")
        void nextQuestion_exhaustedPool_204() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-003", "math", "algebra", 2, "B");
            String id = createSession("math");
            submitAnswer(id, qId, "B");
            var r = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        }

        @Test
        @DisplayName("GET /api/sessions/{id}/next — nonexistent session → 404")
        void nextQuestion_sessionNotFound() {
            var r = rest.getForEntity("/api/sessions/" + UUID.randomUUID() + "/next", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        }

        @Test
        @DisplayName("GET /api/sessions/{id}/next — section filter excludes wrong section")
        void nextQuestion_sectionFilter() {
            data.insertMcqQuestion("IT-MCQ-004", "reading_writing", "craft_structure", 2, "A");
            String id = createSession("math");
            var r = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        }

        // ── SUBMIT ANSWER ─────────────────────────────────────────

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — correct MCQ answer")
        void submitAnswer_correctMcq() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-010", "math", "algebra", 2, "B");
            var fb = submitAnswer(createSession("math"), qId, "B");
            assertThat(fb.get("isCorrect")).isEqualTo(true);
            assertThat(fb.get("correctAnswer")).isEqualTo("B");
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — wrong MCQ answer reveals correct")
        void submitAnswer_wrongMcq() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-011", "math", "algebra", 2, "B");
            var fb = submitAnswer(createSession("math"), qId, "A");
            assertThat(fb.get("isCorrect")).isEqualTo(false);
            assertThat(fb.get("correctAnswer")).isEqualTo("B");
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — comparison is case-insensitive")
        void submitAnswer_caseInsensitive() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-012", "math", "algebra", 2, "B");
            var fb = submitAnswer(createSession("math"), qId, "b");
            assertThat(fb.get("isCorrect")).isEqualTo(true);
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — answer is trimmed before comparison")
        void submitAnswer_trimmed() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-013", "math", "algebra", 2, "B");
            var fb = submitAnswer(createSession("math"), qId, "  B  ");
            assertThat(fb.get("isCorrect")).isEqualTo(true);
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — duplicate submission → 409")
        void submitAnswer_duplicate_409() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-014", "math", "algebra", 2, "B");
            String id = createSession("math");
            submitAnswer(id, qId, "B");
            var r = rest.postForEntity("/api/sessions/" + id + "/answers",
                    Map.of("questionId", qId.toString(), "studentAnswer", "A"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.CONFLICT);
            assertThat(r.getBody().get("error").toString()).containsIgnoringCase("already answered");
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — nonexistent session → 404")
        void submitAnswer_sessionNotFound() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-015", "math", "algebra", 2, "B");
            var r = rest.postForEntity("/api/sessions/" + UUID.randomUUID() + "/answers",
                    Map.of("questionId", qId.toString(), "studentAnswer", "A"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — nonexistent question → 404")
        void submitAnswer_questionNotFound() {
            String id = createSession("math");
            var r = rest.postForEntity("/api/sessions/" + id + "/answers",
                    Map.of("questionId", UUID.randomUUID().toString(), "studentAnswer", "A"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — missing questionId → 400")
        void submitAnswer_missingQuestionId() {
            String id = createSession("math");
            var r = rest.postForEntity("/api/sessions/" + id + "/answers",
                    Map.of("studentAnswer", "A"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
            assertThat(r.getBody().get("error").toString()).contains("questionId");
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — blank studentAnswer → 400")
        void submitAnswer_blankAnswer() {
            UUID qId = data.insertMcqQuestion("IT-MCQ-016", "math", "algebra", 2, "B");
            var req = new HashMap<String, Object>();
            req.put("questionId", qId.toString());
            req.put("studentAnswer", "   ");
            var r = rest.postForEntity("/api/sessions/" + createSession("math") + "/answers", req, Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — SPR correct answer")
        void submitAnswer_sprCorrect() {
            UUID qId = data.insertSprQuestion("IT-SPR-001", "math", "algebra", 3, "4");
            var fb = submitAnswer(createSession("math"), qId, "4");
            assertThat(fb.get("isCorrect")).isEqualTo(true);
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — SPR wrong answer")
        void submitAnswer_sprWrong() {
            UUID qId = data.insertSprQuestion("IT-SPR-002", "math", "algebra", 3, "4");
            var fb = submitAnswer(createSession("math"), qId, "5");
            assertThat(fb.get("isCorrect")).isEqualTo(false);
            assertThat(fb.get("correctAnswer")).isEqualTo("4");
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — MCQ answer not in A-D accepted as wrong (no format validation)")
        void submitAnswer_invalidMcqChoice_acceptedAsWrong() {
            // BUG PROBE: No validation that MCQ answers must be A/B/C/D.
            // "X" is silently treated as wrong (isCorrect=false).
            UUID qId = data.insertMcqQuestion("IT-MCQ-017", "math", "algebra", 2, "B");
            var fb = submitAnswer(createSession("math"), qId, "X");
            assertThat(fb.get("isCorrect")).isEqualTo(false);   // passes; no 400
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — answer > 10 chars → 400 (validation guard)")
        void submitAnswer_elevenCharAnswer_returns400() {
            // @Size(max=10) on SubmitAnswerRequest.studentAnswer fires before DB is touched.
            UUID qId = data.insertSprQuestion("IT-SPR-003", "math", "algebra", 3, "4");
            var r = rest.postForEntity("/api/sessions/" + createSession("math") + "/answers",
                    Map.of("questionId", qId.toString(), "studentAnswer", "12345.67890"), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
            assertThat(r.getBody().get("error").toString()).containsIgnoringCase("10");
        }

        @Test
        @DisplayName("POST /api/sessions/{id}/answers — answer to question in different session is accepted (no ownership check)")
        void submitAnswer_crossSession_notBlocked() {
            // BUG PROBE: No validation that the question belongs to this session.
            UUID qId = data.insertMcqQuestion("IT-MCQ-018", "math", "algebra", 2, "C");
            String sessionB = createSession("math");
            var fb = submitAnswer(sessionB, qId, "C");
            assertThat(fb.get("isCorrect")).isEqualTo(true);   // no error thrown
        }

        // ── SESSION STATUS COUNTS ─────────────────────────────────

        @Test
        @DisplayName("GET /api/sessions/{id} — questionsAnswered and correctCount track correctly")
        void sessionStatus_counts() {
            UUID q1 = data.insertMcqQuestion("IT-MCQ-020", "math", "algebra", 2, "B");
            UUID q2 = data.insertMcqQuestion("IT-MCQ-021", "math", "algebra", 3, "C");
            String id = createSession("math");
            submitAnswer(id, q1, "B");
            submitAnswer(id, q2, "A");
            var s = rest.getForEntity("/api/sessions/" + id, Map.class).getBody();
            assertThat(s.get("questionsAnswered")).isEqualTo(2);
            assertThat(s.get("correctCount")).isEqualTo(1);
        }

        // ── BAND-QUOTA SESSION ────────────────────────────────────

        @Test
        @DisplayName("Band-quota session — returns questions matching requested domain")
        void bandQuota_correctDomain() {
            data.insertMcqQuestion("IT-BAND-001", "math", "algebra", 1, "A");
            var r = rest.postForEntity("/api/sessions", Map.of(
                    "sessionType", "practice", "section", "math",
                    "domainBandCounts", Map.of("algebra", Map.of("easy", 1))
            ), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.CREATED);
            String id = (String) r.getBody().get("id");
            assertThat(r.getBody().get("totalQuestions")).isEqualTo(1);
            var q = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            assertThat(q.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(q.getBody().get("domain")).isEqualTo("algebra");
        }

        @Test
        @DisplayName("Band-quota session — quota > available questions → 204 when exhausted")
        void bandQuota_quotaExceedsPool_204() {
            data.insertMcqQuestion("IT-BAND-002", "math", "algebra", 1, "A");
            var r = rest.postForEntity("/api/sessions", Map.of(
                    "sessionType", "practice", "section", "math",
                    "domainBandCounts", Map.of("algebra", Map.of("easy", 5))
            ), Map.class);
            String id = (String) r.getBody().get("id");
            var q = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            submitAnswer(id, UUID.fromString((String) q.getBody().get("id")), "A");
            var done = rest.getForEntity("/api/sessions/" + id + "/next", Map.class);
            assertThat(done.getStatusCode()).isEqualTo(HttpStatus.NO_CONTENT);
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  QUESTION API TESTS
    // ══════════════════════════════════════════════════════════════

    @Nested
    @DisplayName("Question API")
    class QuestionApiTests {

        @AfterEach void cleanUp() { data.deleteAllTestData(); }

        // ── ANSWER SECURITY ───────────────────────────────────────

        @Test
        @DisplayName("GET /api/questions — correctAnswer NEVER exposed in list response")
        void listQuestions_noCorrectAnswer() {
            data.insertMcqQuestion("QA-SEC-001", "math", "algebra", 2, "B");
            var r = rest.getForEntity("/api/questions?section=math", List.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            for (Object item : r.getBody()) {
                @SuppressWarnings("unchecked") var q = (Map<String, Object>) item;
                assertThat(q).doesNotContainKey("correctAnswer");
            }
        }

        @Test
        @DisplayName("GET /api/questions/{id} — correctAnswer NEVER in single question response")
        void getQuestion_noCorrectAnswer() {
            UUID qId = data.insertMcqQuestion("QA-SEC-002", "math", "algebra", 2, "D");
            var r = rest.getForEntity("/api/questions/" + qId, Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody()).doesNotContainKey("correctAnswer");
        }

        // ── LIST QUESTIONS ────────────────────────────────────────

        @Test
        @DisplayName("GET /api/questions — returns all approved questions")
        void listQuestions_all() {
            data.insertMcqQuestion("QA-LIST-001", "math",            "algebra",        2, "A");
            data.insertMcqQuestion("QA-LIST-002", "reading_writing", "craft_structure", 3, "B");
            var r = rest.getForEntity("/api/questions", List.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody()).hasSize(2);
        }

        @Test
        @DisplayName("GET /api/questions?section=math — filters by section")
        void listQuestions_sectionFilter() {
            data.insertMcqQuestion("QA-LIST-003", "math",            "algebra",        2, "A");
            data.insertMcqQuestion("QA-LIST-004", "reading_writing", "craft_structure", 3, "B");
            var r = rest.getForEntity("/api/questions?section=math", List.class);
            assertThat(r.getBody()).hasSize(1);
        }

        @Test
        @DisplayName("GET /api/questions — empty DB returns empty list, not 404")
        void listQuestions_emptyDb() {
            var r = rest.getForEntity("/api/questions", List.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody()).isEmpty();
        }

        @Test
        @DisplayName("GET /api/questions — required fields are present in response")
        void listQuestions_requiredFields() {
            data.insertMcqQuestion("QA-FIELDS-001", "math", "algebra", 2, "A");
            var r = rest.getForEntity("/api/questions", List.class);
            @SuppressWarnings("unchecked") var q = (Map<String, Object>) r.getBody().get(0);
            assertThat(q).containsKeys("id", "section", "domain", "difficulty",
                                        "questionType", "questionStem",
                                        "optionA", "optionB", "optionC", "optionD");
        }

        // ── GET /api/questions/{id} ───────────────────────────────

        @Test
        @DisplayName("GET /api/questions/{id} — returns question by ID")
        void getQuestion_byId() {
            UUID qId = data.insertMcqQuestion("QA-SINGLE-001", "math", "algebra", 4, "C");
            var r = rest.getForEntity("/api/questions/" + qId, Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody().get("id")).isEqualTo(qId.toString());
            assertThat(r.getBody().get("externalId")).isEqualTo("QA-SINGLE-001");
        }

        @Test
        @DisplayName("GET /api/questions/{id} — nonexistent → 404")
        void getQuestion_notFound() {
            var r = rest.getForEntity("/api/questions/" + UUID.randomUUID(), Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        }

        @Test
        @DisplayName("GET /api/questions/not-a-uuid — malformed UUID → 400")
        void getQuestion_malformedUuid_returns400() {
            var r = rest.getForEntity("/api/questions/not-a-valid-uuid", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
            assertThat(r.getBody().get("error").toString()).contains("id");
        }

        // ── GET /api/questions/count ──────────────────────────────

        @Test
        @DisplayName("GET /api/questions/count — returns domain breakdown with bands")
        void questionCount_breakdown() {
            data.insertMcqQuestion("QA-CNT-001", "math", "algebra", 1, "A"); // easy
            data.insertMcqQuestion("QA-CNT-002", "math", "algebra", 2, "B"); // easy
            data.insertMcqQuestion("QA-CNT-003", "math", "algebra", 4, "C"); // medium
            var r = rest.getForEntity("/api/questions/count?section=math", Map.class);
            assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
            assertThat(r.getBody().get("total")).isEqualTo(3);
            @SuppressWarnings("unchecked")
            var algebra = (Map<String, Object>)
                    ((Map<String, Object>) r.getBody().get("byDomain")).get("algebra");
            assertThat(algebra.get("easy")).isEqualTo(2);
            assertThat(algebra.get("medium")).isEqualTo(1);
            assertThat(algebra.get("hard")).isEqualTo(0);
        }

        @Test
        @DisplayName("GET /api/questions/count — empty DB returns total=0")
        void questionCount_emptyDb() {
            var r = rest.getForEntity("/api/questions/count", Map.class);
            assertThat(r.getBody().get("total")).isEqualTo(0);
        }

        @Test
        @DisplayName("GET /api/questions/count — section filter excludes other section")
        void questionCount_sectionFilter() {
            data.insertMcqQuestion("QA-CNT-004", "math",            "algebra",        2, "A");
            data.insertMcqQuestion("QA-CNT-005", "reading_writing", "craft_structure", 3, "B");
            var r = rest.getForEntity("/api/questions/count?section=reading_writing", Map.class);
            assertThat(r.getBody().get("total")).isEqualTo(1);
        }

        @Test
        @DisplayName("GET /api/questions/count — hard band (difficulty 6-7) counted correctly")
        void questionCount_hardBand() {
            data.insertMcqQuestion("QA-CNT-006", "math", "algebra", 6, "A");
            data.insertMcqQuestion("QA-CNT-007", "math", "algebra", 7, "B");
            var r = rest.getForEntity("/api/questions/count?section=math", Map.class);
            @SuppressWarnings("unchecked")
            var algebra = (Map<String, Object>)
                    ((Map<String, Object>) r.getBody().get("byDomain")).get("algebra");
            assertThat(algebra.get("hard")).isEqualTo(2);
            assertThat(algebra.get("easy")).isEqualTo(0);
        }
    }

    // ══════════════════════════════════════════════════════════════
    //  SHARED HELPERS
    // ══════════════════════════════════════════════════════════════

    private String createSession(String section) {
        var body = new HashMap<String, Object>();
        body.put("sessionType", "practice");
        if (section != null) body.put("section", section);
        var r = rest.postForEntity("/api/sessions", body, Map.class);
        assertThat(r.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        return (String) r.getBody().get("id");
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> submitAnswer(String sessionId, UUID questionId, String answer) {
        var r = rest.postForEntity("/api/sessions/" + sessionId + "/answers",
                Map.of("questionId", questionId.toString(), "studentAnswer", answer), Map.class);
        return r.getBody();
    }
}
