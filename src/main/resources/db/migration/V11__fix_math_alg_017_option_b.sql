-- V11: Fix MATH-ALG-017 option B — decimal 9.67 replaced with whole number 9
-- Correct answer: $290 - $50 flat fee = $240 ÷ $30/hr = 8 hours (option A)
-- Trap for B: student divides $290 ÷ $30 ≈ 9.67 (forgets flat fee), rounds down → 9
-- All four options are now whole numbers: 8, 9, 10, 12

UPDATE questions
SET option_b = '9'
WHERE external_id = 'MATH-ALG-017';
