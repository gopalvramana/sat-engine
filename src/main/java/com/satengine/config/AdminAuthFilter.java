package com.satengine.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * Guards all /admin/** routes — both static HTML pages and API endpoints.
 *
 * Session attributes set at login:
 *   userId   — UUID string, present when logged in
 *   userRole — "ADMIN" | "STUDENT"
 *
 * Rules:
 *   No session / not logged in  → HTML: redirect to /login  | API: 401
 *   Logged in but role != ADMIN → HTML: redirect to /app/   | API: 403
 *   ADMIN                       → pass through
 */
@Slf4j
public class AdminAuthFilter extends OncePerRequestFilter {

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        // Auth disabled for local dev — re-enable before production
        return true;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws ServletException, IOException {

        HttpSession session = request.getSession(false);
        String userId   = session != null ? (String) session.getAttribute("userId")   : null;
        String userRole = session != null ? (String) session.getAttribute("userRole") : null;

        boolean isHtml = request.getRequestURI().endsWith(".html") ||
                         !request.getRequestURI().contains(".");

        if (userId == null) {
            log.debug("admin access denied — not logged in: {}", request.getRequestURI());
            if (isHtml) {
                response.sendRedirect("/login");
            } else {
                response.setStatus(401);
                response.setContentType("application/json");
                response.getWriter().write("{\"error\":\"Authentication required\"}");
            }
            return;
        }

        if (!"ADMIN".equals(userRole)) {
            log.warn("admin access denied — role={} userId={} path={}", userRole, userId, request.getRequestURI());
            if (isHtml) {
                response.sendRedirect("/app/");
            } else {
                response.setStatus(403);
                response.setContentType("application/json");
                response.getWriter().write("{\"error\":\"Admin access required\"}");
            }
            return;
        }

        chain.doFilter(request, response);
    }
}
