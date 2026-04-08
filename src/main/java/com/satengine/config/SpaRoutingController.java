package com.satengine.config;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * Forwards all /app/** routes to the React SPA index.html so that React Router
 * handles client-side navigation (deep links, browser refresh, etc.).
 *
 * Any request to /app/* that doesn't match a static file is forwarded to the
 * React entry point, which is served from static/app/index.html.
 */
@Controller
public class SpaRoutingController {

    @GetMapping({"/app", "/app/"})
    public String appRoot() {
        return "forward:/app/index.html";
    }

    // Catch-all for /app/practice, /app/session/*, etc.
    @GetMapping("/app/{path:[^\\.]*}")
    public String appPath() {
        return "forward:/app/index.html";
    }

    @GetMapping("/app/{path:[^\\.]*}/{sub:[^\\.]*}")
    public String appSubPath() {
        return "forward:/app/index.html";
    }
}
