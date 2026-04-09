ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS domain_difficulties jsonb;
