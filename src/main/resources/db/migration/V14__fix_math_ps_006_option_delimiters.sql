-- V14: Wrap bare LaTeX fractions in MATH-PS-006 options with \( \) delimiters.
-- Options were generated without inline-math delimiters, causing raw text display.
UPDATE questions
SET option_a = '\(\frac{2}{5}\)',
    option_b = '\(\frac{3}{5}\)',
    option_c = '\(\frac{48}{80}\)',
    option_d = '\(\frac{48}{200}\)'
WHERE external_id = 'MATH-PS-006';
