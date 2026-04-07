package com.satengine.pipeline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

/**
 * Validates animation quality for all geometry questions that have frames.
 *
 * Checks (mirrors visual-check-animations.js exactly):
 *   1. MISSING_VERTEX_LABELS — frame 0 missing A/B/C text labels
 *   2. COORD_MISMATCH        — polygon points don't match diagram vertices
 *   3. SIDE_LABEL_OVERLAP    — side_label text box overlaps its segment
 *   4. OUT_OF_BOUNDS         — elements outside the canvas rectangle
 *   5. ARC_TEXT_OVERLAP      — unlabelled arc with nearby multi-char angle text
 *
 * Usage (via PipelineRunner):
 *   java -jar sat-engine.jar --job=visual-check
 *   java -jar sat-engine.jar --job=visual-check --fix
 *   java -jar sat-engine.jar --job=visual-check --id=MATH-GEO-004
 *   java -jar sat-engine.jar --job=visual-check --fix --id=MATH-GEO-004
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class VisualCheckStage {

    private final QuestionRepository questionRepository;
    private final ObjectMapper        objectMapper;

    // ── Public entry points ─────────────────────────────────────────────────

    public void run(boolean fix, String onlyId) {
        List<Question> queue = onlyId != null
                ? questionRepository.findByExternalId(onlyId).map(List::of).orElse(List.of())
                : questionRepository.findAllAnimationEligible();

        queue = queue.stream()
                .filter(q -> {
                    try {
                        JsonNode anim = parseJson(q.getAnimation());
                        return anim != null && anim.path("frames").isArray()
                                && anim.path("frames").size() > 0;
                    } catch (Exception e) { return false; }
                }).toList();

        if (queue.isEmpty()) {
            log.info("Visual check: no animated questions found.");
            return;
        }

        String mode = fix ? "CHECK + FIX" : "CHECK";
        log.info("╔══════════════════════════════════════════════════════╗");
        log.info("║  SatEngine — Animation Visual Check                  ║");
        log.info("║  mode: {}{}  questions: {}",
                mode, " ".repeat(Math.max(0, 14 - mode.length())), queue.size());
        log.info("╚══════════════════════════════════════════════════════╝");
        log.info("");

        int passed = 0, totalIssues = 0, fixed = 0;

        for (Question q : queue) {
            List<Issue> issues = checkAnimation(q);
            String label = padEnd(q.getExternalId(), 20);

            if (issues.isEmpty()) {
                log.info("{}  ✅ PASS", label);
                passed++;
            } else {
                long errors = issues.stream().filter(i -> i.severity == Severity.ERROR).count();
                long warns  = issues.stream().filter(i -> i.severity == Severity.WARN).count();
                log.info("{}  ⚠️  {} error(s), {} warn(s)", label, errors, warns);
                for (Issue iss : issues) {
                    String icon = iss.severity == Severity.ERROR ? "🔴" : "🟡";
                    log.info("       {} [{}] {}", icon, iss.type, iss.detail);
                }
                totalIssues += issues.size();

                if (fix) {
                    boolean didFix = applyFix(q, issues);
                    if (didFix) {
                        log.info("       ✔ patched");
                        fixed++;
                    }
                }
            }
        }

        log.info("");
        log.info("────────────────────────────────────────────────────────");
        log.info("Passed: {}/{}  |  Issues found: {}  |  Fixed: {}",
                passed, queue.size(), totalIssues, fixed);
        if (!fix && totalIssues > 0) {
            log.info("Run with --fix to auto-patch fixable issues.");
        }
    }

    // ── Checks ───────────────────────────────────────────────────────────────

    private List<Issue> checkAnimation(Question q) {
        List<Issue> issues = new ArrayList<>();

        JsonNode anim     = parseJson(q.getAnimation());
        JsonNode diagJson = parseJson(q.getDiagram());
        if (anim == null) return issues;

        JsonNode frames   = anim.path("frames");
        int W = anim.path("width").asInt(280);
        int H = anim.path("height").asInt(260);

        // Diagram vertex map: name → {x, y}
        Map<String, int[]> vertices = extractVertices(diagJson);
        List<String> vertexNames = new ArrayList<>(vertices.keySet());

        // ── 1. MISSING_VERTEX_LABELS ─────────────────────────────────────────
        if (!vertexNames.isEmpty()) {
            JsonNode frame0 = frames.get(0);
            Set<String> labeled = new HashSet<>();
            for (JsonNode el : frame0.path("elements")) {
                if ("text".equals(el.path("type").asText())
                        && vertexNames.contains(el.path("text").asText())) {
                    labeled.add(el.path("text").asText());
                }
            }
            List<String> missing = vertexNames.stream().filter(v -> !labeled.contains(v)).toList();
            if (!missing.isEmpty()) {
                issues.add(new Issue(
                        Severity.ERROR, "MISSING_VERTEX_LABELS",
                        "Frame 0 missing vertex labels: " + String.join(", ", missing),
                        Map.of("missingVertices", missing, "vertices", vertices,
                               "canvasW", W, "canvasH", H)
                ));
            }
        }

        // ── 2. COORD_MISMATCH ────────────────────────────────────────────────
        if (!vertexNames.isEmpty()) {
            JsonNode frame0els = frames.get(0).path("elements");
            for (JsonNode el : frame0els) {
                if (!"polygon".equals(el.path("type").asText())) continue;
                List<double[]> polyPts = new ArrayList<>();
                for (JsonNode pt : el.path("points")) {
                    polyPts.add(new double[]{ pt.get(0).asDouble(), pt.get(1).asDouble() });
                }
                for (String name : vertexNames) {
                    int[] dv = vertices.get(name);
                    boolean close = polyPts.stream().anyMatch(pp ->
                            Math.hypot(pp[0] - dv[0], pp[1] - dv[1]) < 3);
                    if (!close) {
                        issues.add(new Issue(
                                Severity.WARN, "COORD_MISMATCH",
                                "Polygon missing diagram vertex " + name +
                                " (" + dv[0] + "," + dv[1] + ") — animation may not match question diagram",
                                Map.of()
                        ));
                        break;
                    }
                }
                break; // check first polygon only
            }
        }

        // ── 3. SIDE_LABEL_OVERLAP ────────────────────────────────────────────
        for (int fi = 0; fi < frames.size(); fi++) {
            for (JsonNode el : frames.get(fi).path("elements")) {
                if (!"side_label".equals(el.path("type").asText())) continue;
                double[] p1 = arr2(el.path("p1"));
                double[] p2 = arr2(el.path("p2"));
                double[] pos = sideLabelPos(el);
                String text = el.path("text").asText("");
                int fs = el.path("fontSize").asInt(13);
                double hw = textWidth(text, fs) / 2;
                double hh = fs * 0.5;
                double overlap = textBoxOverlapsSegment(pos[0], pos[1], hw, hh,
                        p1[0], p1[1], p2[0], p2[1]);
                if (overlap > 2) {
                    boolean isVertical = Math.abs(p1[0] - p2[0]) < 3;
                    int safeOffset = isVertical ? 38 : 26;
                    issues.add(new Issue(
                            Severity.ERROR, "SIDE_LABEL_OVERLAP",
                            String.format("Frame %d side_label \"%s\" overlaps segment (overlap≈%.1fpx). Increase offset to %d.",
                                    fi, text, overlap, safeOffset),
                            Map.of("frameIdx", fi, "elementText", text, "suggestedOffset", safeOffset)
                    ));
                }
            }
        }

        // ── 4. OUT_OF_BOUNDS ─────────────────────────────────────────────────
        final int PAD = 5;
        for (int fi = 0; fi < frames.size(); fi++) {
            outer:
            for (JsonNode el : frames.get(fi).path("elements")) {
                String type = el.path("type").asText();
                List<double[]> pts = new ArrayList<>();
                switch (type) {
                    case "polygon" -> {
                        for (JsonNode pt : el.path("points"))
                            pts.add(new double[]{ pt.get(0).asDouble(), pt.get(1).asDouble() });
                    }
                    case "dot"  -> pts.add(new double[]{ el.path("x").asDouble(), el.path("y").asDouble() });
                    case "text" -> pts.add(new double[]{ el.path("x").asDouble(), el.path("y").asDouble() });
                    case "side_label" -> { double[] p = sideLabelPos(el); pts.add(p); }
                }
                for (double[] pt : pts) {
                    if (pt[0] < -PAD || pt[0] > W + PAD || pt[1] < -PAD || pt[1] > H + PAD) {
                        String label = type + (el.has("text") ? " \"" + el.path("text").asText() + "\"" : "");
                        issues.add(new Issue(
                                Severity.WARN, "OUT_OF_BOUNDS",
                                String.format("Frame %d element \"%s\" at (%.1f,%.1f) outside canvas %dx%d",
                                        fi, label, pt[0], pt[1], W, H),
                                Map.of()
                        ));
                        continue outer;
                    }
                }
            }
        }

        // ── 5. ARC_TEXT_OVERLAP ──────────────────────────────────────────────
        for (int fi = 0; fi < frames.size(); fi++) {
            List<JsonNode> els = new ArrayList<>();
            for (JsonNode el : frames.get(fi).path("elements")) els.add(el);
            for (JsonNode el : els) {
                if (!"arc".equals(el.path("type").asText())) continue;
                if (!el.path("label").isMissingNode() && !el.path("label").asText("").isEmpty()) continue;
                double arcX = el.path("cx").asDouble();
                double arcY = el.path("cy").asDouble();
                double arcR = el.path("r").asDouble(20);
                for (JsonNode t : els) {
                    if (!"text".equals(t.path("type").asText())) continue;
                    String txt = t.path("text").asText("").trim();
                    if (txt.length() <= 1 || txt.matches("[A-Z]")) continue; // skip vertex labels
                    double dist = Math.hypot(t.path("x").asDouble() - arcX,
                                            t.path("y").asDouble() - arcY);
                    if (dist < arcR * 2.0) {
                        issues.add(new Issue(
                                Severity.WARN, "ARC_TEXT_OVERLAP",
                                String.format("Frame %d arc at (%.0f,%.0f) has no \"label\" field but nearby angle text \"%s\" — move to arc.label",
                                        fi, arcX, arcY, txt),
                                Map.of()
                        ));
                        break;
                    }
                }
            }
        }

        return issues;
    }

    // ── Auto-fix ─────────────────────────────────────────────────────────────

    @Transactional
    boolean applyFix(Question q, List<Issue> issues) {
        try {
            JsonNode animNode = parseJson(q.getAnimation());
            if (animNode == null) return false;
            // Deep-clone via re-serialise
            ObjectNode anim = (ObjectNode) objectMapper.readTree(objectMapper.writeValueAsString(animNode));
            ArrayNode frames = (ArrayNode) anim.path("frames");
            boolean changed = false;

            for (Issue issue : issues) {

                // Fix 1: add missing vertex labels to all frames
                if ("MISSING_VERTEX_LABELS".equals(issue.type)) {
                    @SuppressWarnings("unchecked")
                    List<String> missing = (List<String>) issue.data.get("missingVertices");
                    @SuppressWarnings("unchecked")
                    Map<String, int[]> verts = (Map<String, int[]>) issue.data.get("vertices");
                    int cW = (int) issue.data.get("canvasW");
                    int cH = (int) issue.data.get("canvasH");
                    double[] centroid = computeCentroid(verts);

                    List<ObjectNode> newLabels = new ArrayList<>();
                    for (String name : missing) {
                        int[] v = verts.get(name);
                        double ddx = v[0] - centroid[0], ddy = v[1] - centroid[1];
                        double dlen = Math.max(Math.hypot(ddx, ddy), 1);
                        int lx = (int) Math.round(v[0] + (ddx / dlen) * 16);
                        int ly = (int) Math.round(v[1] + (ddy / dlen) * 16);
                        lx = Math.max(12, Math.min(lx, cW - 12));
                        ly = Math.max(12, Math.min(ly, cH - 12));
                        ObjectNode lbl = objectMapper.createObjectNode();
                        lbl.put("type", "text").put("x", lx).put("y", ly)
                           .put("text", name).put("fontSize", 13)
                           .put("color", "#1e293b").put("bold", true).put("anchor", "middle");
                        newLabels.add(lbl);
                    }

                    for (JsonNode frameNode : frames) {
                        ArrayNode els = (ArrayNode) frameNode.path("elements");
                        Set<String> existing = new HashSet<>();
                        int insertPos = 0;
                        for (int i = 0; i < els.size(); i++) {
                            String t = els.get(i).path("type").asText();
                            if ("text".equals(t)) existing.add(els.get(i).path("text").asText());
                            if ("dot".equals(t) || "polygon".equals(t)) insertPos = i + 1;
                        }
                        for (ObjectNode lbl : newLabels) {
                            if (!existing.contains(lbl.path("text").asText())) {
                                // Insert at insertPos
                                ArrayNode newEls = objectMapper.createArrayNode();
                                for (int i = 0; i < insertPos; i++) newEls.add(els.get(i));
                                newEls.add(lbl);
                                for (int i = insertPos; i < els.size(); i++) newEls.add(els.get(i));
                                ((ObjectNode) frameNode).set("elements", newEls);
                                insertPos++;
                                changed = true;
                            }
                        }
                    }
                }

                // Fix 2: increase offset on overlapping side labels
                if ("SIDE_LABEL_OVERLAP".equals(issue.type)) {
                    String targetText = (String) issue.data.get("elementText");
                    int suggested = (int) issue.data.get("suggestedOffset");
                    for (JsonNode frameNode : frames) {
                        for (JsonNode el : frameNode.path("elements")) {
                            if ("side_label".equals(el.path("type").asText())
                                    && targetText.equals(el.path("text").asText())) {
                                if (el.path("offset").asInt(0) < suggested) {
                                    ((ObjectNode) el).put("offset", suggested);
                                    changed = true;
                                }
                            }
                        }
                    }
                }
            }

            if (!changed) return false;
            q.setAnimation(objectMapper.writeValueAsString(anim));
            questionRepository.save(q);
            return true;

        } catch (Exception e) {
            log.error("Fix failed for {}: {}", q.getExternalId(), e.getMessage());
            return false;
        }
    }

    // ── Math helpers (exact mirrors of visual-check-animations.js) ────────────

    /** Approximate rendered text width in px. */
    private double textWidth(String text, int fontSize) {
        return (text == null ? 0 : text.length()) * fontSize * 0.55;
    }

    /**
     * Compute the rendered centre position of a side_label element.
     * Mirrors sideLabelPos() in visual-check-animations.js.
     */
    private double[] sideLabelPos(JsonNode el) {
        double[] p1 = arr2(el.path("p1"));
        double[] p2 = arr2(el.path("p2"));
        double mx = (p1[0] + p2[0]) / 2, my = (p1[1] + p2[1]) / 2;

        JsonNode awf = el.path("awayFrom");
        double ax = awf.isArray() ? awf.get(0).asDouble() : mx;
        double ay = awf.isArray() ? awf.get(1).asDouble() : my;

        double dx = mx - ax, dy = my - ay;
        double len = Math.hypot(dx, dy);
        if (len < 1e-9) len = 1;
        dx /= len; dy /= len;

        int    fs  = el.path("fontSize").asInt(13);
        String txt = el.path("text").asText("");
        double htw = textWidth(txt, fs) / 2;
        double hth = fs * 0.5;

        // Capped auto-offset — identical to renderer.js formula
        double minX = Math.abs(dx) > 0.15 ? Math.min((htw + 5) / Math.abs(dx), htw + 8) : 0;
        double minY = Math.abs(dy) > 0.15 ? Math.min((hth + 4) / Math.abs(dy), hth + 6) : 0;
        double off  = Math.max(el.path("offset").asDouble(18), Math.max(minX, minY));

        return new double[]{ mx + dx * off, my + dy * off };
    }

    /**
     * Signed distance from point (px,py) to segment (x1,y1)→(x2,y2).
     */
    private double distPointToSegment(double px, double py,
                                      double x1, double y1, double x2, double y2) {
        double sdx = x2 - x1, sdy = y2 - y1;
        double len = Math.hypot(sdx, sdy);
        if (len < 1e-9) return Math.hypot(px - x1, py - y1);
        return Math.abs((sdy * px - sdx * py + x2 * y1 - y2 * x1) / len);
    }

    /**
     * Returns overlap distance (> 0 means text box overlaps the segment).
     */
    private double textBoxOverlapsSegment(double cx, double cy, double hw, double hh,
                                          double x1, double y1, double x2, double y2) {
        double d = distPointToSegment(cx, cy, x1, y1, x2, y2);
        double clearance = Math.hypot(hw, hh) * 0.7;
        return clearance - d;
    }

    /** Compute centroid from vertex map. Returns [cx, cy]. */
    private double[] computeCentroid(Map<String, int[]> vertices) {
        double sumX = 0, sumY = 0;
        for (int[] v : vertices.values()) { sumX += v[0]; sumY += v[1]; }
        int n = Math.max(vertices.size(), 1);
        return new double[]{ sumX / n, sumY / n };
    }

    /** Parse [x, y] array node into double[2]. */
    private double[] arr2(JsonNode node) {
        if (node.isArray() && node.size() >= 2)
            return new double[]{ node.get(0).asDouble(), node.get(1).asDouble() };
        return new double[]{ 0, 0 };
    }

    /** Extract vertices map from diagram JSON. Returns name → [x, y]. */
    private Map<String, int[]> extractVertices(JsonNode diagJson) {
        Map<String, int[]> result = new LinkedHashMap<>();
        if (diagJson == null) return result;
        JsonNode verts = diagJson.path("svgConfig").path("vertices");
        if (!verts.isObject()) return result;
        verts.fields().forEachRemaining(e -> result.put(
                e.getKey(),
                new int[]{ e.getValue().path("x").asInt(), e.getValue().path("y").asInt() }
        ));
        return result;
    }

    private JsonNode parseJson(String json) {
        if (json == null || json.isBlank()) return null;
        try { return objectMapper.readTree(json); }
        catch (Exception e) { return null; }
    }

    private String padEnd(String s, int len) {
        if (s == null) s = "";
        return s.length() >= len ? s : s + " ".repeat(len - s.length());
    }

    // ── Internal types ────────────────────────────────────────────────────────

    private enum Severity { ERROR, WARN }

    private record Issue(Severity severity, String type, String detail, Map<String, Object> data) {}
}
