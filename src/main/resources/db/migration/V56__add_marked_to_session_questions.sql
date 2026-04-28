-- session_questions was created manually in production before the marked column
-- was added to V54.  V54's CREATE TABLE IF NOT EXISTS skipped recreation,
-- leaving the column absent and causing Hibernate schema-validation to fail.
-- ADD COLUMN IF NOT EXISTS is idempotent: safe on DBs that already have it.
ALTER TABLE session_questions
    ADD COLUMN IF NOT EXISTS marked BOOLEAN NOT NULL DEFAULT FALSE;
