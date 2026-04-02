-- V20: MATH-ALG-001 — insert "Recall the quadratic formula" step so the formula
-- is explicitly shown before the substitution step.

UPDATE questions
SET alternative_approach = jsonb_set(
    alternative_approach,
    '{steps}',
    '[
      {
        "title": "Rewrite in standard form",
        "content": "Rearrange the equation into standard quadratic form by setting height equal to zero.",
        "math": "-5t^{2} + 20t = 0 \\quad \\Rightarrow \\quad 5t^{2} - 20t = 0"
      },
      {
        "title": "Recall the quadratic formula",
        "content": "For any equation ax\u00b2 + bx + c = 0, the solutions are given by:",
        "math": "t = \\frac{-b \\pm \\sqrt{b^{2} - 4ac}}{2a}"
      },
      {
        "title": "Substitute and simplify",
        "content": "Identify a = 5, b = \u221220, c = 0, then substitute into the formula and simplify.",
        "math": "t = \\frac{-(-20) \\pm \\sqrt{(-20)^{2} - 4(5)(0)}}{2(5)} = \\frac{20 \\pm \\sqrt{400}}{10}"
      },
      {
        "title": "Simplify and choose the non-zero root",
        "content": "Evaluate the square root and compute both solutions. Discard t = 0 since it represents the launch.",
        "math": "t = \\frac{20 \\pm 20}{10} \\Rightarrow t = 4 \\text{ or } t = 0"
      }
    ]'::jsonb
)
WHERE external_id = 'MATH-ALG-001';
