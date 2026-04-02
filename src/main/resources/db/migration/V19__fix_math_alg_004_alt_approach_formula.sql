-- V19: MATH-ALG-004 — insert "State the quadratic formula" step (with actual formula)
-- before the substitution step so reviewers/students see the formula definition first.

UPDATE questions
SET alternative_approach = jsonb_set(
    alternative_approach,
    '{steps}',
    '[
      {
        "title": "Identify coefficients",
        "content": "Rewrite the equation h(t) = 0 in standard form and identify the coefficients: a = \u221216, b = 64, and c = 0.",
        "math": "-16t^{2} + 64t + 0 = 0"
      },
      {
        "title": "Recall the quadratic formula",
        "content": "For any quadratic equation ax\u00b2 + bx + c = 0, the solutions are given by:",
        "math": "t = \\frac{-b \\pm \\sqrt{b^{2} - 4ac}}{2a}"
      },
      {
        "title": "Substitute and simplify",
        "content": "Substitute a = \u221216, b = 64, c = 0 into the formula and simplify.",
        "math": "t = \\frac{-64 \\pm \\sqrt{64^{2} - 4(-16)(0)}}{2(-16)} = \\frac{-64 \\pm \\sqrt{4096}}{-32} = \\frac{-64 \\pm 64}{-32}"
      },
      {
        "title": "Evaluate both solutions",
        "content": "The two solutions are t = (\u221264 + 64)/(\u221232) = 0 and t = (\u221264 \u2212 64)/(\u221232) = 4. Discard t = 0 (launch time), so the answer is t = 4.",
        "math": "t = \\frac{-128}{-32} = 4"
      }
    ]'::jsonb
)
WHERE external_id = 'MATH-ALG-004';
