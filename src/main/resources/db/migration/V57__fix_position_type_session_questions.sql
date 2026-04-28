-- session_questions was created manually with position as SMALLINT (int2).
-- Hibernate entity maps position to Integer (int4 / INTEGER).
-- Cast to INTEGER; safe because position values are small and fit in either type.
ALTER TABLE session_questions
    ALTER COLUMN position TYPE INTEGER USING position::INTEGER;
