package com.satengine.api.errorlog;

import com.satengine.domain.session.SessionService;
import com.satengine.dto.ErrorLogItem;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping("/api/error-log")
@RequiredArgsConstructor
public class ErrorLogController {

    private final SessionService sessionService;

    @GetMapping
    public ResponseEntity<List<ErrorLogItem>> getErrorLog(HttpSession httpSession) {
        String userIdStr = (String) httpSession.getAttribute("userId");
        if (userIdStr == null) return ResponseEntity.status(401).build();
        UUID userId;
        try { userId = UUID.fromString(userIdStr); }
        catch (IllegalArgumentException e) { return ResponseEntity.status(401).build(); }
        List<ErrorLogItem> items = sessionService.getErrorLog(userId);
        log.info("error-log userId={} items={}", userId, items.size());
        return ResponseEntity.ok(items);
    }
}
