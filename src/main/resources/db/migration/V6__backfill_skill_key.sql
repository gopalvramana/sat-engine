-- V6: Backfill skill_key for all questions generated before V5 (skill_key was NULL)
-- Matches the free-form `skill` text field to canonical slugs from sat_taxonomy.json.
-- Pattern matching is case-insensitive (ILIKE). Most specific patterns first.

-- ─────────────────────────────────────────────────────────────────────────────
-- ALGEBRA domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'systems_linear_eq'
WHERE skill_key IS NULL AND domain = 'algebra'
  AND (skill ILIKE '%system%' OR skill ILIKE '%systems of linear%' OR skill ILIKE '%systems of equation%');

UPDATE questions SET skill_key = 'nonlinear_eq_systems'
WHERE skill_key IS NULL AND domain = 'algebra'
  AND skill ILIKE '%nonlinear%';

UPDATE questions SET skill_key = 'quadratic_equations'
WHERE skill_key IS NULL AND domain = 'algebra'
  AND (skill ILIKE '%quadratic%' OR skill ILIKE '%quadratic formula%');

UPDATE questions SET skill_key = 'rational_expressions'
WHERE skill_key IS NULL AND domain = 'algebra'
  AND (skill ILIKE '%rational equation%' OR skill ILIKE '%extraneous%');

UPDATE questions SET skill_key = 'linear_eq_one_var'
WHERE skill_key IS NULL AND domain = 'algebra'
  AND (skill ILIKE '%linear equation%' OR skill ILIKE '%variables on both%' OR skill ILIKE '%solving linear%');

-- ─────────────────────────────────────────────────────────────────────────────
-- ADVANCED MATH domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'polynomial_functions'
WHERE skill_key IS NULL AND domain = 'advanced_math'
  AND (skill ILIKE '%end behavior%' OR skill ILIKE '%leading coefficient%' OR skill ILIKE '%polynomial behavior%');

UPDATE questions SET skill_key = 'factoring'
WHERE skill_key IS NULL AND domain = 'advanced_math'
  AND (skill ILIKE '%factoring%' OR skill ILIKE '%roots%' OR skill ILIKE '%rational roots%');

UPDATE questions SET skill_key = 'quadratic_equations'
WHERE skill_key IS NULL AND domain = 'advanced_math'
  AND (skill ILIKE '%quadratic%' OR skill ILIKE '%substitution%');

UPDATE questions SET skill_key = 'rational_expressions'
WHERE skill_key IS NULL AND domain = 'advanced_math'
  AND (skill ILIKE '%rational equation%' OR skill ILIKE '%polynomial denominator%');

UPDATE questions SET skill_key = 'polynomial_operations'
WHERE skill_key IS NULL AND domain = 'advanced_math'
  AND (skill ILIKE '%polynomial%');

-- ─────────────────────────────────────────────────────────────────────────────
-- GEOMETRY & TRIGONOMETRY domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'law_sines_cosines'
WHERE skill_key IS NULL AND domain = 'geometry_trigonometry'
  AND (skill ILIKE '%law of cosine%' OR skill ILIKE '%law of sine%' OR skill ILIKE '%cosines%' OR skill ILIKE '%sines%');

UPDATE questions SET skill_key = 'right_triangle_trig'
WHERE skill_key IS NULL AND domain = 'geometry_trigonometry'
  AND (skill ILIKE '%trigonometr%' OR skill ILIKE '%trig ratio%' OR skill ILIKE '%right triangle%' OR skill ILIKE '%angle of elevation%');

-- ─────────────────────────────────────────────────────────────────────────────
-- PROBLEM SOLVING & DATA ANALYSIS domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'conditional_probability'
WHERE skill_key IS NULL AND domain = 'problem_solving_data'
  AND (skill ILIKE '%conditional%' OR skill ILIKE '%two-way%' OR skill ILIKE '%frequency table%');

UPDATE questions SET skill_key = 'scatterplots'
WHERE skill_key IS NULL AND domain = 'problem_solving_data'
  AND (skill ILIKE '%scatter%' OR skill ILIKE '%regression%' OR skill ILIKE '%correlation%');

UPDATE questions SET skill_key = 'percentages'
WHERE skill_key IS NULL AND domain = 'problem_solving_data'
  AND skill ILIKE '%percent%';

UPDATE questions SET skill_key = 'data_center'
WHERE skill_key IS NULL AND domain = 'problem_solving_data'
  AND (skill ILIKE '%average%' OR skill ILIKE '%mean%' OR skill ILIKE '%median%' OR skill ILIKE '%weighted average%');

-- ─────────────────────────────────────────────────────────────────────────────
-- CRAFT & STRUCTURE domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'rhetorical_devices'
WHERE skill_key IS NULL AND domain = 'craft_structure'
  AND (skill ILIKE '%rhetorical%' OR skill ILIKE '%tone%' OR skill ILIKE '%juxtaposition%');

UPDATE questions SET skill_key = 'text_structure_purpose'
WHERE skill_key IS NULL AND domain = 'craft_structure'
  AND (skill ILIKE '%structure%' OR skill ILIKE '%transition%' OR skill ILIKE '%purpose%');

-- ─────────────────────────────────────────────────────────────────────────────
-- EXPRESSION OF IDEAS domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'rhetorical_synthesis'
WHERE skill_key IS NULL AND domain = 'expression_ideas';

-- ─────────────────────────────────────────────────────────────────────────────
-- INFORMATION & IDEAS domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'inferences'
WHERE skill_key IS NULL AND domain = 'information_ideas'
  AND (skill ILIKE '%rhetorical device%' OR skill ILIKE '%function%' OR skill ILIKE '%effect%');

UPDATE questions SET skill_key = 'central_ideas'
WHERE skill_key IS NULL AND domain = 'information_ideas'
  AND (skill ILIKE '%main idea%' OR skill ILIKE '%purpose%' OR skill ILIKE '%detail%');

-- ─────────────────────────────────────────────────────────────────────────────
-- STANDARD ENGLISH CONVENTIONS domain
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET skill_key = 'pronoun_agreement'
WHERE skill_key IS NULL AND domain = 'standard_english'
  AND (skill ILIKE '%pronoun%' OR skill ILIKE '%antecedent%');
