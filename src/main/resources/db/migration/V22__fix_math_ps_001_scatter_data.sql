-- V22: Replace MATH-PS-001 scatter plot data points
-- Old data had slope ~7.3 pts/hr (14.6 pts/2 hrs) which matched option C, not marked answer A.
-- New data has slope ~4.5 pts/hr (9.1 pts/2 hrs) which correctly matches option A (8-10 pts/2 hrs).
-- Regression verified: y = 4.526x + 40.84, strong positive linear relationship.
-- Diagram is stored as a jsonb column directly on the questions table.

UPDATE questions
SET diagram = jsonb_set(
    diagram,
    '{chartConfig,datasets,0,points}',
    '[
      {"x": 1,   "y": 46},
      {"x": 2,   "y": 50},
      {"x": 3,   "y": 55},
      {"x": 4,   "y": 57},
      {"x": 5,   "y": 65},
      {"x": 6,   "y": 66},
      {"x": 7,   "y": 72},
      {"x": 7.5, "y": 75},
      {"x": 8,   "y": 78},
      {"x": 9,   "y": 82}
    ]'::jsonb
)
WHERE external_id = 'MATH-PS-001';
