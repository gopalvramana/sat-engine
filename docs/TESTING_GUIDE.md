# Testing Guide

Everything you need to run, read, and write tests for SatEngine.

---

## 1. Quick Start

```bash
# Run all tests (spins up a real PostgreSQL container automatically)
mvn test

# Run only the fast unit tests (no Docker/DB needed)
mvn test -Dtest=SessionServiceUnitTest

# Run only the integration tests
mvn test -Dtest=IntegrationTest

# Run a single test method
mvn test -Dtest="IntegrationTest#createSession_happyPath"
```

Expect:
- Unit tests → **< 1 second** (no Spring, no DB)
- Integration tests → **15–25 seconds** (first run pulls Docker image; subsequent runs reuse it)

---

## 2. Test Architecture

```
src/test/
├── java/com/satengine/
│   ├── IntegrationTest.java          ← REST-level tests against real PostgreSQL
│   ├── TestDataHelper.java           ← JDBC fixture helper (insert/delete test rows)
│   └── session/
│       └── SessionServiceUnitTest.java  ← Pure unit tests, all deps mocked
└── resources/
    └── application-test.yml          ← Test Spring config (overrides datasource, disables pipeline)
```

### Two layers — use the right one

| Layer | Class | When to write here |
|---|---|---|
| **Unit** | `SessionServiceUnitTest` | Business logic, edge cases, exception types — no DB needed |
| **Integration** | `IntegrationTest` | HTTP contract (status codes, response shape, headers) — hits real DB |

---

## 3. How Integration Tests Work

`IntegrationTest` uses **Testcontainers** to boot a real PostgreSQL container once for the whole test run. Spring Boot auto-configures the datasource to point at it. Flyway runs all migrations automatically, so the schema is always current.

```
┌───────────────────┐     HTTP     ┌───────────────────────────┐     JDBC     ┌──────────────────┐
│ TestRestTemplate  │ ──────────→  │ Spring Boot (random port) │ ──────────→  │ PostgreSQL       │
│ (in-process)      │ ←──────────  │ Controllers + Services     │ ←──────────  │ (Docker via TC)  │
└───────────────────┘              └───────────────────────────┘              └──────────────────┘
```

**Test isolation:** each `@Nested` class has an `@AfterEach` that calls `data.deleteAllTestData()`. This clears `session_answers`, `sessions`, `question_answers`, `questions` — so every test starts with a clean DB.

