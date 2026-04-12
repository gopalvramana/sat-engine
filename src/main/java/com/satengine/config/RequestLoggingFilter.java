package com.satengine.config;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.UUID;

@Slf4j
@Component
public class RequestLoggingFilter implements Filter {

    @Override
    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse,
                         FilterChain chain) throws IOException, ServletException {

        HttpServletRequest  req  = (HttpServletRequest)  servletRequest;
        HttpServletResponse resp = (HttpServletResponse) servletResponse;

        String path   = req.getRequestURI();
        String method = req.getMethod();

        // Skip static assets — no MDC, no logging
        if (isStaticAsset(path)) {
            chain.doFilter(servletRequest, servletResponse);
            return;
        }

        String reqId  = UUID.randomUUID().toString().substring(0, 8);
        String userId = resolveUserId(req);

        MDC.put("reqId",  reqId);
        MDC.put("method", method);
        MDC.put("path",   path);
        MDC.put("userId", userId);

        log.info("→ {} {} user={} reqId={}", method, path, userId, reqId);
        long startMs = System.currentTimeMillis();

        try {
            chain.doFilter(servletRequest, servletResponse);
        } finally {
            long durationMs = System.currentTimeMillis() - startMs;
            int  status     = resp.getStatus();
            log.info("← {} {} {} {}ms reqId={}", method, path, status, durationMs, reqId);
            MDC.clear();
        }
    }

    private boolean isStaticAsset(String path) {
        if (path.contains("/assets/")) return true;
        return path.endsWith(".js")
            || path.endsWith(".css")
            || path.endsWith(".html")
            || path.endsWith(".ico")
            || path.endsWith(".png");
    }

    private String resolveUserId(HttpServletRequest req) {
        try {
            Object attr = req.getSession(false) != null
                    ? req.getSession(false).getAttribute("userId")
                    : null;
            return attr != null ? attr.toString() : "anon";
        } catch (Exception e) {
            return "anon";
        }
    }
}
