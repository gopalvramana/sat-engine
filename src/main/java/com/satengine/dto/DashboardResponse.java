package com.satengine.dto;

import java.util.List;

/**
 * Response for GET /api/dashboard
 * Contains stats cards + recent sessions list.
 */
public record DashboardResponse(
        long sessionsCompleted,
        long questionsAnswered,
        Integer accuracyPct,        // null if no answers yet
        Integer avgTimeSeconds,     // null if no answers yet
        List<RecentSession> recentSessions
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
