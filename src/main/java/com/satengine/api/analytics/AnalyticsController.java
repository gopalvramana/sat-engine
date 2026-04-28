package com.satengine.api.analytics;

import com.satengine.domain.session.SessionService;
import com.satengine.dto.AnalyticsResponse;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/analytics")
@RequiredArgsConstructor
public class AnalyticsController {

    private final SessionService sessionService;

    @GetMapping
    public ResponseEntity<AnalyticsResponse> getAnalytics(HttpSession httpSession) {
        String userIdStr = (String) httpSession.getAttribute("userId");
        if (userIdStr == null) return ResponseEntity.status(401).build();
        UUID userId;
        try { userId = UUID.fromString(userIdStr); }
        catch (IllegalArgumentException e) { return ResponseEntity.status(401).build(); }
        AnalyticsResponse resp = sessionService.getAnalytics(userId);
        log.info("analytics userId={} total={}", userId, resp.totalQuestions());
        return ResponseEntity.ok(resp);
    }
}
