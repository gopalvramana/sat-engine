-- V27: Fix MATH-ALG-012 — restructure ambiguous "NOT a solution" question
--
-- Problem: x² − 5x + 6 = 0 has exactly two solutions (x=2 and x=3).
-- Original options A=1, B=2, C=3, D=6 meant BOTH A and D were "not solutions",
-- giving two defensible correct answers — flagged critical by agent review.
--
-- Fix: Reframe as "What is the complete solution set?" with set-notation options.
-- Only B = {2, 3} is correct. Each wrong option maps to a distinct student error:
--   A = {−2, −3} : sign-flip error — student writes (x+2)(x+3)=0 instead of (x−2)(x−3)=0
--   C = {1, 6}   : confuses the factor pair 1×6 of the constant term with the roots
--   D = {2, 5}   : correctly finds x=2 but computes the second root as 5 (arithmetic error)

-- 1. Update question stem, options, and explanation steps (all on questions table)
UPDATE questions
SET
  question_stem = 'If \( x^2 - 5x + 6 = 0 \), what is the complete solution set for \( x \)?',
  option_a = '\(\{-2,\ -3\}\)',
  option_b = '\(\{2,\ 3\}\)',
  option_c = '\(\{1,\ 6\}\)',
  option_d = '\(\{2,\ 5\}\)',
  trap_category = 'sign_error',
  trap_explanation = 'Students who factor carelessly write (x+2)(x+3)=0, giving roots −2 and −3 (option A). This is the most common error when students forget that (x−r)=0 means x=r, not x=−r.',
  explanation_steps = $json$[
    {
      "title": "Factor the Quadratic",
      "content": "Find two numbers that multiply to 6 and add to −5. These are −2 and −3, so the equation factors into two binomials.",
      "math": "x^2 - 5x + 6 = (x - 2)(x - 3) = 0"
    },
    {
      "title": "Apply the Zero Product Property",
      "content": "If a product equals zero, at least one factor must equal zero. Set each factor equal to zero and solve for x.",
      "math": "x - 2 = 0 \\Rightarrow x = 2 \\qquad x - 3 = 0 \\Rightarrow x = 3"
    },
    {
      "title": "State the Complete Solution Set",
      "content": "Both x = 2 and x = 3 satisfy the original equation, so the solution set is {2, 3}. Option A is the classic sign-flip trap — writing (x + 2)(x + 3) = 0 gives wrong signs on both roots.",
      "math": "\\{2,\\, 3\\}"
    }
  ]$json$::jsonb
WHERE external_id = 'MATH-ALG-012';

-- 2. Update correct answer (on question_answers table)
UPDATE question_answers
SET correct_answer = 'B'
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-ALG-012');
