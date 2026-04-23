ALTER TABLE sympy_questions
    ADD COLUMN IF NOT EXISTS prerequisites       JSONB,
    ADD COLUMN IF NOT EXISTS alternative_approach TEXT;
