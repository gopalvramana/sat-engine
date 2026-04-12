-- Fix #44: Mark sessions with ≥1 answer as 'completed' where they are stuck as 'active'.
-- Sessions that were started but abandoned with 0 answers remain 'active' and will
-- be filtered out of the dashboard recent sessions list at query time.

UPDATE sessions
SET
    status       = 'completed',
    completed_at = COALESCE(completed_at, started_at)
WHERE
    status = 'active'
    AND id IN (
        SELECT DISTINCT session_id FROM session_answers
    );
