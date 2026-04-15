package com.satengine.config;

import com.satengine.domain.user.User;
import com.satengine.domain.user.UserService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Slf4j
@Component
@RequiredArgsConstructor
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final UserService userService;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request,
                                        HttpServletResponse response,
                                        Authentication authentication) throws IOException {
        OAuth2User oauth2User = (OAuth2User) authentication.getPrincipal();

        String email   = oauth2User.getAttribute("email");
        String name    = oauth2User.getAttribute("name");
        String picture = oauth2User.getAttribute("picture");

        User user = userService.findOrCreate(email, name, picture);

        // Store user ID and role in the HTTP session
        var session = request.getSession(true);
        session.setAttribute("userId",   user.getId().toString());
        session.setAttribute("userRole", user.getRole());

        log.info("OAuth2 login: {} ({}) role={}", email, user.getId(), user.getRole());

        response.sendRedirect(user.getRole().equals("ADMIN") ? "/admin/pipeline.html" : "/app/");
    }
}
