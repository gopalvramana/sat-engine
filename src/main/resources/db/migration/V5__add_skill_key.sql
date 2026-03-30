-- V5: Add skill_key column — canonical slug from sat_taxonomy.json
-- Separate from the free-form `skill` text already on the table.
-- skill_key values are exact slugs like "linear_eq_one_var", "pythagorean_theorem", etc.
-- Used for coverage reporting and targeted generation.

ALTER TABLE questions ADD COLUMN IF NOT EXISTS skill_key VARCHAR(60);

-- Index for coverage queries: "count approved questions per skill_key"
CREATE INDEX IF NOT EXISTS idx_questions_skill_key ON questions (skill_key)
    WHERE skill_key IS NOT NULL;
