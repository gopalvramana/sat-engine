-- ============================================================
-- V51: Backfill template + variant from content JSONB
-- ============================================================
-- Every template-aware generator (L1V, L2V, LFN, SLE, LIN, EXP, NLE)
-- writes params["tpl"] and params["variant"] into the MathObject.
-- Those params are stored verbatim inside content->'mathObject'->'params'.
--
-- Skills without template tracking (circles, statistics, etc.) will
-- correctly remain NULL — the diversity query handles NULLs gracefully.
-- ============================================================

UPDATE sat_questions
SET
    template = content -> 'mathObject' -> 'params' ->> 'tpl',
    variant  = content -> 'mathObject' -> 'params' ->> 'variant'
WHERE
    (template IS NULL OR variant IS NULL)
    AND content -> 'mathObject' -> 'params' ->> 'tpl' IS NOT NULL;
