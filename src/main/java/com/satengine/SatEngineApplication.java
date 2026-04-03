package com.satengine;

import io.github.cdimascio.dotenv.Dotenv;
import io.github.cdimascio.dotenv.DotenvException;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.WebApplicationType;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.util.Arrays;

@SpringBootApplication
public class SatEngineApplication {

    public static void main(String[] args) {
        // Load .env file if present (silently ignored if missing in production)
        try {
            Dotenv dotenv = Dotenv.configure()
                    .ignoreIfMissing()
                    .load();
            dotenv.entries().forEach(e -> {
                if (System.getenv(e.getKey()) == null) {
                    System.setProperty(e.getKey(), e.getValue());
                }
            });
        } catch (DotenvException ex) {
            // .env not present or malformed — rely on environment variables
        }

        SpringApplication app = new SpringApplication(SatEngineApplication.class);

        // Pipeline jobs don't need a web server — skip Tomcat entirely to avoid
        // port conflicts and reduce startup time.
        boolean isPipelineJob = Arrays.stream(args).anyMatch(a -> a.startsWith("--job="));
        if (isPipelineJob) {
            app.setWebApplicationType(WebApplicationType.NONE);
        }

        app.run(args);
    }
}
