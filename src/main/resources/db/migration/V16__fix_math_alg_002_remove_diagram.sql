-- V16: Remove unnecessary diagram from MATH-ALG-002.
-- Agent review flagged it as extraneous — "solve x²-5x+6=0" is a purely
-- algebraic question. A coordinate plane diagram adds clutter without value.
UPDATE questions
SET diagram = NULL
WHERE external_id = 'MATH-ALG-002';
