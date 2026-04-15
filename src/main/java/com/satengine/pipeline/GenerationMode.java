package com.satengine.pipeline;

/**
 * Controls which pool questions are generated for and which difficulty weights are used.
 *
 * DRILL      — default pool; uses DIFFICULTY_WEIGHTS (skewed hard); saves pool='both'
 * DIAGNOSTIC — d3-d4 only; picks skills globally to ensure 3-per-skill coverage; saves pool='diagnostic'
 * TEST       — SAT-realistic weights; saves pool='test'
 */
public enum GenerationMode {
    DRILL,
    DIAGNOSTIC,
    TEST
}
