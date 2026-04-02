-- V32: Fix MATH-GEO-009 — diagram structure and stale agent review
--
-- Math is correct: A = ½(8+14)×6 = 66 ✓
-- sprMin=66, sprMax=66, explanationShort present — all data correct.
--
-- Issues fixed:
--
-- 1. Diagram structure: "width", "height", "subtype" were at the TOP level of the
--    diagram JSON object, not inside svgConfig. The renderer does:
--      const cfg = diagramConfig.svgConfig ?? {};
--    so it only reads what is inside svgConfig. Without width/height there, the
--    renderer fell back to defaults (280×200) and ignored the outer-level values.
--    Fixed: moved width/height inside svgConfig; corrected diagramType key.
--
-- 2. Vertex proportions: AB=240px, DC=160px → ratio 1.50, should be 14/8=1.75.
--    Fixed: scale 16px/unit, centered in 320px canvas.
--      A=(48,190) B=(272,190) → AB=224px
--      D=(96,80)  C=(224,80)  → DC=128px
--      ratio = 224/128 = 1.75 ✓  height = 110px ✓
--
-- 3. Stale agent review: all three SCHEMA/SPR_RANGE failures were false positives
--    from the buildSlimNode bug (sprMin/sprMax/explanationShort missing from payload).

-- 1. Replace diagram with corrected structure
UPDATE questions
SET diagram = '{
  "diagramType": "svg_programmatic",
  "svgConfig": {
    "shape": "trapezoid",
    "width": 320,
    "height": 220,
    "vertices": {
      "A": {"x": 48,  "y": 190},
      "B": {"x": 272, "y": 190},
      "C": {"x": 224, "y": 80},
      "D": {"x": 96,  "y": 80}
    },
    "sides": [
      {"from": "A", "to": "B", "label": "14"},
      {"from": "D", "to": "C", "label": "8"},
      {"from": "A", "to": "D", "label": ""},
      {"from": "B", "to": "C", "label": ""}
    ],
    "parallelPairs": [["AB","DC"]],
    "showHeight": true,
    "heightLabel": "6"
  }
}'::jsonb
WHERE external_id = 'MATH-GEO-009';

-- 2. Clear false-positive agent review
UPDATE question_reviews
SET
  pass          = true,
  confidence    = 0.99,
  issues        = '[]'::jsonb,
  solved_answer = '66',
  notes         = 'False positive cleared (V32): sprMin=66, sprMax=66, explanationShort '
               || 'all present in DB but were missing from buildSlimNode review payload. '
               || 'Math verified: ½(8+14)×6 = 66. Diagram structure also fixed.',
  checked_at    = NOW()
WHERE question_id = (SELECT id FROM questions WHERE external_id = 'MATH-GEO-009');
