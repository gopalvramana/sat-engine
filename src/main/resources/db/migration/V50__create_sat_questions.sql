-- ============================================================
-- V50: Create sat_questions — consolidated question store
-- ============================================================
-- Replaces the two-table sympy_questions + sympy_question_answers design.
-- template and variant are first-class indexed columns for diversity queries.
-- All question content + raw math object packed into a single content JSONB.
--
-- Old tables are NOT dropped here. Drop them only after the app is verified
-- end-to-end (counts must match, sessions must serve, answers must submit).
-- ============================================================

CREATE TABLE sat_questions (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id    VARCHAR(20)  UNIQUE NOT NULL,
    skill_key      VARCHAR(60)  NOT NULL,
    template       VARCHAR(60),                        -- first-class indexed column
    variant        VARCHAR(60),                        -- first-class indexed column
    difficulty     SMALLINT     NOT NULL CHECK (difficulty BETWEEN 1 AND 3),
    question_type  VARCHAR(5)   NOT NULL,
    section        VARCHAR(20)  NOT NULL,
    domain         VARCHAR(50)  NOT NULL,
    pool           VARCHAR(20)  NOT NULL DEFAULT 'drill',
    status         VARCHAR(30)  NOT NULL DEFAULT 'generated',
    correct_answer TEXT,                               -- flat for fast answer-checking
    param_hash     VARCHAR(64),
    scenario_tag   VARCHAR(60),
    review_notes   TEXT,
    generated_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- All question content + raw math object in one JSONB column
    content        JSONB        NOT NULL
);

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

-- ── Migrate existing data ──────────────────────────────────────────────────
-- Extract template and variant from math_object->params->tpl / variant.
-- LEFT JOIN handles questions with no answer row (SPR without correct_answer).

INSERT INTO sat_questions (
    id, external_id, skill_key, template, variant,
    difficulty, question_type, section, domain, pool, status,
    correct_answer, param_hash, scenario_tag, review_notes,
    generated_at, created_at, content
)
SELECT
    sq.id,
    sq.external_id,
    COALESCE(sq.skill_key, 'unknown')                               AS skill_key,
    sq.math_object -> 'params' ->> 'tpl'                           AS template,
    sq.math_object -> 'params' ->> 'variant'                       AS variant,
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
        'correctLetter',       sqa.correct_answer,
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
    )                                                               AS content
FROM sympy_questions sq
LEFT JOIN sympy_question_answers sqa ON sqa.question_id = sq.id;

-- ── Verification (run manually after migration) ───────────────────────────
-- SELECT COUNT(*) FROM sympy_questions;   -- source count
-- SELECT COUNT(*) FROM sat_questions;     -- must equal source count
--
-- SELECT id, template, variant, correct_answer,
--        content ->> 'questionStem',
--        content -> 'mathObject' ->> 'skill'
-- FROM sat_questions LIMIT 5;
