-- V34: Fix corrupted tab characters in question options introduced by a bug in
-- fixLatexEscapes() where \text, \theta, \frac etc. (LaTeX commands starting
-- with \t, \n, \r, \b, \f) were incorrectly treated as JSON escape sequences
-- and stored with a literal tab character instead of a backslash.
--
-- Affected: MATH-PS-011 options had \( 12 \text{ cm} \) stored as
--           \( 12 [TAB]ext{ cm} \) breaking KaTeX rendering.
--
-- Fix: replace chr(9) (tab) with backslash in option_a/b/c/d, question_stem,
--      and explanation_short across all questions. Tabs have no legitimate use
--      in these fields — every tab is a corrupted backslash from the bug.

UPDATE questions
SET
    option_a         = replace(option_a,          chr(9), '\'),
    option_b         = replace(option_b,          chr(9), '\'),
    option_c         = replace(option_c,          chr(9), '\'),
    option_d         = replace(option_d,          chr(9), '\'),
    question_stem    = replace(question_stem,     chr(9), '\'),
    explanation_short = replace(explanation_short, chr(9), '\')
WHERE
    option_a          LIKE '%' || chr(9) || '%'
    OR option_b       LIKE '%' || chr(9) || '%'
    OR option_c       LIKE '%' || chr(9) || '%'
    OR option_d       LIKE '%' || chr(9) || '%'
    OR question_stem  LIKE '%' || chr(9) || '%'
    OR explanation_short LIKE '%' || chr(9) || '%';

-- Fix JSONB fields: explanation_steps, core_concept, alternative_approach,
-- prerequisites, wrong_answer_explanations
UPDATE questions
SET
    explanation_steps        = replace(explanation_steps::text,        chr(9), '\')::jsonb,
    core_concept             = replace(core_concept::text,             chr(9), '\')::jsonb,
    alternative_approach     = replace(alternative_approach::text,     chr(9), '\')::jsonb,
    prerequisites            = replace(prerequisites::text,            chr(9), '\')::jsonb,
    wrong_answer_explanations = replace(wrong_answer_explanations::text, chr(9), '\')::jsonb
WHERE
    explanation_steps::text        LIKE '%' || chr(9) || '%'
    OR core_concept::text          LIKE '%' || chr(9) || '%'
    OR alternative_approach::text  LIKE '%' || chr(9) || '%'
    OR prerequisites::text         LIKE '%' || chr(9) || '%'
    OR wrong_answer_explanations::text LIKE '%' || chr(9) || '%';
