package com.satengine.dto;

import java.util.List;

/**
 * Response for GET /api/analytics.
 */
public record AnalyticsResponse(
        long    totalQuestions,
        Integer accuracyPct,        // null if no answers
        Integer difficultyPct,      // (avgDifficulty-1)/2*100, null if no answers
        Integer avgTimeSeconds,     // null if no answers
        Last24hStat last24h,        // stats for the trailing 24 h window
        List<DomainStat> domains,
        List<DayStat>    dailyActivity,   // last 30 days, sorted oldest→newest
        List<RecentSession> recentSessions  // last 5 sessions with ≥1 answer
) {
    public record DomainStat(
            String  domain,
            String  section,        // "math" or "reading_writing"
            int     total,
            int     correct,
            int     accuracyPct,
            Integer avgTimeSeconds
    ) {}

    public record DayStat(
            String date,        // "YYYY-MM-DD"
            int    questions
    ) {}

    /** Questions / accuracy / difficulty for the last 24 hours. */
    public record Last24hStat(
            int     questions,
            Integer accuracyPct,
            Integer difficultyPct
    ) {}

    /** Summary of a single session for the "recently completed" list. */
    public record RecentSession(
            String  sessionId,
            String  sessionType,    // e.g. "study", "practice_test"
            String  section,        // "math" or "reading_writing"
            String  startedAt,      // ISO-8601 string
            int     total,
            int     correct,
            Integer accuracyPct
    ) {}
}
