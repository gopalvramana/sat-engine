-- V18: Fix MATH-ALG-005 SPR range.
-- sprMin and sprMax were both 0, but the correct answer is -12.
-- An SPR range must contain the correct answer.
UPDATE questions
SET spr_min = -12,
    spr_max = -12
WHERE external_id = 'MATH-ALG-005';
