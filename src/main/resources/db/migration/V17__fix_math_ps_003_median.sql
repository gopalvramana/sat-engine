-- V17: Fix MATH-PS-003 median question.
-- Root cause: chart had point (4,82) making median=81 which is not an answer
-- choice. Both 80 and 82 were equally close — ambiguous. Explanation also said
-- "select the closest answer" which is invalid SAT question design.
-- Fix: change (4,82) → (4,80) so scores are 72,78,80,80,86,88 → median=80 exactly.

UPDATE questions
SET
  diagram = '{
    "diagramType": "chartjs",
    "chartConfig": {
      "title": "Hours Studied vs Test Score",
      "chartType": "scatter",
      "gridLines": true,
      "xAxis": { "min": 0, "max": 8, "label": "Hours Studied", "stepSize": 1 },
      "yAxis": { "min": 60, "max": 95, "label": "Test Score", "stepSize": 5 },
      "datasets": [
        {
          "label": "Students",
          "color": "#ef4444",
          "showPoints": true,
          "pointRadius": 6,
          "points": [
            { "x": 1,   "y": 72 },
            { "x": 2,   "y": 78 },
            { "x": 3,   "y": 80 },
            { "x": 4,   "y": 80 },
            { "x": 5.5, "y": 86 },
            { "x": 6.5, "y": 88 }
          ]
        }
      ]
    }
  }'::jsonb,

  explanation_short = 'Arrange the 6 test scores in order: 72, 78, 80, 80, 86, 88. The median of an even-count set is the average of the two middle values: \(\\frac{80+80}{2} = 80\).',

  explanation_steps = '[
    {
      "title": "Read the scores from the scatter plot",
      "content": "Identify each student''s test score from the scatter plot. The six test scores are: 72, 78, 80, 80, 86, and 88.",
      "math": null
    },
    {
      "title": "Arrange scores in ascending order",
      "content": "List all six scores from least to greatest to prepare for finding the median.",
      "math": "72, 78, 80, 80, 86, 88"
    },
    {
      "title": "Find the median of an even-numbered data set",
      "content": "With 6 data points, the median is the average of the 3rd and 4th values. Both the 3rd and 4th values are 80.",
      "math": "\\\\text{Median} = \\\\frac{80 + 80}{2} = \\\\frac{160}{2} = 80"
    }
  ]'::jsonb

WHERE external_id = 'MATH-PS-003';
