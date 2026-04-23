-- SymPy Pipeline POC: isolated replica tables for A/B comparison
-- No changes to the production 'questions' table.

CREATE TABLE sympy_questions (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id       VARCHAR(20)  UNIQUE NOT NULL,
    section           VARCHAR(20)  NOT NULL,
    domain            VARCHAR(50)  NOT NULL,
    skill             VARCHAR(100),
    skill_key         VARCHAR(60),
    scenario_tag      VARCHAR(60),
    difficulty        SMALLINT     NOT NULL CHECK (difficulty BETWEEN 1 AND 7),
    question_type     VARCHAR(5)   NOT NULL,
    question_stem     TEXT         NOT NULL,
    option_a          TEXT,
    option_b          TEXT,
    option_c          TEXT,
    option_d          TEXT,
    spr_min           NUMERIC(10,4),
    spr_max           NUMERIC(10,4),
    explanation_short TEXT,
    explanation_steps JSONB,
    pool              VARCHAR(10)  NOT NULL DEFAULT 'drill',
    diagram           JSONB,
    calculator_ok     BOOLEAN      DEFAULT TRUE,
    source            VARCHAR(30)  DEFAULT 'sympy_generated',
    status            VARCHAR(20)  NOT NULL DEFAULT 'generated',
    math_object       JSONB        NOT NULL,
    param_hash        VARCHAR(64),
    review_notes      TEXT,
    generated_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_sympy_skill_key   ON sympy_questions(skill_key);
CREATE INDEX idx_sympy_difficulty  ON sympy_questions(difficulty);
CREATE INDEX idx_sympy_status      ON sympy_questions(status);
CREATE INDEX idx_sympy_param_hash  ON sympy_questions(param_hash) WHERE param_hash IS NOT NULL;
CREATE INDEX idx_sympy_scenario    ON sympy_questions(scenario_tag) WHERE scenario_tag IS NOT NULL;

CREATE TABLE sympy_question_answers (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id    UUID NOT NULL REFERENCES sympy_questions(id) ON DELETE CASCADE,
    correct_answer VARCHAR(10) NOT NULL,
    UNIQUE (question_id)
);
