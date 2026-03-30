package com.satengine.pipeline.claude;

import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.models.messages.Message;
import com.anthropic.models.messages.MessageCreateParams;
import io.github.cdimascio.dotenv.Dotenv;
import io.github.cdimascio.dotenv.DotenvException;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class ClaudeClient {

    private AnthropicClient client;

    @PostConstruct
    public void init() {
        // Load .env file if present
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
            // .env not present or malformed
        }

        String apiKey = null;
        // Resolution order: Spring property → env var → system property (dotenv sets this)
        log.info("Initializing ClaudeClient...");
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
