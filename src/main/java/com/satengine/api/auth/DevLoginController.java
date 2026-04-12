package com.satengine.api.auth;

import com.satengine.domain.user.User;
import com.satengine.domain.user.UserService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * LOCAL DEV ONLY — does not exist on Railway (production).
 *
 * POST /dev/login  →  creates/reuses dev@satengine.local, sets session, returns user JSON.
 * The login.html page calls this on localhost so developers can test without Google OAuth.
 */
@Slf4j
@Profile("local")
@RestController
@RequestMapping("/dev")
@RequiredArgsConstructor
public class DevLoginController {

    private final UserService userService;

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> devLogin(HttpSession session) {
        User user = userService.findOrCreate(
                "dev@satengine.local",
                "Dev User",
                null
        );
        session.setAttribute("userId", user.getId().toString());
        log.info("Dev login: {} session={}", user.getEmail(), session.getId());
        return ResponseEntity.ok(AuthController.toMap(user));
    }
}
