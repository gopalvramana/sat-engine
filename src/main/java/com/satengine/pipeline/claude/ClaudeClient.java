package com.satengine.pipeline.claude;

import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.models.messages.Message;
import com.anthropic.models.messages.MessageCreateParams;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class ClaudeClient {

    private AnthropicClient client;

    @PostConstruct
    public void init() {
        // Try several candidate directories for .env — stop at first that sets the key
        String[] candidates = {".", "sat-engine", "../sat-engine"};
        for (String dir : candidates) {
            loadDotenv(dir);
            String loaded = System.getProperty("ANTHROPIC_API_KEY", "");
            if (!loaded.isBlank()) break;
        }
        // Final fallback: parent directory of the JAR (handles any layout)
        if (System.getProperty("ANTHROPIC_API_KEY", "").isBlank()) {
            try {
                String jarPath = ClaudeClient.class.getProtectionDomain()
                        .getCodeSource().getLocation().toURI().getPath();
                java.nio.file.Path jarDir = java.nio.file.Paths.get(jarPath).getParent();
                if (jarDir != null && jarDir.getParent() != null) {
                    loadDotenv(jarDir.getParent().toString());
                }
            } catch (Exception ex) {
                log.debug("JAR path .env lookup failed: {}", ex.getMessage());
            }
        }

        String apiKey = null;
        // Resolution order: Spring property → env var → system property (dotenv sets this)
        log.info("Initializing ClaudeClient...");
        log.info("user.dir: {}", System.getProperty("user.dir"));
        apiKey = System.getenv("ANTHROPIC_API_KEY");
        log.info("apiKey from getenv: '{}'", apiKey);
        if (apiKey == null || apiKey.isBlank()) {
            apiKey = System.getProperty("ANTHROPIC_API_KEY");
            log.info("apiKey from getProperty: '{}'", apiKey);
        }
        if (apiKey == null || apiKey.isBlank()) {
            // Not required for --load-batch or API-only mode — defer error to first actual call
            log.warn("ANTHROPIC_API_KEY is not set — pipeline jobs will fail if invoked");
            return;
        }
        client = AnthropicOkHttpClient.builder()
                .apiKey(apiKey)
                .build();
        log.info("ClaudeClient initialised");
    }

    /**
     * Call Claude with a system prompt + user message. Returns the text content of the first response block.
     */
    public String call(String model, int maxTokens, String systemPrompt, String userMessage) {
        return call(model, maxTokens, systemPrompt, userMessage, null);
    }

    /** Read .env file directly so system env blank values cannot shadow file values. */
    private void loadDotenv(String directory) {
        java.nio.file.Path envFile = java.nio.file.Paths.get(directory, ".env");
        if (!java.nio.file.Files.exists(envFile)) return;
        log.info("Loading .env from: {}", envFile.toAbsolutePath());
        try {
            java.nio.file.Files.lines(envFile).forEach(line -> {
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) return;
                int eq = line.indexOf('=');
                if (eq <= 0) return;
                String key = line.substring(0, eq).trim();
                String val = line.substring(eq + 1).trim();
                if (val.length() >= 2 && val.charAt(0) == '"' && val.charAt(val.length() - 1) == '"')
                    val = val.substring(1, val.length() - 1);
                if (!val.isBlank()) {
                    String envVal = System.getenv(key);
                    if (envVal == null || envVal.isBlank()) {
                        System.setProperty(key, val);
                        log.info("Set system property {} from .env", key);
                    }
                }
            });
        } catch (Exception ex) {
            log.warn("Failed to read .env from {}: {}", directory, ex.getMessage());
        }
    }

    public String call(String model, int maxTokens, String systemPrompt, String userMessage, Double temperature) {
        MessageCreateParams.Builder builder = MessageCreateParams.builder()
                .model(model)
                .maxTokens((long) maxTokens)
                .system(systemPrompt)
                .addUserMessage(userMessage);
        if (temperature != null) {
            builder.temperature(temperature);
        }
        Message message = client.messages().create(builder.build());
        return message.content().get(0).asText().text();
    }
}
