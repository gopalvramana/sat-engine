-- V24: Fix MATH-PS-008 bar chart diagram
--
-- Problems fixed:
--   1. Ambiguous data: Baseball=140 = Basketball+Soccer=140, so 35% answered correctly
--      by just reading the Baseball bar — two interpretations of same answer.
--      Fixed: Tennis 120→100, Baseball 140→160 (total still 400).
--      Now each distractor maps to a distinct mistake:
--        A=30%  → reading error (basketball misread as 60: 60+60=120)
--        B=35%  → correct (basketball+soccer = 80+60 = 140)
--        C=40%  → picks highest bar only (baseball=160)
--        D=45%  → picks wrong sport pair (basketball+tennis = 80+100=180)
--
--   2. Diagram config used wrong field names for renderer:
--        "labels"          → must be "categories"   (bar x-axis labels)
--        "backgroundColor" → must be "colors"       (per-bar colour array)
--      Without these, bars rendered with no labels and default single colour.
--
--   3. Missing title, yAxis config, and diagramType was "type" (not wrong but normalised).

UPDATE questions
SET diagram = '{
  "diagramType": "chartjs",
  "chartConfig": {
    "chartType": "bar",
    "title": "Favorite Sport Survey (400 Students)",
    "categories": ["Basketball", "Soccer", "Tennis", "Baseball"],
    "yAxis": {
      "min": 0,
      "max": 180,
      "stepSize": 20,
      "label": "Number of Students"
    },
    "xAxis": {
      "label": "Sport"
    },
    "datasets": [
      {
        "label": "Number of Students",
        "data": [80, 60, 100, 160],
        "colors": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
      }
    ]
  }
}'::jsonb
WHERE external_id = 'MATH-PS-008';
