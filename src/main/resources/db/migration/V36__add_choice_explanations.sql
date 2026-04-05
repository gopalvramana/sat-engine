-- Add choice_explanations column to store why each answer choice (A/B/C/D) is correct or incorrect.
-- Stored as jsonb: {"A": "why A", "B": "why B", "C": "why C", "D": "why D"}
-- Nullable — populated via enrichment pass on existing questions, and from generation for new ones.
ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS choice_explanations jsonb;
