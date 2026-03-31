-- V9: Reject RW-ALG-001 — miscategorised question (algebra domain under reading_writing section)
-- Root cause: pickSection() was random when --domain was specified but --section was not.
-- Fix applied in GenerateStage.java: sectionForDomain() now deterministically infers section from domain.

UPDATE questions
SET status = 'rejected'
WHERE external_id = 'RW-ALG-001';
