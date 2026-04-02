-- V25: Fix MATH-PS-007 grouped bar chart
--
-- Problems fixed:
--   1. Wrong math: Q2 Region C was 13.0, giving weighted avg = 118/9 = $13.11
--      Marked answer B = $13.20 was incorrect.
--      Fix: Region C Q2: 13.0 → 13.4  (now: (3×12+4×14+2×13.4)/9 = 118.8/9 = $13.20 exactly)
--
--   2. Diagram field names wrong (same pattern as MATH-PS-008):
--      "labels"          → must be "categories"   (renderer field for bar x-axis labels)
--      "backgroundColor" → must be "color"        (single colour per dataset)
--      Missing title, yAxis config, diagramType was "type"

UPDATE questions
SET diagram = '{
  "diagramType": "chartjs",
  "chartConfig": {
    "chartType": "bar",
    "title": "Average Monthly Streaming Spend by Region",
    "categories": ["Region A", "Region B", "Region C"],
    "yAxis": {
      "min": 0,
      "max": 16,
      "stepSize": 2,
      "label": "Avg Spend per Subscriber ($)"
    },
    "xAxis": {
      "label": "Region"
    },
    "datasets": [
      {
        "label": "Q1 Spending ($)",
        "data": [11.5, 13.0, 12.5],
        "color": "#4472C4"
      },
      {
        "label": "Q2 Spending ($)",
        "data": [12.0, 14.0, 13.4],
        "color": "#ED7D31"
      }
    ]
  }
}'::jsonb
WHERE external_id = 'MATH-PS-007';
