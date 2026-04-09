ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS min_difficulty integer NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS max_difficulty integer NOT NULL DEFAULT 7;
