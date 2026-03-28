CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE questions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id         VARCHAR(20)  UNIQUE NOT NULL,
    section             VARCHAR(20)  NOT NULL,
    domain              VARCHAR(50)  NOT NULL,
    skill               VARCHAR(100),
    difficulty          SMALLINT     NOT NULL CHECK (difficulty BETWEEN 1 AND 7),
    question_type       VARCHAR(5)   NOT NULL,
    question_stem       TEXT         NOT NULL,
    option_a            TEXT,
    option_b            TEXT,
    option_c            TEXT,
    option_d            TEXT,
    spr_min             NUMERIC,
    spr_max             NUMERIC,
    explanation_short   TEXT,
    explanation_steps   JSONB,
    trap_category       VARCHAR(30),
    trap_explanation    TEXT,
    core_concept        JSONB,
    prerequisites       JSONB,
    animation           JSONB,
    pool                VARCHAR(10)  NOT NULL DEFAULT 'both',
    passage_text        TEXT,
    passage_source      TEXT,
    diagram             JSONB,
    calculator_ok       BOOLEAN      DEFAULT TRUE,
    source              VARCHAR(20)  DEFAULT 'ai_generated',
    reviewed            BOOLEAN      DEFAULT FALSE,
    review_notes        TEXT,
    generated_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ  DEFAULT NOW(),
    embedding           vector(1536)
);

CREATE TABLE question_answers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    correct_answer  VARCHAR(10) NOT NULL,
    UNIQUE (question_id)
);

CREATE TABLE question_reviews (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id     UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    pass            BOOLEAN      NOT NULL,
    confidence      NUMERIC(3,2),
    solved_answer   VARCHAR(10),
    issues          JSONB,
    notes           TEXT,
    model           VARCHAR(50),
    checked_at      TIMESTAMPTZ,
    UNIQUE (question_id)
);

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    session_type    VARCHAR(10)  NOT NULL,
    section         VARCHAR(20),
    status          VARCHAR(15)  DEFAULT 'active',
    started_at      TIMESTAMPTZ  DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    score           JSONB
);

CREATE TABLE session_questions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id     UUID NOT NULL REFERENCES questions(id),
    position        SMALLINT     NOT NULL,
    UNIQUE (session_id, position)
);

CREATE TABLE session_answers (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id          UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id         UUID NOT NULL REFERENCES questions(id),
    student_answer      VARCHAR(10),
    is_correct          BOOLEAN,
    answered_at         TIMESTAMPTZ    DEFAULT NOW(),
    time_spent_seconds  INTEGER,
    UNIQUE (session_id, question_id)
);

CREATE INDEX idx_questions_section    ON questions(section);
CREATE INDEX idx_questions_domain     ON questions(domain);
CREATE INDEX idx_questions_pool       ON questions(pool);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_reviewed   ON questions(reviewed);
CREATE INDEX idx_questions_embedding  ON questions USING hnsw (embedding vector_cosine_ops);
