-- V26: Fix MATH-PS-004 display and answer
--
-- Problems fixed:
--   1. question_stem used a markdown pipe table (| col | col |) which does not render in HTML.
--      Replaced with a proper HTML <table> as required by the prompt rules.
--
--   2. Correct answer was 'A' (12.1 hours) but the actual weighted mean is:
--      (2.5×24 + 8×56 + 13×78 + 18×32 + 23.5×10) / 200 = 2333/200 = 11.665
--      Closest option: B=11.5 (diff=0.165), not A=12.1 (diff=0.435).
--      Fixed: correct_answer A → B.
--
--   3. explanation_steps step 4 claimed "12.1 hours is the closest to 11.7" — incorrect.
--      Fixed to correctly state B=11.5 is closest.

-- 1. Fix question stem: markdown table → HTML table
UPDATE questions
SET question_stem =
  'A survey asked 200 high school students about their weekly screen time. The results are shown in the table below:\n' ||
  '<table><thead><tr><th>Screen Time (hours)</th><th>Number of Students</th></tr></thead>' ||
  '<tbody>' ||
  '<tr><td>0–5</td><td>24</td></tr>' ||
  '<tr><td>6–10</td><td>56</td></tr>' ||
  '<tr><td>11–15</td><td>78</td></tr>' ||
  '<tr><td>16–20</td><td>32</td></tr>' ||
  '<tr><td>21+</td><td>10</td></tr>' ||
  '</tbody></table>' ||
  '\n\nIf we use the midpoint of each interval to estimate the average weekly screen time, which of the following is closest to the mean?'
WHERE external_id = 'MATH-PS-004';

-- 2. Fix correct answer: A → B
UPDATE question_answers
SET correct_answer = 'B'
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-PS-004');

-- 3. Fix explanation step 4 (index 3): update content and add math showing closest distance
UPDATE questions
SET explanation_steps = jsonb_set(
    explanation_steps,
    '{3}',
    '{"title": "Select the closest answer",
      "content": "The estimated mean is 11.665 ≈ 11.7 hours. Comparing the distance to each answer choice, option B (11.5 hours) is closest, with a difference of only 0.165 hours.",
      "math": "|11.665 - 11.5| = 0.165 \\u2190 smallest difference"
     }'::jsonb
)
WHERE external_id = 'MATH-PS-004';
