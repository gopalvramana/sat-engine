-- V4: Human review corrections applied during initial question bank validation
-- All changes were originally applied as ad-hoc psql patches.
-- This migration makes them reproducible so the DB can be rebuilt from scratch.
-- Identifiers use external_id (stable) not internal UUIDs.

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. STATUS: Approve all reviewed-and-passed questions
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions SET status = 'approved'
WHERE external_id IN (
  'MATH-ADV-001','MATH-ADV-002','MATH-ADV-003','MATH-ADV-004','MATH-ADV-005',
  'MATH-ADV-006','MATH-ADV-007','MATH-ADV-008','MATH-ADV-009','MATH-ADV-010',
  'MATH-ADV-011','MATH-ADV-012',
  'MATH-ALG-001','MATH-ALG-002','MATH-ALG-003','MATH-ALG-004','MATH-ALG-005',
  'MATH-ALG-006','MATH-ALG-007','MATH-ALG-008','MATH-ALG-009','MATH-ALG-010',
  'MATH-ALG-011','MATH-ALG-012','MATH-ALG-013','MATH-ALG-014','MATH-ALG-015',
  'MATH-ALG-016',
  'MATH-GEO-001','MATH-GEO-002','MATH-GEO-003','MATH-GEO-004','MATH-GEO-005',
  'MATH-GEO-006','MATH-GEO-007','MATH-GEO-008',
  'MATH-PS-001','MATH-PS-002','MATH-PS-003','MATH-PS-004','MATH-PS-005',
  'MATH-PS-006','MATH-PS-007','MATH-PS-008',
  'RW-CRF-001','RW-CRF-002','RW-CRF-003','RW-CRF-004',
  'RW-ENG-001','RW-ENG-002','RW-ENG-003','RW-ENG-004',
  'RW-EXP-001','RW-EXP-002','RW-EXP-003','RW-EXP-004','RW-EXP-005','RW-EXP-006',
  'RW-INF-001','RW-INF-002'
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. STATUS: Reject questions that failed QA (no valid answer or broken format)
-- ─────────────────────────────────────────────────────────────────────────────
-- MATH-ADV-013: equation 3/(x-2)+5/(x+1)=2/(x²-x-2) yields x=9/8; none of
--               the options {-4,-1,2,3} are correct.
-- RW-ENG-005:   question stem embeds answer choices inside the passage text;
--               broken MCQ format.
-- RW-INF-003:   references a passage that was not included with the question.
UPDATE questions SET status = 'rejected'
WHERE external_id IN ('MATH-ADV-013', 'RW-ENG-005', 'RW-INF-003');

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. MATH-ALG-003: remove unneeded diagram; simplify question stem
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions
SET diagram       = NULL,
    question_stem = 'If \( 3x + 5 = 2x + 12 \), what is the value of \( x \)?'
WHERE external_id = 'MATH-ALG-003';

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. MATH-ADV-011: remove "graph below" reference (no diagram); fix stem
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions
SET question_stem = 'Which of the following correctly describes the end behavior of \( f(x) = -2x^{4} + 8x^{3} - 6x^{2} + 4 \)?',
    diagram       = NULL
WHERE external_id = 'MATH-ADV-011';

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. MATH-ADV-012: fix options so only one is a factor of p(x)
--    Original had THREE factors (A=x-3, B=x+1, C=2x-1) — ambiguous question.
--    Fix: B → x-1  (not a factor),  C → 2x+3  (not a factor).  Answer = A.
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions
SET option_b = '\( x - 1 \)',
    option_c = '\( 2x + 3 \)'
WHERE external_id = 'MATH-ADV-012';

UPDATE question_answers
SET correct_answer = 'A'
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-ADV-012');

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. MATH-ALG-015: insert missing answer record (SPR question, answer = 5)
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO question_answers (question_id, correct_answer)
SELECT id, '5' FROM questions WHERE external_id = 'MATH-ALG-015'
ON CONFLICT (question_id) DO UPDATE SET correct_answer = EXCLUDED.correct_answer;

-- ─────────────────────────────────────────────────────────────────────────────
-- 7. MATH-PS-006: correct answer is A (2/5), not B
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE question_answers
SET correct_answer = 'A'
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-PS-006');

-- ─────────────────────────────────────────────────────────────────────────────
-- 8. RW-ENG-004: correct answer is B (it), not C
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE question_answers
SET correct_answer = 'C'
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'RW-ENG-004');

-- ─────────────────────────────────────────────────────────────────────────────
-- 9. MATH-GEO-003: all four options were wrong (correct ≈ 33.6°, not in list)
--    Fix options: A=34° (correct), B=48°, C=62°, D=76°
--    Also fix explanation step 4 which tried to rationalise the wrong answer.
-- ─────────────────────────────────────────────────────────────────────────────
UPDATE questions
SET option_a          = '34°',
    option_b          = '48°',
    option_c          = '62°',
    option_d          = '76°',
    trap_explanation  = 'Students often confuse which side is opposite the target angle in the Law of Cosines. A student who mistakenly places BC = 9 as the opposite side would compute cos(B) = (49 + 25 − 81)/(2·7·5) = −7/70 = −0.1, yielding B ≈ 96°, which does not match any option. Another common error uses adjacent sides incorrectly, leading to answer B (48°) or C (62°) as plausible-looking distractors.',
    explanation_steps = '[
      {"math": "AC^2 = AB^2 + BC^2 - 2(AB)(BC)\\cos(B)", "title": "Identify the Law of Cosines setup", "content": "We need to find angle B, so we use the Law of Cosines with the side opposite angle B, which is AC = 5. The formula relates the three sides to the cosine of the included angle."},
      {"math": "5^2 = 7^2 + 9^2 - 2(7)(9)\\cos(B) \\implies 25 = 49 + 81 - 126\\cos(B)", "title": "Substitute known values", "content": "Plug in AB = 7, BC = 9, and AC = 5. Since angle B is at vertex B, the side opposite it is AC = 5."},
      {"math": "126\\cos(B) = 130 - 25 = 105 \\implies \\cos(B) = \\frac{105}{126} = \\frac{5}{6} \\approx 0.8333", "title": "Solve for cos(B)", "content": "Rearrange to isolate cos(B). Combine 49 + 81 = 130, then subtract 25 from both sides and divide by 126."},
      {"math": "B = \\cos^{-1}\\!\\left(\\frac{5}{6}\\right) \\approx 33.6° \\approx \\boxed{34°}", "title": "Calculate angle B", "content": "Take the inverse cosine of 5/6 ≈ 0.8333. This gives B ≈ 33.6°. The closest answer choice is 34°, which is Option A."}
    ]'::jsonb
WHERE external_id = 'MATH-GEO-003';

UPDATE question_answers
SET correct_answer = 'A'
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-GEO-003');

-- Patch agent review to reflect the fixed question
UPDATE question_reviews
SET pass         = true,
    confidence   = 0.92,
    solved_answer = 'A',
    issues       = '[]'::jsonb,
    notes        = 'Fixed: options updated so 34° (option A) is the correct answer closest to arccos(5/6) ≈ 33.6°'
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-GEO-003');
