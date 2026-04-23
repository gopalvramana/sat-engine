-- All questions generated during pipeline testing are moved to 'reference' pool.
-- New diagnostic/drill/test questions will be generated fresh with explicit pool tags.
UPDATE sympy_questions
SET pool = 'reference'
WHERE pool IS NULL
   OR pool NOT IN ('diagnostic', 'test');
-- ^ This catches 'drill' (old default) and any nulls, leaving diagnostic/test untouched.
