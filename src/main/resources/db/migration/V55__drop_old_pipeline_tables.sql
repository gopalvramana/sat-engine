-- Remove old question pipeline tables.
-- All approved content lives in sat_questions.
-- No session_answers reference these tables (verified: 0 rows affected).
DROP TABLE IF EXISTS question_reviews  CASCADE;
DROP TABLE IF EXISTS question_answers  CASCADE;
DROP TABLE IF EXISTS questions         CASCADE;
