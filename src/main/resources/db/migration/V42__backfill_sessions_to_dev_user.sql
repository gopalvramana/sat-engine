-- Backfill all orphaned sessions (user_id IS NULL) to the dev user.
-- These were created before session ownership was wired up.
-- Safe to run multiple times (WHERE user_id IS NULL is idempotent).
UPDATE sessions
SET user_id = (SELECT id FROM users WHERE email = 'dev@satengine.local' LIMIT 1)
WHERE user_id IS NULL;
