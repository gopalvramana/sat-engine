-- V29: Fix MATH-PS-009 diagram — flat structure → nested chartConfig
--
-- Problem: renderer requires diagramConfig.chartConfig as a nested object.
--   const cfg = diagramConfig.chartConfig;
--   if (!cfg) { hostEl.innerHTML = '<p>Missing chartConfig</p>'; return; }
--
-- MATH-PS-009 stored all chart fields flat at the top level:
--   { "type": "chartjs", "chartType": "line", "title": "...", "categories": [...], ... }
-- This caused the renderer to show nothing (no chartConfig key found).
--
-- Fix: wrap chart fields inside chartConfig and normalise "type" → "diagramType".
-- Data is verified correct: rate = 450/3 = 150 widgets/hr → points at (0,0),(1,150),...,(8,1200)

UPDATE questions
SET diagram = '{
  "diagramType": "chartjs",
  "chartConfig": {
    "chartType": "line",
    "title": "Widget Production Over Time",
    "categories": ["0","1","2","3","4","5","6","7","8"],
    "xAxis": {
      "label": "Time (hours)"
    },
    "yAxis": {
      "min": 0,
      "max": 1400,
      "stepSize": 200,
      "label": "Widgets Produced"
    },
    "datasets": [
      {
        "label": "Production",
        "data": [0, 150, 300, 450, 600, 750, 900, 1050, 1200],
        "color": "#2563eb"
      }
    ]
  }
}'::jsonb
WHERE external_id = 'MATH-PS-009';
