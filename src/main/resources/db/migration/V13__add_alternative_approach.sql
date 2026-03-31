-- V13: Add alternative_approach column for math questions
-- Replaces trap_category / trap_explanation in the UI (those columns are kept for data history)
ALTER TABLE questions ADD COLUMN IF NOT EXISTS alternative_approach JSONB;
