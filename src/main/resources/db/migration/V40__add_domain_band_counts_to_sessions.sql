ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS domain_band_counts jsonb;
