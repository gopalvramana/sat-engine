-- V15: Replace MATH-ALG-007 chartjs scatter diagram with svg_programmatic
-- coordinate_plane / system_of_equations.
-- The scatter chart drew 4 hand-picked points per line (looked like dots).
-- The SVG renderer evaluates y=mx+b continuously, giving clean mathematical lines.
UPDATE questions
SET diagram = '{
  "diagramType": "svg_programmatic",
  "svgConfig": {
    "shape": "coordinate_plane",
    "subtype": "system_of_equations",
    "width": 300,
    "height": 300,
    "xMin": -1,
    "xMax": 5,
    "yMin": 0,
    "yMax": 12,
    "functions": [
      {
        "type": "linear",
        "params": { "m": -3, "b": 11 },
        "color": "#2563eb",
        "label": "y = -3x + 11",
        "labelAt": { "x": 0.1, "y": 10.7 }
      },
      {
        "type": "linear",
        "params": { "m": 1, "b": 1 },
        "color": "#dc2626",
        "label": "y = x + 1",
        "labelAt": { "x": 3.4, "y": 4.2 }
      }
    ],
    "intersections": [
      { "x": 2.5, "y": 3.5, "label": "(2.5, 3.5)" }
    ]
  }
}'::jsonb
WHERE external_id = 'MATH-ALG-007';
