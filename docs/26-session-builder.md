# Session Builder — Full Plan

**Status:** APPROVED, NOT YET IMPLEMENTED  
**Trigger:** "implement session builder"

---

## Goal

Replace the two-table question store (`sympy_questions` + `sympy_question_answers`) with a
single clean table (`sat_questions`) that has `template` and `variant` as first-class
indexed columns, all question content in one `content` JSONB column, and serves student
sessions directly — with built-in variant diversity.

**Student experience target:** complete 5–6 sessions before the same `(template, variant)`
pair repeats in a given skill.

---

## New schema — `sat_questions`

```sql
CREATE TABLE sat_questions (
  id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  external_id    VARCHAR(20)  UNIQUE NOT NULL,
  skill_key      VARCHAR(60)  NOT NULL,
  template       VARCHAR(60)  NOT NULL,       -- first-class indexed column
  variant        VARCHAR(60),                 -- first-class indexed column
  difficulty     SMALLINT     NOT NULL,
  question_type  VARCHAR(5)   NOT NULL,       -- 'mcq' or 'spr'
  section        VARCHAR(20)  NOT NULL,
  domain         VARCHAR(50)  NOT NULL,
  pool           VARCHAR(20)  NOT NULL DEFAULT 'drill',
  status         VARCHAR(30)  NOT NULL DEFAULT 'generated',
  correct_answer TEXT,                        -- flat for fast answer-checking
  param_hash     VARCHAR(64),
  scenario_tag   VARCHAR(60),
  review_notes   TEXT,
  generated_at   TIMESTAMPTZ,
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

  -- All question content + raw math object in one JSONB column
  content        JSONB        NOT NULL
);
```

`content` JSONB shape:
```json
{
  "questionStem":        "text with LaTeX",
  "optionA":             "...",
  "optionB":             "...",
  "optionC":             "...",
  "optionD":             "...",
  "correctLetter":       "D",
  "sprMin":              null,
  "sprMax":              null,
  "explanationShort":    "...",
  "explanationSteps":    [...],
  "coreConcept":         "...",
  "distractorRationale": {...},
  "prerequisites":       [...],
  "alternativeApproach": "...",
  "diagram":             {...},
  "mathObject":          {...}
}
```

### Indexes

```sql
-- Session diversity query (skill + template + variant)
CREATE INDEX idx_sq_skill_tpl_var
  ON sat_questions (skill_key, template, variant)
  WHERE status = 'approved';

-- Session selection by domain + difficulty
CREATE INDEX idx_sq_domain_diff
  ON sat_questions (status, domain, difficulty);

-- Duplicate detection
CREATE UNIQUE INDEX idx_sq_param_hash
  ON sat_questions (skill_key, param_hash)
  WHERE param_hash IS NOT NULL;
```

---

## Migration — lossless, old tables untouched until verified

```sql
-- Step 1: Create sat_questions (above DDL)

-- Step 2: Copy all rows — LEFT JOIN handles questions with no answer row
INSERT INTO sat_questions (
  id, external_id, skill_key, template, variant,
  difficulty, question_type, section, domain, pool, status,
  correct_answer, param_hash, scenario_tag, review_notes,
  generated_at, created_at, content
)
SELECT
  sq.id,
  sq.external_id,
  sq.skill_key,
  COALESCE(sq.math_object -> 'params' ->> 'tpl', 'unknown') AS template,
  sq.math_object -> 'params' ->> 'variant'                  AS variant,
  sq.difficulty,
  sq.question_type,
  sq.section,
  sq.domain,
  sq.pool,
  sq.status,
  sqa.correct_answer,
  sq.param_hash,
  sq.scenario_tag,
  sq.review_notes,
  sq.generated_at,
  sq.created_at,
  jsonb_build_object(
    'questionStem',        sq.question_stem,
    'optionA',             sq.option_a,
    'optionB',             sq.option_b,
    'optionC',             sq.option_c,
    'optionD',             sq.option_d,
    'correctLetter',       sqa.correct_letter,
    'sprMin',              sq.spr_min,
    'sprMax',              sq.spr_max,
    'explanationShort',    sq.explanation_short,
    'explanationSteps',    sq.explanation_steps,
    'coreConcept',         sq.core_concept,
    'distractorRationale', sq.distractor_rationale,
    'prerequisites',       sq.prerequisites,
    'alternativeApproach', sq.alternative_approach,
    'diagram',             sq.diagram,
    'mathObject',          sq.math_object
  ) AS content
FROM sympy_questions sq
LEFT JOIN sympy_question_answers sqa ON sqa.question_id = sq.id;

-- Step 3: Verify — counts MUST match before dropping anything
SELECT COUNT(*) FROM sympy_questions;   -- source
SELECT COUNT(*) FROM sat_questions;     -- target — must equal source

-- Step 4: Smoke-check a few rows
SELECT id, template, variant, correct_answer,
       content ->> 'questionStem',
       content -> 'mathObject' ->> 'skill'
FROM sat_questions LIMIT 5;

-- Step 5: Only after app is verified working end-to-end:
DROP TABLE sympy_question_answers;
DROP TABLE sympy_questions;
```

`session_answers.question_id` is a plain UUID with no FK — existing rows resolve against
the same UUIDs now in `sat_questions`. No change to `session_answers`.

---

## Java changes (8 files)

### 1. `SatQuestion.java` (new entity)

```java
@Entity @Table(name = "sat_questions")
public class SatQuestion {
    @Id UUID id;
    String externalId;
    String skillKey;
    String template;      // first-class column
    String variant;       // first-class column
    Short  difficulty;
    String questionType;
    String section;
    String domain;
    String pool;
    String status;
    String correctAnswer; // flat — used by submitAnswer()
    String paramHash;
    String scenarioTag;
    String reviewNotes;
    OffsetDateTime generatedAt;
    OffsetDateTime createdAt;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    String content;       // all question content + mathObject
}
```

