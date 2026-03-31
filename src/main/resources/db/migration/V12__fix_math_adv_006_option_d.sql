-- V12: Fix MATH-ADV-006 option D — replace non-realistic distractor
-- Old: x² + 3x + 3 (no common student mistake produces this)
-- New: x² + 4x + 4 = (x+2)² — trap for students who subtract p(x) - q(x)
--      instead of dividing: (x²+5x+6) - (x+2) = x²+4x+4

UPDATE questions
SET option_d = '\( x^{2} + 4x + 4 \)'
WHERE external_id = 'MATH-ADV-006';