**TestDataHelper** inserts minimal rows directly via JDBC (bypasses the API so tests don't depend on the create-question pipeline). Two helper methods:

```java
UUID qId = data.insertMcqQuestion("EXT-ID", "math", "algebra", 2, "B");
UUID qId = data.insertSprQuestion("EXT-ID", "math", "algebra", 3, "4");
```

---

## 4. How Unit Tests Work

`SessionServiceUnitTest` uses **Mockito** — no Spring context, no database. All four repositories are `@Mock`. The service is instantiated directly in `@BeforeEach`.

```java
@BeforeEach
void setUp() {
    service = new SessionService(
            sessionRepository, sessionAnswerRepository,
            questionRepository, questionAnswerRepository,
            new ObjectMapper());
}
```

Tests use `when(...).thenReturn(...)` to control what the mocked repos return, then assert on what the service produces or throws.

---

## 5. Test Coverage Map

### Session API (IntegrationTest — 31 tests)

| Test | What it verifies |
|---|---|
| `createSession_happyPath` | 201, body has id + status=active |
| `createSession_missingSessionType` | 400 with "sessionType" in error |
| `createSession_blankSessionType` | 400 |
| `createSession_noSection_allowed` | 201 (section is optional) |
| `createSession_domainBandCounts_total` | totalQuestions = sum of all band counts |
| `getSession_returnsStatus` | 200, correct id and questionsAnswered=0 |
| `getSession_notFound` | 404 |
| `getSession_malformedUuid_returns400` | 400 with param name in error |
| `nextQuestion_returnsQuestion` | 200 when pool has questions |
| `nextQuestion_noCorrectAnswerExposed` | correctAnswer key absent from response |
| `nextQuestion_emptyPool_204` | 204 when no questions in DB |
| `nextQuestion_exhaustedPool_204` | 204 after all questions answered |
| `nextQuestion_sessionNotFound` | 404 |
| `nextQuestion_sectionFilter` | 204 when only wrong-section questions exist |
| `submitAnswer_correctMcq` | isCorrect=true, correctAnswer=B |
| `submitAnswer_wrongMcq` | isCorrect=false, correctAnswer revealed |
| `submitAnswer_caseInsensitive` | "b" matches "B" |
| `submitAnswer_trimmed` | "  B  " matches "B" |
| `submitAnswer_duplicate_409` | 409 with "already answered" |
| `submitAnswer_sessionNotFound` | 404 |
| `submitAnswer_questionNotFound` | 404 |
| `submitAnswer_missingQuestionId` | 400 with "questionId" in error |
| `submitAnswer_blankAnswer` | 400 |
| `submitAnswer_sprCorrect` | SPR correct answer |
| `submitAnswer_sprWrong` | SPR wrong answer, correct revealed |
| `submitAnswer_invalidMcqChoice_acceptedAsWrong` | **Bug probe**: "X" treated as wrong, no 400 |
| `submitAnswer_elevenCharAnswer_returns400` | 400 on @Size(max=10) violation |
| `submitAnswer_crossSession_notBlocked` | **Bug probe**: no ownership validation |
| `sessionStatus_counts` | questionsAnswered=2, correctCount=1 after 2 answers |
| `bandQuota_correctDomain` | quota session returns question from correct domain |
| `bandQuota_quotaExceedsPool_204` | 204 when pool smaller than quota |

### Question API (IntegrationTest — 13 tests)

| Test | What it verifies |
|---|---|
| `listQuestions_noCorrectAnswer` | correctAnswer absent from list response |
| `getQuestion_noCorrectAnswer` | correctAnswer absent from single-question response |
| `listQuestions_all` | returns both inserted questions |
| `listQuestions_sectionFilter` | section=math returns only math questions |
| `listQuestions_emptyDb` | 200 + empty list (not 404) |
| `listQuestions_requiredFields` | all expected keys present in response |
| `getQuestion_byId` | 200 with correct id and externalId |
| `getQuestion_notFound` | 404 |
| `getQuestion_malformedUuid_returns400` | 400 with param name |
| `questionCount_breakdown` | byDomain.algebra.easy=2, medium=1 |
| `questionCount_emptyDb` | total=0 |
| `questionCount_sectionFilter` | cross-section questions excluded |
| `questionCount_hardBand` | difficulty 6-7 counted in "hard" |

### SessionService Unit (SessionServiceUnitTest — 26 tests across 4 @Nested groups)

| Group | Tests |
|---|---|
| `createSession` | saves correct fields, serialises bandCounts, null=null, stores userId |
| `getSessionStatus` | null bandCounts→0, multi-domain sum, malformed JSON→0, answer counts, not-found→ResourceNotFoundException |
| `getNextQuestion` | not-found→ResourceNotFoundException |
| `submitAnswer` | session not found, blank answer, null answer, duplicate, correct, wrong, case-insensitive, trimmed, answer record missing |
| `difficultyToBand` | all 7 difficulty values (parameterised) |

---

## 6. Bug Probes — Tests That Document Known Issues

Two tests are written as **intentional documentation of current bugs**, not regressions. They are named with the word "probe" in their display name and contain inline comments explaining the known deficiency.

### `submitAnswer_invalidMcqChoice_acceptedAsWrong`
No validation that MCQ studentAnswer must be one of A/B/C/D. Sending "X" returns `isCorrect=false` with HTTP 200. The test asserts on the current broken behaviour so any future fix (adding MCQ format validation) will be caught.

### `submitAnswer_crossSession_notBlocked`
No ownership check: any user can submit an answer to any session ID they don't own. Currently returns 200. Tracked as GitHub issue #5. Test asserts on current behaviour as a reminder.

---

## 7. Reading a Test Failure

When a test fails, Maven prints:
```
[ERROR] IntegrationTest.submitAnswer_blankAnswer -- Time elapsed: 0.12 s <<< FAILURE!
org.opentest4j.AssertionFailedError:
expected: 400 BAD_REQUEST
 but was: 200 OK
```

Steps to diagnose:
1. Run that single test: `mvn test -Dtest="IntegrationTest#submitAnswer_blankAnswer"`
2. Add `-Dlogging.level.com.satengine=DEBUG` to see full server logs during the test run
3. If it's an integration test, check which HTTP call returned the unexpected status — look at the assertion line number in the stack trace
4. If the test was a **bug probe** (see Section 6), the production code was just fixed — update the assertion to match the new correct behaviour

---

## 8. Writing a New Test

### Rule 1 — choose the right layer

- **Does it test a business rule** (e.g., "trimmed before comparison", "sum of band counts")? → Unit test in `SessionServiceUnitTest`
- **Does it test an HTTP contract** (status code, response key, header)? → Integration test in `IntegrationTest`
- **Does it test a new service?** → Create a new `*UnitTest.java` in `src/test/java/com/satengine/<domain>/`

### Rule 2 — follow the naming convention

```
methodUnderTest_scenario_expectedResult
```

Examples:
```
createSession_nullBandCounts_storesNull
submitAnswer_blankAnswer_throws
nextQuestion_sectionFilter_excludesOtherSection
```

### Rule 3 — each test asserts one thing

One behaviour per test method. Multiple `assertThat` lines are fine when they all describe the same outcome (e.g., checking both `isCorrect` and `correctAnswer` after a submit).

### Writing a unit test

```java
@Test
@DisplayName("brief human-readable description")
void methodName_scenario_expectedResult() {
    // Arrange — set up mocks
    var sessionId = UUID.randomUUID();
    mockSession(sessionId, null);              // helper from bottom of test class
    when(questionAnswerRepository.findByQuestionId(any())).thenReturn(Optional.empty());

    // Act + Assert
    assertThatThrownBy(() -> service.submitAnswer(sessionId,
            new SubmitAnswerRequest(UUID.randomUUID(), "A", null)))
            .isInstanceOf(ResourceNotFoundException.class)
            .hasMessageContaining("not found");
}
```

### Writing an integration test

```java
@Test
@DisplayName("brief description")
void methodName_scenario() {
    // Arrange — insert fixture data
    UUID qId = data.insertMcqQuestion("MY-TEST-001", "math", "algebra", 2, "B");
    String sessionId = createSession("math");   // shared helper at bottom of IntegrationTest

    // Act
    var r = rest.postForEntity("/api/sessions/" + sessionId + "/answers",
            Map.of("questionId", qId.toString(), "studentAnswer", "B"), Map.class);

    // Assert
    assertThat(r.getStatusCode()).isEqualTo(HttpStatus.OK);
    assertThat(r.getBody().get("isCorrect")).isEqualTo(true);
}
```

**Important:** use a unique `externalId` for every `insertMcqQuestion` call (e.g. `"MY-TEST-001"`). The column has a unique constraint — duplicate external IDs across tests will cause 500 errors even with `@AfterEach` cleanup, because Flyway seeds data with fixed IDs.

### Asserting exceptions in integration tests

The API returns `{ "error": "message" }` on failure. Assert like this:

```java
assertThat(r.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
assertThat(r.getBody().get("error").toString()).contains("not found");
```

---

## 9. What Is Not Tested (and Why)

| Area | Why not tested yet |
|---|---|
| `GapAnalysisService` | Calls Claude API — needs a mock HTTP server (WireMock). Worth adding when the gap feature stabilises. |
| `DashboardController` | Needs auth session setup in tests (HTTP session with userId). Add when auth is hardened (issue #5). |
| `AdminQuestionService` | Low student-facing risk; admin-only endpoints. |
| Authentication (OAuth2) | Requires Google token — integration tested manually. |
| Pipeline stages | Internal tooling; not student-facing. |

---

## 10. CI / Future

The test suite is ready to drop into any CI pipeline as-is:

```yaml
# GitHub Actions example
- name: Run tests
  run: mvn test --no-transfer-progress
```

Docker is required on the CI host for Testcontainers to spin up PostgreSQL. GitHub Actions runners include Docker by default.

When you add tests, keep this invariant: **`mvn test` must pass before every commit**.
