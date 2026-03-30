-- V8: Fix RW-ENG-003 and RW-ENG-005 — bad Standard English question format.
--
-- Both questions were generated with the old Math prompt which produced
-- meta-analysis questions ("which best explains pronoun use") instead of
-- SAT-style fill-in-the-blank grammar questions. They also had options
-- embedded inside questionStem separated by \n\n.
--
-- Fix: strip the embedded options from questionStem, reject both questions.
-- They will be regenerated with the correct prompt.

-- RW-ENG-003: strip embedded options from stem, reject
UPDATE questions
SET
    question_stem = 'The city council members debated the new zoning proposal for hours, but they ultimately decided to table it until the next meeting. Which of the following best explains why the pronoun use in this sentence is effective?',
    status        = 'rejected'
WHERE external_id = 'RW-ENG-003';

-- RW-ENG-005: strip embedded options from stem (already rejected)
UPDATE questions
SET
    question_stem = 'The research team discovered that many employees felt disconnected from their workplace, so they decided to implement new mentorship programs. Which of the following best describes the problem with the pronoun use in this sentence?'
WHERE external_id = 'RW-ENG-005';
