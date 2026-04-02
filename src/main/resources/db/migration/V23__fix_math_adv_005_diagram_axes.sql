-- V23: Fix MATH-ADV-005 diagram axis range
-- Issues:
--   1. diagramType was "svg_programmatic" with type "quartic" which renderer did not support
--      (quartic support added to renderer.js in this release)
--   2. yMax=40 far too high — function peaks at only ~9.25 in the x window, leaving top 75% empty
--   3. yMin=-20 clips both arms too early; with tighter yMin=-15 both downward arms are clearly visible
--   4. xMin=-3 unnecessary — function is -281 there (completely off any reasonable chart)
--      Narrowing to xMin=-2 keeps the visible portion without dead space
-- Function: f(x) = -2x^4 + 5x^3 - 3x + 7
--   Peak ~9.25 at x≈1.5; both arms cross y=-15 around x≈-1.5 and x≈2.95

UPDATE questions
SET diagram = jsonb_set(
    jsonb_set(
        jsonb_set(
            jsonb_set(
                diagram,
                '{svgConfig,xMin}', '-2'::jsonb
            ),
            '{svgConfig,xMax}', '3'::jsonb
        ),
        '{svgConfig,yMin}', '-15'::jsonb
    ),
    '{svgConfig,yMax}', '15'::jsonb
)
WHERE external_id = 'MATH-ADV-005';
