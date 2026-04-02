-- V28: Fix MATH-GEO-003 — question stem and diagram vertices
--
-- Problems fixed:
--
--   1. question_stem had stray "\ " (backslash-space) before every variable name:
--      "In triangle \ ABC ... \ AB = 7 ... \ BC = 9 ... \ AC = 5 ... angle \ B"
--      These render as literal backslash characters in HTML — not LaTeX commands.
--      Fixed: removed all stray backslashes; variable names are plain text.
--
--   2. Diagram vertices were not geometrically proportional.
--      Current: A=(196,60), B=(50,240), C=(260,240)
--        → pixel angle at B ≈ 51°  (should be ≈ 33.6°)
--        → pixel side ratios AB:BC:AC ≈ 1.21:1.10:1.00 (should be 1.40:1.80:1.00)
--      Fixed: vertices computed from cos(B) = 5/6, scale k=22 px/unit:
--        A = (178, 155), B = (50, 240), C = (248, 240)
--        → pixel angle at B = arccos(5/6) ≈ 33.6° ✓
--        → pixel distances AB=154, BC=198, AC=110 → ratio 7:9:5 ✓

-- 1. Fix question stem
UPDATE questions
SET question_stem =
  'In triangle ABC, the sides have lengths AB = 7, BC = 9, and AC = 5. ' ||
  'Which of the following is closest to the measure of angle B (the angle at vertex B)?'
WHERE external_id = 'MATH-GEO-003';

-- 2. Fix diagram vertices
UPDATE questions
SET diagram = jsonb_set(
    jsonb_set(
        jsonb_set(
            diagram,
            '{svgConfig,vertices,A}',
            '{"x": 178, "y": 155}'::jsonb
        ),
        '{svgConfig,vertices,B}',
        '{"x": 50, "y": 240}'::jsonb
    ),
    '{svgConfig,vertices,C}',
    '{"x": 248, "y": 240}'::jsonb
)
WHERE external_id = 'MATH-GEO-003';
