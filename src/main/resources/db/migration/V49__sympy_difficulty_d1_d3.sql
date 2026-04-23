-- Migrate sympy_questions difficulty from d1-d5 (invented scale) to d1-d3 (SAT taxonomy).
--
-- SAT has exactly three difficulty levels: Easy (d1) / Medium (d2) / Hard (d3).
-- The original d1-d7 range was internal and does not map to any published SAT standard.
--
-- Remap for existing data (d1-d3 are already valid and unchanged):
--   d4 → d2  (Medium)
--   d5 → d3  (Hard)
--   d6 → d3  (Hard — stubs, should not exist)
--   d7 → d3  (Hard — stubs, should not exist)

BEGIN;

-- Single-pass CASE to avoid intermediate-value conflicts
UPDATE sympy_questions
SET difficulty = CASE
    WHEN difficulty >= 5 THEN 3
    WHEN difficulty = 4  THEN 2
    ELSE difficulty          -- d1, d2, d3 unchanged
END
WHERE difficulty > 3;

-- Replace the old wide-range check with the SAT 3-level constraint
ALTER TABLE sympy_questions
    DROP CONSTRAINT IF EXISTS sympy_questions_difficulty_check;

ALTER TABLE sympy_questions
    ADD CONSTRAINT sympy_questions_difficulty_check
    CHECK (difficulty BETWEEN 1 AND 3);

COMMIT;
