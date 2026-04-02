-- V21: Add scenario_tag to track real-world scenario used per question.
-- Used during generation to inject "already used scenarios" context so
-- Claude doesn't generate duplicate setups (e.g. two projectile motion questions).

ALTER TABLE questions ADD COLUMN IF NOT EXISTS scenario_tag VARCHAR(60);

CREATE INDEX IF NOT EXISTS idx_questions_scenario_tag ON questions(scenario_tag);