### 2. `SatQuestionRepository.java` (new repository)

```java
// ── Session selection ──────────────────────────────────────────────────────

@Query(value = """
    SELECT * FROM sat_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SatQuestion> findNextNoExclusions(@Param("section") String section);

@Query(value = """
    SELECT * FROM sat_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    AND id NOT IN (:excludeIds)
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SatQuestion> findNext(
    @Param("section") String section,
    @Param("excludeIds") List<UUID> excludeIds);

@Query(value = """
    SELECT * FROM sat_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    AND domain = :domain
    AND difficulty BETWEEN :minDiff AND :maxDiff
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SatQuestion> findNextByDomainDiffNoExclusions(
    @Param("section") String section, @Param("domain") String domain,
    @Param("minDiff") int minDiff,    @Param("maxDiff") int maxDiff);

@Query(value = """
    SELECT * FROM sat_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    AND domain = :domain
    AND difficulty BETWEEN :minDiff AND :maxDiff
    AND id NOT IN (:excludeIds)
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SatQuestion> findNextByDomainDiff(
    @Param("section") String section, @Param("domain") String domain,
    @Param("excludeIds") List<UUID> excludeIds,
    @Param("minDiff") int minDiff,    @Param("maxDiff") int maxDiff);

// ── Diversity-aware selection ──────────────────────────────────────────────
// Excludes (template, variant) pairs seen in the student's last N sessions.
// Falls back gracefully when no diverse question exists (new student, small pool).

@Query(value = """
    SELECT * FROM sat_questions sq
    WHERE sq.status = 'approved'
    AND (:section IS NULL OR sq.section = :section)
    AND sq.id NOT IN (:excludeIds)
    AND (sq.template IS NULL OR sq.variant IS NULL
         OR (sq.template, sq.variant) NOT IN (
           SELECT sq2.template, sq2.variant
           FROM session_answers sa
           JOIN sessions       s   ON sa.session_id  = s.id
           JOIN sat_questions  sq2 ON sa.question_id = sq2.id
           WHERE s.user_id = :userId
             AND sq2.template IS NOT NULL
             AND sq2.variant  IS NOT NULL
           ORDER BY s.created_at DESC
           LIMIT :recentSessions
         ))
    ORDER BY RANDOM() LIMIT 1
    """, nativeQuery = true)
Optional<SatQuestion> findNextDiverse(
    @Param("section") String section,
    @Param("excludeIds") List<UUID> excludeIds,
    @Param("userId") UUID userId,
    @Param("recentSessions") int recentSessions);

// ── Admin / stats ──────────────────────────────────────────────────────────

@Query(value = """
    SELECT domain,
      SUM(CASE WHEN difficulty IN (1,2) THEN 1 ELSE 0 END) AS easy,
      SUM(CASE WHEN difficulty = 3      THEN 1 ELSE 0 END) AS medium,
      SUM(CASE WHEN difficulty IN (4,5) THEN 1 ELSE 0 END) AS hard,
      COUNT(*) AS total
    FROM sat_questions
    WHERE status = 'approved'
    AND (:section IS NULL OR section = :section)
    GROUP BY domain
    """, nativeQuery = true)
List<Object[]> countByDomainAndDifficulty(@Param("section") String section);

boolean existsBySkillKeyAndParamHash(String skillKey, String paramHash);

@Query(value = """
    SELECT param_hash FROM sat_questions
    WHERE skill_key = :skillKey AND param_hash IS NOT NULL
    AND status != 'rejected'
    """, nativeQuery = true)
List<String> findParamHashesBySkillKey(@Param("skillKey") String skillKey);

@Query(value = """
    SELECT COALESCE(MAX(CAST(SUBSTRING(external_id FROM :prefixLen) AS INTEGER)), 0)
    FROM sat_questions WHERE external_id LIKE :prefix
    """, nativeQuery = true)
int findMaxSeqForPrefix(@Param("prefix") String prefix, @Param("prefixLen") int prefixLen);
```

### 3. `QuestionResponse.java`

Add `from(SatQuestion sq)` static factory — reads `content` JSONB fields via Jackson.

### 4. `SessionService.java`

Replace all `SymPyQuestionRepository` calls with `SatQuestionRepository`.
Use `findNextDiverse()` with `recentSessions = 5` as the primary picker;
fall back to `findNext()` when diverse query returns empty.

### 5. `SessionAnswerRepository.java`

```sql
-- Before: JOIN sympy_questions q ON sa.question_id = q.id
-- After:  JOIN sat_questions   q ON sa.question_id = q.id
```

### 6. `QuestionService.java`

`getQuestion(UUID id)` and `getCountsByDomain()` → use `SatQuestionRepository`.

### 7. `SymPyGenerateStage.java`

Write new questions to `sat_questions` instead of `sympy_questions`.
Build `SatQuestion` entity: `template` and `variant` from `mo.params()`,
all narration fields + `mathObject` packed into `content` JSONB.

### 8. `SymPyAdminController.java` + `SymPyQuestionResponse.java`

Point admin review page reads to `sat_questions`.
Map `content` JSONB fields to `SymPyQuestionResponse` (replaces individual column reads).

---

## Difficulty band mapping

| Band | sat_questions difficulty values |
|---|---|
| Easy | 1, 2 |
| Medium | 3 |
| Hard | 4, 5 (empty until d4+ templates added) |

---

## What stays unchanged

- `session_answers` table — untouched; UUIDs resolve against `sat_questions` identically
- `sessions` table — untouched
- All frontend DTOs and API endpoint URLs — identical JSON shape
- `questions` / `question_answers` (old non-sympy tables) — untouched, not dropped
