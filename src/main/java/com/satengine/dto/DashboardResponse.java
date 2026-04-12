package com.satengine.dto;

import java.util.List;
import java.util.Map;

/**
 * Response for GET /api/dashboard
 * Contains stats cards + recent sessions list + per-domain accuracy.
 */
public record DashboardResponse(
        long sessionsCompleted,
        long questionsAnswered,
        Integer accuracyPct,                    // null if no answers yet
        Integer avgTimeSeconds,                 // null if no answers yet
        List<RecentSession> recentSessions,
        Map<String, Integer> domainAccuracy     // domain → accuracy pct (0-100)
) {
    public record RecentSession(
            String id,
            String section,
            int questionsAnswered,
            int correctCount,
            Integer accuracyPct,
            String startedAt
    ) {}
}
