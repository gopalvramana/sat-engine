package com.satengine.api.skill;

import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Serves static skill-content JSON files from classpath:/skill-content/{skillKey}.json.
 * No DB involved — content is bundled with the jar.
 */
@RestController
@RequestMapping("/api/skills")
public class SkillContentController {

    @GetMapping("/{skillKey}/content")
    public ResponseEntity<String> getContent(@PathVariable String skillKey) {
        // Only allow safe keys: lowercase letters, digits, underscores (max 60 chars)
        if (!skillKey.matches("[a-z0-9_]{1,60}")) {
            return ResponseEntity.badRequest().build();
        }

        String path = "/skill-content/" + skillKey + ".json";
        try (InputStream is = getClass().getResourceAsStream(path)) {
            if (is == null) {
                return ResponseEntity.notFound().build();
            }
            String body = new String(is.readAllBytes(), StandardCharsets.UTF_8);
            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(body);
        } catch (IOException e) {
            return ResponseEntity.internalServerError().build();
        }
    }
}
