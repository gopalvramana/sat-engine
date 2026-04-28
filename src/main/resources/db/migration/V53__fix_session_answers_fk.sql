-- V53: Fix session_answers.question_id FK to reference sat_questions instead of questions.
--
-- Background: V50 created sat_questions (merged sympy_questions + enrichment data).
-- Sessions now serve sat_questions IDs, but the FK still pointed to the legacy
-- questions table, causing a 23503 constraint violation on every answer submission.

-- 1. Drop the old FK constraint
ALTER TABLE session_answers
    DROP CONSTRAINT IF EXISTS session_answers_question_id_fkey;

-- 2. Remove orphaned rows that reference legacy questions (not in sat_questions)
DELETE FROM session_answers
WHERE question_id NOT IN (SELECT id FROM sat_questions);

-- 3. Add new FK pointing to sat_questions
ALTER TABLE session_answers
    ADD CONSTRAINT session_answers_question_id_fkey
    FOREIGN KEY (question_id) REFERENCES sat_questions(id);
