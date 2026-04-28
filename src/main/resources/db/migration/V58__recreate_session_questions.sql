-- The manually-created session_questions table has wrong column types
-- (position = SMALLINT instead of INTEGER).  V57's ALTER failed or was a no-op
-- because of the dependent unique constraint.
--
-- Nuclear fix: drop and recreate with the correct schema.
-- Safe: this table holds transient session state only; no permanent user data.

DROP TABLE IF EXISTS session_questions CASCADE;

CREATE TABLE session_questions (
    id          UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    question_id UUID    NOT NULL REFERENCES sat_questions(id),
    position    INTEGER NOT NULL,
    marked      BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_session_question UNIQUE (session_id, question_id),
    CONSTRAINT uq_session_position UNIQUE (session_id, position)
);

CREATE INDEX idx_session_questions_session ON session_questions (session_id);
