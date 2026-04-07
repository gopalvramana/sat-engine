package com.satengine.pipeline;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.satengine.domain.question.Question;
import com.satengine.domain.question.QuestionRepository;
import com.satengine.pipeline.claude.ClaudeClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Generates step-by-step SVG animation frames for geometry/coordinate questions
 * that have animation.eligible=true but no frames yet.
 *
 * Stored in questions.animation as:
 * {
 *   "eligible": true,
 *   "width": 280,
 *   "height": 260,
 *   "frames": [
 *     { "caption": "...", "elements": [...] },
 *     ...
 *   ]
 * }
 *
 * Element types: polygon, line, right_angle, arc, dot, text, katex
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EnrichAnimationStage {

    private final QuestionRepository questionRepository;
    private final ClaudeClient        claudeClient;
    private final ObjectMapper        objectMapper;

    private static final String MODEL      = "claude-opus-4-5";
    private static final int    MAX_TOKENS = 4096;

    // ── Public entry points ─────────────────────────────────────────────────

    /** Backfill all eligible questions missing animation frames. */
    public int runBackfill() {
        List<Question> queue = questionRepository.findAnimationEligible();
        if (queue.isEmpty()) {
            log.info("Animation backfill: nothing to do.");
            return 0;
        }
        log.info("═".repeat(60));
        log.info(" EnrichAnimation  questions={}  model={}", queue.size(), MODEL);
        log.info("═".repeat(60));
        return processQueue(queue);
    }

    /** Re-enrich ALL eligible questions, even those that already have frames (force refresh). */
    public int runReenrichAll() {
        List<Question> queue = questionRepository.findAllAnimationEligible();
        if (queue.isEmpty()) {
            log.info("Animation re-enrich: no eligible questions found.");
            return 0;
        }
        log.info("═".repeat(60));
        log.info(" EnrichAnimation (re-enrich all)  questions={}  model={}", queue.size(), MODEL);
        log.info("═".repeat(60));
        return processQueue(queue);
    }

    /** Re-run on a single question by externalId (force re-generates frames). */
    public void runById(String externalId) {
        Question q = questionRepository.findByExternalId(externalId)
                .orElseThrow(() -> new IllegalArgumentException("Question not found: " + externalId));
        enrichOne(q, 1, 1);
    }

    /**
     * Called automatically by EnrichStage after pedagogy enrichment.
     * Generates animation frames only if:
     *   1. The question has a non-empty diagram (the real signal of visual content)
     *   2. animation.eligible = true (Claude's intent)
     *   3. No frames exist yet (skip already-animated questions)
     *
     * The diagram check prevents animating word problems that Claude incorrectly
     * marks eligible — if there is nothing to draw, there is no diagram.
     *
     * Returns true if frames were generated, false if skipped or failed.
     */
    public boolean enrichIfEligible(Question q) {
        // Guard 1: must have a diagram — word problems never do
        boolean hasDiagram = q.getDiagram() != null && !q.getDiagram().isBlank()
                && !q.getDiagram().equals("{}");
        if (!hasDiagram) return false;

        try {
            JsonNode anim = q.getAnimation() != null
                    ? objectMapper.readTree(q.getAnimation()) : null;
            boolean eligible = anim != null && anim.path("eligible").asBoolean(false);
            boolean hasFrames = anim != null && anim.path("frames").isArray()
                    && anim.path("frames").size() > 0;
            if (!eligible || hasFrames) return false;
        } catch (Exception e) {
            return false;
        }
        return enrichOne(q, 1, 1);
    }

    // ── Internal ────────────────────────────────────────────────────────────

    private int processQueue(List<Question> queue) {
        int done = 0, failed = 0;
        for (int i = 0; i < queue.size(); i++) {
            boolean ok = enrichOne(queue.get(i), i + 1, queue.size());
            if (ok) done++; else failed++;
            if (i < queue.size() - 1) {
                try { Thread.sleep(600); } catch (InterruptedException ignored) {}
            }
        }
        log.info("─".repeat(60));
        log.info(" Results: {} animated  {} failed", done, failed);
        return done;
    }

    private boolean enrichOne(Question q, int i, int total) {
        String label = padEnd(q.getExternalId(), 20);
        try {
            String prompt  = buildPrompt(q);
            String raw     = claudeClient.call(MODEL, MAX_TOKENS, "", prompt);
            String cleaned = raw.replaceAll("(?i)^```json\\s*", "").replaceAll("\\s*```$", "").strip();

            JsonNode result = objectMapper.readTree(cleaned);
            validate(result);

            save(q, objectMapper.writeValueAsString(result));
            int frameCount = result.path("frames").size();
            log.info("[{}/{}] {} done  ({} frames)", i, total, label, frameCount);
            return true;

        } catch (Exception e) {
            log.error("[{}/{}] {} FAILED: {}", i, total, label, e.getMessage());
            return false;
        }
    }

    private String buildPrompt(Question q) {
        StringBuilder sb = new StringBuilder();
        sb.append("You are generating a step-by-step SVG animation for an SAT math problem.\n\n");

        sb.append("QUESTION\n");
        sb.append("ExternalId: ").append(q.getExternalId()).append("\n");
        sb.append("Domain: ").append(q.getDomain()).append("\n");
        sb.append("Skill: ").append(q.getSkill()).append("\n");
        sb.append("Difficulty: ").append(q.getDifficulty()).append("/7\n");
        sb.append("Stem: ").append(q.getQuestionStem()).append("\n\n");

        // ── Extract canvas size + exact vertex coordinates from diagram ──────
        int canvasW = 280, canvasH = 260;
        StringBuilder vertexBlock = new StringBuilder();
        if (q.getDiagram() != null && !q.getDiagram().isBlank()) {
            try {
                JsonNode diag = objectMapper.readTree(q.getDiagram());
                JsonNode cfg  = diag.path("svgConfig");
                if (cfg.has("width"))  canvasW = cfg.path("width").asInt(280);
                if (cfg.has("height")) canvasH = cfg.path("height").asInt(260);
                final int fCanvasW = canvasW, fCanvasH = canvasH;
                JsonNode vertices = cfg.path("vertices");
                if (vertices.isObject() && !vertices.isEmpty()) {
                    double[] sumX = {0}, sumY = {0};
                    int[]    cnt  = {0};
                    vertices.fields().forEachRemaining(e -> {
                        sumX[0] += e.getValue().path("x").asDouble();
                        sumY[0] += e.getValue().path("y").asDouble();
                        cnt[0]++;
                    });
                    int centX = (int) Math.round(sumX[0] / cnt[0]);
                    int centY = (int) Math.round(sumY[0] / cnt[0]);

                    vertexBlock.append("DIAGRAM COORDINATES — USE THESE EXACT VALUES, DO NOT INVENT NEW ONES:\n");
                    vertexBlock.append("Canvas: ").append(canvasW).append("x").append(canvasH).append(" px\n");
                    vertexBlock.append("Vertices (use for polygon points AND vertex text labels):\n");
                    vertices.fields().forEachRemaining(e -> {
                        int vx = e.getValue().path("x").asInt();
                        int vy = e.getValue().path("y").asInt();
                        // compute label offset position (16px outward from centroid)
                        double ddx = vx - centX, ddy = vy - centY;
                        double dlen = Math.max(Math.sqrt(ddx*ddx + ddy*ddy), 1);
                        int lxRaw = (int) Math.round(vx + (ddx/dlen)*16);
                        int lyRaw = (int) Math.round(vy + (ddy/dlen)*16);
                        // clamp to canvas
                        int lx = Math.max(12, Math.min(lxRaw, fCanvasW - 12));
                        int ly = Math.max(12, Math.min(lyRaw, fCanvasH - 12));
                        vertexBlock.append("  ").append(e.getKey())
                                   .append(": polygon point=(").append(vx).append(",").append(vy).append(")")
                                   .append("  label pos=(").append(lx).append(",").append(ly).append(")\n");
                    });
                    vertexBlock.append("Centroid (use as awayFrom for side_label): (")
                               .append(centX).append(",").append(centY).append(")\n");
                }
            } catch (Exception ignored) {}
        }
        if (!vertexBlock.isEmpty()) {
            sb.append(vertexBlock).append("\n");
        }

        // Include explanation steps for context
        if (q.getExplanationSteps() != null && !q.getExplanationSteps().isBlank()) {
            sb.append("SOLUTION STEPS (your animation should visually support these):\n");
            String steps = q.getExplanationSteps();
            if (steps.length() > 1200) steps = steps.substring(0, 1200) + "...";
            sb.append(steps).append("\n\n");
        }

        final int fw = canvasW, fh = canvasH;
        final boolean hasVertices = !vertexBlock.isEmpty();
        sb.append("TASK: Generate EXACTLY 3-4 animation frames that progressively build a geometric figure.\n");
        sb.append("Frames are CUMULATIVE — each frame includes ALL elements from previous frames plus new ones.\n\n");
        sb.append("CANVAS: ").append(fw).append("x").append(fh)
          .append(" px. Top-left origin. Y increases downward. 25px margin.\n\n");

        if (hasVertices) {
            sb.append("CRITICAL: The diagram coordinates above are the SOURCE OF TRUTH.\n");
            sb.append("Your polygon points MUST match the vertex coordinates exactly.\n\n");
        }

        sb.append("""
FRAME STRUCTURE (cumulative):
- Frame 1: base polygon/shape + dot at each vertex + vertex text labels (A, B, C…) + angle arc if needed
- Frame 2: side_label elements for all given/known side values
- Frame 3: highlight the unknown (red #dc2626)
- Frame 4 (optional): show final answer (green #16a34a)

VERTEX LABELS — ADD IN FRAME 1 (required for named-vertex problems):
Use the label positions computed from vertices above. Format:
{"type":"text","x":<lx>,"y":<ly>,"text":"A","fontSize":13,"color":"#1e293b","bold":true,"anchor":"middle"}

SIDE LABELS — always use side_label type (never plain text on a side line):
{"type":"side_label","p1":[x1,y1],"p2":[x2,y2],"text":"7","color":"#2563eb","offset":22,"awayFrom":[centX,centY],"fontSize":13}
offset rules: vertical sides (p1.x≈p2.x) → offset≥36; horizontal sides → offset≥20; diagonal → offset≥24.

STRICT LIMITS:
- Max 10 elements per frame total (cumulative)
- text labels: keep under 12 chars
- NO katex elements
- ALL numeric values MUST be numbers, not strings

ELEMENT TYPES — use ONLY these:
{"type":"polygon","points":[[x,y],...],"stroke":"#334155","fill":"#f0f9ff","strokeWidth":2}
{"type":"line","x1":x,"y1":y,"x2":x,"y2":y,"stroke":"#334155","strokeWidth":2,"dashed":false}
{"type":"circle","cx":x,"cy":y,"r":r,"stroke":"#334155","fill":"#f0f9ff","strokeWidth":2}
{"type":"rect","x":x,"y":y,"width":w,"height":h,"stroke":"#334155","fill":"#f0f9ff","strokeWidth":2}
{"type":"sector","cx":x,"cy":y,"r":r,"startDeg":deg,"endDeg":deg,"stroke":"#334155","fill":"#dbeafe","strokeWidth":2}
{"type":"right_angle","vertex":[x,y],"leg1":[x,y],"leg2":[x,y],"size":12}
{"type":"arc","cx":x,"cy":y,"r":r,"startDeg":deg,"endDeg":deg,"stroke":"#64748b","strokeWidth":1.5,"label":"52°","labelColor":"#64748b","labelSize":12}
{"type":"dot","x":x,"y":y,"r":4,"fill":"#1e293b"}
{"type":"text","x":x,"y":y,"text":"label","fontSize":13,"color":"#1e293b","bold":false,"anchor":"middle"}
{"type":"side_label","p1":[x1,y1],"p2":[x2,y2],"text":"label","color":"#2563eb","offset":22,"awayFrom":[cx,cy],"fontSize":13}

COLORS: base "#334155"/#f0f9ff, given "#2563eb", unknown "#dc2626", answer "#16a34a"

PROBLEM TYPE GUIDANCE:
- Triangles: polygon + dot at each vertex + vertex text labels + arc for angle markers + side_label for sides
- Circle area/circumference: circle element, label radius with side_label or text
- Sector/arc: sector element + arc for the arc portion
- Area of shaded region: outer shape then inner shape with different fill
- Coordinate geometry: dot elements for points, line elements for segments
- Pythagorean theorem: draw the right TRIANGLE (polygon 3 points), right_angle marker, label legs
- right_angle element: vertex is the corner, leg1/leg2 are the OTHER ends of the two legs (not unit vectors)
- arc angle labels: use "label" field on the arc (e.g. "label":"52°") — renderer auto-positions it; never put a separate text element on top of an arc
""");
        sb.append("Return ONLY valid JSON, no markdown:\n");
        sb.append("{\"eligible\":true,\"width\":").append(fw)
          .append(",\"height\":").append(fh)
          .append(",\"frames\":[{\"caption\":\"...\",\"elements\":[...]}]}\n");
        return sb.toString();
    }

    private void validate(JsonNode result) {
        if (!result.path("eligible").asBoolean(false)) {
            throw new IllegalStateException("eligible must be true");
        }
        JsonNode frames = result.path("frames");
        if (!frames.isArray() || frames.size() < 2) {
            throw new IllegalStateException("frames must be an array with at least 2 entries");
        }
        for (int i = 0; i < frames.size(); i++) {
            JsonNode frame = frames.get(i);
            if (frame.path("caption").asText("").isBlank()) {
                throw new IllegalStateException("frame " + i + " missing caption");
            }
            JsonNode elements = frame.path("elements");
            if (!elements.isArray() || elements.isEmpty()) {
                throw new IllegalStateException("frame " + i + " has no elements");
            }
        }
    }

    @Transactional
    void save(Question q, String animationJson) {
        q.setAnimation(animationJson);
        questionRepository.save(q);
    }

    private String padEnd(String s, int len) {
        if (s == null) s = "";
        return s.length() >= len ? s : s + " ".repeat(len - s.length());
    }
}
