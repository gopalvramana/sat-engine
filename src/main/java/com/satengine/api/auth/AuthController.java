package com.satengine.api.auth;

import com.satengine.domain.user.User;
import com.satengine.domain.user.UserRepository;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserRepository userRepository;

    /**
     * GET /api/auth/me
     * Returns the logged-in user's profile, or 401 if no session exists.
     * Called by the frontend on every page load to populate AuthContext.
     */
    @GetMapping("/me")
    public ResponseEntity<Map<String, Object>> me(HttpSession session) {
        String userIdStr = (String) session.getAttribute("userId");
        if (userIdStr == null) {
            return ResponseEntity.status(401).build();
        }

        return userRepository.findById(UUID.fromString(userIdStr))
                .<ResponseEntity<Map<String, Object>>>map(user -> ResponseEntity.ok(toMap(user)))
                .orElse(ResponseEntity.status(401).build());
    }

    // ── helpers ────────────────────────────────────────────────────────────

    static Map<String, Object> toMap(User u) {
        return Map.of(
                "id",      u.getId().toString(),
                "email",   u.getEmail(),
                "name",    u.getName() != null    ? u.getName()    : "",
                "picture", u.getPicture() != null ? u.getPicture() : ""
        );
    }
}
