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

        // Include existing diagram coordinates if available
        if (q.getDiagram() != null && !q.getDiagram().isBlank()) {
            sb.append("EXISTING DIAGRAM (use these exact coordinates for your animation):\n");
            sb.append(q.getDiagram()).append("\n\n");
        }

        // Include explanation steps for context
        if (q.getExplanationSteps() != null && !q.getExplanationSteps().isBlank()) {
            sb.append("SOLUTION STEPS (your animation should visually support these):\n");
            // Truncate if too long
            String steps = q.getExplanationSteps();
            if (steps.length() > 1200) steps = steps.substring(0, 1200) + "...";
            sb.append(steps).append("\n\n");
        }

        sb.append("""
TASK: Generate EXACTLY 3-4 animation frames that progressively build a geometric figure.
Frames are CUMULATIVE — each frame includes ALL elements from previous frames plus new ones.

CANVAS: 280x260 px. Top-left origin. Y increases downward. 25px margin.

FRAME STRUCTURE (cumulative):
- Frame 1: base figure only (the geometric shape(s))
- Frame 2: add labels for all known/given values
- Frame 3: highlight unknown element (use red #dc2626)
- Frame 4 (optional): show final answer highlighted (use green #16a34a)

STRICT LIMITS:
- Max 8 elements per frame total (cumulative)
- text labels: keep under 10 chars each
- NO katex elements — formulas go in the solution steps, not the canvas
- No vertex labels (A, B, C) unless needed for the problem
- ALL numeric values in elements (x, y, cx, cy, r, x1, y1, x2, y2, fontSize, strokeWidth, size) MUST be numbers, never strings

ELEMENT TYPES — use ONLY these:
{"type":"polygon","points":[[x,y],...],"stroke":"#334155","fill":"#f0f9ff","strokeWidth":2}
{"type":"line","x1":x,"y1":y,"x2":x,"y2":y,"stroke":"#334155","strokeWidth":2,"dashed":false}
{"type":"circle","cx":x,"cy":y,"r":r,"stroke":"#334155","fill":"#f0f9ff","strokeWidth":2}
{"type":"rect","x":x,"y":y,"width":w,"height":h,"stroke":"#334155","fill":"#f0f9ff","strokeWidth":2}
{"type":"sector","cx":x,"cy":y,"r":r,"startDeg":deg,"endDeg":deg,"stroke":"#334155","fill":"#dbeafe","strokeWidth":2}
{"type":"right_angle","vertex":[x,y],"leg1":[x,y],"leg2":[x,y],"size":12}
{"type":"arc","cx":x,"cy":y,"r":r,"startDeg":deg,"endDeg":deg,"stroke":"#64748b","strokeWidth":1.5}
{"type":"dot","x":x,"y":y,"r":4,"fill":"#1e293b"}
{"type":"text","x":x,"y":y,"text":"short label","fontSize":13,"color":"#1e293b"}

COLORS: base "#334155"/#f0f9ff, known "#2563eb", unknown "#dc2626", answer "#16a34a", sector "#dbeafe"

COORDINATE TEMPLATES:
Right triangle (right angle at C bottom-right): A=(40,220) C=(220,220) B=(220,55)
Circle: center=(140,130) r=90
Sector (arc slice): center=(140,220) r=110 — use startDeg/endDeg in degrees (0=right, 90=down, -90=up)
Rectangle: x=40 y=60 width=200 height=140
Composite (circle inside rectangle): rect x=40 y=60 w=200 h=160, circle cx=140 cy=140 r=70
Coordinate plane: axes lines from (20,130)→(260,130) and (140,20)→(140,240), dot at origin (140,130)
Triangle (general): three polygon points, use arc for angle markers

PROBLEM TYPE GUIDANCE:
- Circle area/circumference: use circle element, label radius
- Sector/arc: use sector element + arc for the arc portion
- Area of shaded region: draw outer shape (rect/polygon) then inner shape with different fill
- Similar triangles: two polygon triangles, highlight corresponding sides
- Inscribed figures: outer circle + inner polygon (or vice versa)
- Coordinate geometry: dot elements for points, line elements for segments
- Composite figures: multiple shapes layered
- Pythagorean theorem / diagonal of rectangle: ALWAYS draw the right TRIANGLE (not the full rectangle); use polygon with 3 points for the triangle, right_angle marker at the 90° corner, then add a bold line for the hypotenuse in frame 3-4; never draw the rectangle when the problem is about finding a diagonal
- right_angle element: vertex is the corner point, leg1 and leg2 are the OTHER ends of the two legs (not unit vectors)

Return ONLY valid JSON, no markdown:
{"eligible":true,"width":280,"height":260,"frames":[{"caption":"...","elements":[...]}]}
""");
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
