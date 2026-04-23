# Plan 25 — Serve Questions Directly from `sympy_questions`

## Decision
Discard all questions from the old AI pipeline (`questions` / `question_answers` tables).
Use only SymPy-generated questions (`sympy_questions` / `sympy_question_answers`) for all
session delivery, answer checking, and review flows going forward.

## Why
- Old pipeline questions were never cleanly promoted into the production table.
- SymPy pipeline produces higher-quality, verified math questions.
- Removes the promote-to-production-table complexity entirely.

## What Does NOT Change
- `questions` / `question_answers` tables — left in place, not dropped (safe)
- `QuestionRepository` — kept as-is (admin pipeline still uses it)
- All frontend DTOs and API endpoint URLs — same JSON shape, no frontend changes needed
- `SymPyPromoteService` — kept for optional future use
- `SymPyAdminController` — untouched

## No DB Migrations Needed
`session_answers.question_id` is a plain UUID column with no FK constraint, so it can
already store sympy question UUIDs.

---

## Implementation: 6 Files

### File 1 — `SymPyQuestionRepository.java`
Add 5 new native query methods (mirror `QuestionRepository` session-selection queries,
but against `sympy_questions`, filtered on `status = 'approved'` only — no pool constraint):

```java
// Random approved question, with exclusions
@Query(value = """
    SELECT * FROM sympy_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    AND id NOT IN (:excludeIds)
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SymPyQuestion> findNextQuestion(
    @Param("section") String section,
    @Param("excludeIds") List<UUID> excludeIds);

// Random approved question, no exclusions (first question of a session)
@Query(value = """
    SELECT * FROM sympy_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SymPyQuestion> findNextQuestionNoExclusions(@Param("section") String section);

// Domain + difficulty band, with exclusions
@Query(value = """
    SELECT * FROM sympy_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    AND domain = :domain
    AND difficulty BETWEEN :minDiff AND :maxDiff
    AND id NOT IN (:excludeIds)
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SymPyQuestion> findNextQuestionByDomainAndDifficulty(
    @Param("section") String section,
    @Param("domain") String domain,
    @Param("excludeIds") List<UUID> excludeIds,
    @Param("minDiff") int minDiff,
    @Param("maxDiff") int maxDiff);

// Domain + difficulty band, no exclusions
@Query(value = """
    SELECT * FROM sympy_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    AND domain = :domain
    AND difficulty BETWEEN :minDiff AND :maxDiff
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SymPyQuestion> findNextQuestionByDomainAndDifficultyNoExclusions(
    @Param("section") String section,
    @Param("domain") String domain,
    @Param("minDiff") int minDiff,
    @Param("maxDiff") int maxDiff);

// Session builder counts: [domain, easy_count, medium_count, hard_count, total]
// easy=1-2, medium=3-5, hard=6-7 (sympy max is 3, so hard will be 0 until d4+ are added)
@Query(value = """
    SELECT domain,
      SUM(CASE WHEN difficulty BETWEEN 1 AND 2 THEN 1 ELSE 0 END) AS easy,
      SUM(CASE WHEN difficulty BETWEEN 3 AND 5 THEN 1 ELSE 0 END) AS medium,
      SUM(CASE WHEN difficulty BETWEEN 6 AND 7 THEN 1 ELSE 0 END) AS hard,
      COUNT(*) AS total
    FROM sympy_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    GROUP BY domain
    """, nativeQuery = true)
List<Object[]> countByDomainAndDifficultyForSection(@Param("section") String section);
```

---

### File 2 — `SymPyQuestionAnswerRepository.java`
Add batch fetch method:

```java
@Query(value = "SELECT * FROM sympy_question_answers WHERE question_id IN (:ids)",
       nativeQuery = true)
List<SymPyQuestionAnswer> findAllByQuestionIds(@Param("ids") List<UUID> ids);
```

---

### File 3 — `QuestionResponse.java`
Add a `from(SymPyQuestion sq)` static factory and two static helper methods.

Key field mappings:
| QuestionResponse field   | SymPyQuestion source                          |
|--------------------------|-----------------------------------------------|
| `coreConceptJson`        | `wrapCoreConcept(sq.getCoreConcept())`        |
| `alternativeApproach`    | `wrapAltApproach(sq.getAlternativeApproach())`|
| `prerequisitesJson`      | `sq.getPrerequisites()` (already JSONB)       |
| `diagramJson`            | `sq.getDiagram()` (already JSONB)             |
| `explanationSteps`       | `sq.getExplanationSteps()` (already JSONB)    |
| `choiceExplanations`     | `null` (not in sympy)                         |
| `animationJson`          | `null` (not in sympy)                         |
| `trapCategory`           | `null` (not in sympy)                         |
| `trapExplanation`        | `null` (not in sympy)                         |
| `passageText`            | `null` (not in sympy)                         |
| `passageSource`          | `null` (not in sympy)                         |

