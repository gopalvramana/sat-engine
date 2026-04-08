-- Add domain_counts JSONB column to sessions for quota-based practice sets
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS domain_counts jsonb;
