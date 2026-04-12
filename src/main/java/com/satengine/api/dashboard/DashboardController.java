package com.satengine.api.dashboard;

import com.satengine.domain.session.SessionService;
import com.satengine.dto.DashboardResponse;
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
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final SessionService sessionService;

    /**
     * GET /api/dashboard
     * Returns stats cards + recent sessions for the logged-in user.
     * Returns 401 if no session exists.
     */
    @GetMapping
    public ResponseEntity<DashboardResponse> getDashboard(HttpSession httpSession) {
        String userIdStr = (String) httpSession.getAttribute("userId");
        if (userIdStr == null) {
            log.debug("dashboard — no session");
            return ResponseEntity.status(401).build();
        }
        try {
            UUID userId = UUID.fromString(userIdStr);
            DashboardResponse resp = sessionService.getDashboard(userId);
            log.info("dashboard requested userId={}", userId);
            return ResponseEntity.ok(resp);
        } catch (Exception e) {
            log.debug("dashboard — no session (invalid userId)");
            return ResponseEntity.status(401).build();
        }
    }
}
