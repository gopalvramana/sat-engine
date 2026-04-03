-- V35: Fix MATH-PS-011 options which were left as '\ext{ cm}' after V34.
--
-- V34 replaced chr(9) (tab) with '\', but this was wrong because the
-- tab character consumed the 't' from '\text'. So '\text' became
-- [TAB]ext in the DB, and after V34 it became '\ext' (not '\text').
--
-- The options are simple numeric values with units — no LaTeX needed.
-- Set them to plain text.

UPDATE questions
SET option_a = '12 cm',
    option_b = '16 cm',
    option_c = '20 cm',
    option_d = '24 cm'
WHERE external_id = 'MATH-PS-011';