Helper methods (same logic as `SymPyPromoteService`):
```java
// Wraps plain TEXT coreConcept → {"title":"...","summary":null,"keyFormula":null}
public static String wrapCoreConcept(String text) { ... }

// Wraps plain TEXT alternativeApproach → {"title":"Alternative Method","steps":[{...}]}
public static String wrapAltApproach(String text) { ... }
```

---

### File 4 — `SessionService.java`
Inject `SymPyQuestionRepository sympyQuestionRepository` and
`SymPyQuestionAnswerRepository sympyAnswerRepository`.

Swap 4 method bodies:

**`getNextQuestion()` fallback path (lines ~172–175):**
```java
// Before — questionRepository.findNextQuestionNoExclusions("practice", section)
// After:
sympyQuestionRepository.findNextQuestionNoExclusions(session.getSection())
sympyQuestionRepository.findNextQuestion(session.getSection(), answeredIds)
// .map(QuestionResponse::from)  →  .map(sq -> QuestionResponse.from(sq))
```

**`getNextQuestionByBandQuota()` (lines ~207–245):**
```java
// Before — questionRepository.findAllById(answeredIds) returns List<Question>
// After:
List<SymPyQuestion> answeredQuestions = sympyQuestionRepository.findAllById(answeredIds);
// for loop type: for (SymPyQuestion q : answeredQuestions)
// slot queries: sympyQuestionRepository.findNextQuestionByDomainAndDifficulty*(...)
// .map(QuestionResponse::from) → .map(sq -> QuestionResponse.from(sq))
```

**`submitAnswer()` (lines ~273–303):**
```java
// Before — questionAnswerRepository.findByQuestionId + questionRepository.findById
// After:
SymPyQuestionAnswer answer = sympyAnswerRepository.findByQuestionId(req.questionId())...
SymPyQuestion question = sympyQuestionRepository.findById(req.questionId())...
// answer.getCorrectAnswer() and question.getExplanationShort/Steps — same field names, no change
```

**`getSessionAnswers()` (lines ~380–418):**
```java
// Before — questionRepository.findAllById + questionAnswerRepository.findAllByQuestionIds
// After:
Map<UUID, SymPyQuestion> questionMap = sympyQuestionRepository.findAllById(questionIds)...
Map<UUID, String> correctAnswerMap = sympyAnswerRepository.findAllByQuestionIds(questionIds)...
// In SessionAnswerDetail construction:
//   coreConceptJson   → QuestionResponse.wrapCoreConcept(q.getCoreConcept())
//   alternativeApproach → QuestionResponse.wrapAltApproach(q.getAlternativeApproach())
//   choiceExplanations, animationJson, passageText, passageSource → null
//   diagramJson → q.getDiagram()
//   all other fields map directly (same names)
```

---

### File 5 — `SessionAnswerRepository.java`
Fix `getDomainAccuracyForUser` native SQL query:

```sql
-- Before:
JOIN questions q ON sa.question_id = q.id
-- After:
JOIN sympy_questions q ON sa.question_id = q.id
```

---

### File 6 — `QuestionService.java`
Inject `SymPyQuestionRepository sympyQuestionRepository` (alongside existing `QuestionRepository`).

```java
// getQuestion(UUID id) — used by GET /api/questions/{id}
// Before: questionRepository.findById(id) → QuestionResponse.from(Question)
// After:  sympyQuestionRepository.findById(id) → QuestionResponse.from(SymPyQuestion)

// getCountsByDomain(String section) — used by GET /api/questions/count (session builder)
// Before: questionRepository.countByDomainAndDifficulty(section)
// After:  sympyQuestionRepository.countByDomainAndDifficultyForSection(section)
```

---

## Difficulty Band Note
SymPy uses difficulty 1/2/3. Session builder bands map as:
- `easy` (1–2): d1 + d2 sympy questions ✓
- `medium` (3–5): d3 sympy questions ✓
- `hard` (6–7): empty until higher-difficulty templates are added

This is a data gap, not a code bug. Hard band sessions will simply return no questions.
