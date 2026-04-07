#!/usr/bin/env node
/**
 * visual-check-animations.js
 * Checks animation quality for all geometry questions.
 *
 * Two tiers of checks:
 *   1. Static math analysis  — overlap detection, bounds, vertex coverage (instant, no API)
 *   2. Claude semantic review — sends animation JSON + question to Claude for quality judgement
 *
 * Usage:
 *   node scripts/visual-check-animations.js              # check only, print report
 *   node scripts/visual-check-animations.js --fix        # auto-patch issues via API
 *   node scripts/visual-check-animations.js --id GEO-004 # single question
 *   node scripts/visual-check-animations.js --claude     # also run Claude semantic review
 *   node scripts/visual-check-animations.js --fix --claude --id GEO-004
 *
 * Environment:
 *   ANTHROPIC_API_KEY   required only with --claude
 *   API_BASE            defaults to http://localhost:8080
 */

'use strict';

const http  = require('http');
const https = require('https');
const path  = require('path');

const API_BASE  = process.env.API_BASE || 'http://localhost:8080';
const FIX_MODE  = process.argv.includes('--fix');
const CLAUDE    = process.argv.includes('--claude');
const ID_IDX    = process.argv.indexOf('--id');
const ONLY_ID   = ID_IDX !== -1 ? process.argv[ID_IDX + 1] : null;

// ─── HTTP helpers ────────────────────────────────────────────────────────────

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    mod.get(url, res => {
      let body = '';
      res.on('data', d => body += d);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); }
        catch (e) { reject(new Error(`JSON parse failed for ${url}: ${e.message}`)); }
      });
    }).on('error', reject);
  });
}

function patchJson(url, data) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const parsed = new URL(url);
    const mod = parsed.protocol === 'https:' ? https : http;
    const req = mod.request({
      hostname: parsed.hostname, port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path: parsed.pathname, method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    }, res => {
      let b = '';
      res.on('data', d => b += d);
      res.on('end', () => resolve({ status: res.statusCode, body: b }));
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ─── Static analysis helpers ─────────────────────────────────────────────────

/** Estimate rendered text width (px) for a given string + fontSize. */
function textWidth(text, fontSize) {
  return String(text).length * (fontSize || 13) * 0.55;
}

/**
 * Compute label position for a side_label element.
 * Returns {x, y} centre of the rendered label.
 */
function sideLabelPos(el) {
  const [x1, y1] = el.p1 || [0, 0];
  const [x2, y2] = el.p2 || [0, 0];
  const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
  const [ax, ay] = el.awayFrom || [mx, my];
  let dx = mx - ax, dy = my - ay;
  const len = Math.hypot(dx, dy) || 1;
  dx /= len; dy /= len;
  // auto-enforce minimum offset (mirrors renderer.js logic — with cap to prevent over-expansion)
  const fs = el.fontSize || 13;
  const htw = textWidth(el.text || '', fs) / 2;
  const hth = fs * 0.5;
  const minX = Math.abs(dx) > 0.15 ? Math.min((htw + 5) / Math.abs(dx), htw + 8) : 0;
  const minY = Math.abs(dy) > 0.15 ? Math.min((hth + 4) / Math.abs(dy), hth + 6) : 0;
  const off = Math.max(el.offset ?? 18, minX, minY);
  return { x: mx + dx * off, y: my + dy * off };
}

/**
 * Signed distance from point (px, py) to segment (x1,y1)→(x2,y2).
 * Positive = left of direction vector, negative = right.
 */
function distPointToSegment(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  return Math.abs((dy * px - dx * py + x2 * y1 - y2 * x1) / len);
}

/**
 * Check if a text box (centred at cx,cy, half-width hw, half-height hh)
 * overlaps a line segment.
 * Returns overlap distance (> 0 means overlap, ≤ 0 means clear).
 */
function textBoxOverlapsSegment(cx, cy, hw, hh, x1, y1, x2, y2) {
  const d = distPointToSegment(cx, cy, x1, y1, x2, y2);
  // Approximate text box clearance: use the diagonal of the half-box
  const clearance = Math.hypot(hw, hh) * 0.7;
  return clearance - d; // positive = overlap
}

// ─── Issue checkers ───────────────────────────────────────────────────────────

/**
 * Returns array of issue objects: { severity, type, detail, fix? }
 * severity: 'error' | 'warn'
 */
function checkAnimation(q) {
  const issues = [];
  const anim = q.animation || {};
  const frames = anim.frames || [];
  const diag = (() => { try { return JSON.parse(q.diagram || '{}'); } catch { return {}; } })();
  const cfg = diag.svgConfig || {};
  const vertices = cfg.vertices || {};
  const vertexNames = Object.keys(vertices);
  const W = anim.width || 280, H = anim.height || 260;

  if (!frames.length) {
    issues.push({ severity: 'error', type: 'NO_FRAMES', detail: 'Animation has no frames' });
    return issues;
  }

  // ── 1. Vertex labels in frame 0 ───────────────────────────────────────────
  if (vertexNames.length > 0) {
    const frame0els = frames[0].elements || [];
    const labeledVertices = new Set(
      frame0els.filter(e => e.type === 'text' && vertexNames.includes(e.text)).map(e => e.text)
    );
    const missing = vertexNames.filter(v => !labeledVertices.has(v));
    if (missing.length > 0) {
      issues.push({
        severity: 'error',
        type: 'MISSING_VERTEX_LABELS',
        detail: `Frame 0 missing vertex labels: ${missing.join(', ')}`,
        missingVertices: missing,
        vertices, centroid: computeCentroid(vertices), canvasW: W, canvasH: H
      });
    }
  }

  // ── 2. Polygon coordinates match diagram vertices ─────────────────────────
  if (vertexNames.length > 0) {
    const frame0els = frames[0].elements || [];
    const polygons = frame0els.filter(e => e.type === 'polygon');
    if (polygons.length > 0) {
      const poly = polygons[0];
      const polyPoints = (poly.points || []).map(([x, y]) => ({ x, y }));
      const diagPoints = vertexNames.map(k => vertices[k]);
      // Check if every diagram vertex is in the polygon (within 3px)
      for (const dv of diagPoints) {
        const close = polyPoints.some(pp => Math.hypot(pp.x - dv.x, pp.y - dv.y) < 3);
        if (!close) {
          issues.push({
            severity: 'warn',
            type: 'COORD_MISMATCH',
            detail: `Polygon does not include diagram vertex (${dv.x},${dv.y}) — animation may not match question diagram`
          });
          break; // one warning per question is enough
        }
      }
    }
  }

  // ── 3. Side label overlap / insufficient offset ───────────────────────────
  for (let fi = 0; fi < frames.length; fi++) {
    const els = frames[fi].elements || [];
    for (const el of els) {
      if (el.type !== 'side_label') continue;
      const [x1, y1] = el.p1 || [0, 0];
      const [x2, y2] = el.p2 || [0, 0];
      const pos = sideLabelPos(el);
      const hw = textWidth(el.text || '', el.fontSize || 13) / 2;
      const hh = (el.fontSize || 13) * 0.5;
      const overlap = textBoxOverlapsSegment(pos.x, pos.y, hw, hh, x1, y1, x2, y2);
      if (overlap > 2) {
        // compute minimum safe offset
        const dx = (x1 === x2) ? 0 : (x2 - x1) / Math.hypot(x2-x1, y2-y1);
        const dy = (y1 === y2) ? 0 : (y2 - y1) / Math.hypot(x2-x1, y2-y1);
        const isVertical = Math.abs(x1 - x2) < 3;
        const safeOffset = isVertical ? 38 : 26;
        issues.push({
          severity: 'error',
          type: 'SIDE_LABEL_OVERLAP',
          detail: `Frame ${fi} side_label "${el.text}" overlaps its segment (overlap≈${overlap.toFixed(1)}px). Increase offset to ${safeOffset}.`,
          frameIdx: fi, elementText: el.text, suggestedOffset: safeOffset
        });
      }
    }
  }

  // ── 4. Elements out of canvas bounds ─────────────────────────────────────
  const PAD = 5;
  for (let fi = 0; fi < frames.length; fi++) {
    const els = frames[fi].elements || [];
    for (const el of els) {
      let pts = [];
      if (el.type === 'polygon')   pts = (el.points || []).map(([x,y]) => [x,y]);
      if (el.type === 'dot')       pts = [[el.x, el.y]];
      if (el.type === 'text')      pts = [[el.x, el.y]];
      if (el.type === 'side_label') { const p = sideLabelPos(el); pts = [[p.x, p.y]]; }
      for (const [x, y] of pts) {
        if (x < -PAD || x > W + PAD || y < -PAD || y > H + PAD) {
          issues.push({
            severity: 'warn',
            type: 'OUT_OF_BOUNDS',
            detail: `Frame ${fi} element "${el.type}${el.text ? ' "'+el.text+'"' : ''}" at (${x},${y}) outside canvas ${W}x${H}`
          });
          break;
        }
      }
    }
  }

  // ── 5. Angle labels on arcs — detect old-style separate text on top of arc ──
  // Only flag multi-character text that looks like an angle value (e.g. "52°", "B=?")
  // NOT single-letter vertex labels (A, B, C) which are expected near arc angle markers.
  for (let fi = 0; fi < frames.length; fi++) {
    const els = frames[fi].elements || [];
    for (const el of els) {
      if (el.type === 'arc' && !el.label) {
        const arcX = el.cx, arcY = el.cy, arcR = el.r || 20;
        const nearbyAngleText = els.filter(t =>
          t.type === 'text' &&
          Math.hypot(t.x - arcX, t.y - arcY) < arcR * 2.0 &&
          t.text && t.text.length > 1 && // skip single-letter vertex labels
          !/^[A-Z]$/.test(t.text.trim())  // skip standalone vertex letters
        );
        if (nearbyAngleText.length > 0) {
          issues.push({
            severity: 'warn',
            type: 'ARC_TEXT_OVERLAP',
            detail: `Frame ${fi} arc at (${arcX},${arcY}) has no "label" field but nearby angle text "${nearbyAngleText[0].text}" — move to arc.label to prevent overlap`
          });
        }
      }
    }
  }

  return issues;
}

function computeCentroid(vertices) {
  const keys = Object.keys(vertices);
  const cx = keys.reduce((s, k) => s + vertices[k].x, 0) / keys.length;
  const cy = keys.reduce((s, k) => s + vertices[k].y, 0) / keys.length;
  return { x: Math.round(cx), y: Math.round(cy) };
}

// ─── Auto-fix generators ──────────────────────────────────────────────────────

/**
 * Build a patched animation that fixes all static issues found.
 * Returns the patched animation object, or null if nothing to fix.
 */
function buildFix(q, issues) {
  if (!issues.length) return null;
  const anim = JSON.parse(JSON.stringify(q.animation)); // deep clone
  let changed = false;

  for (const issue of issues) {
    // Fix 1: add missing vertex labels to every frame
    if (issue.type === 'MISSING_VERTEX_LABELS') {
      const { missingVertices, vertices, centroid, canvasW, canvasH } = issue;
      const newLabels = missingVertices.map(name => {
        const vx = vertices[name].x, vy = vertices[name].y;
        const ddx = vx - centroid.x, ddy = vy - centroid.y;
        const dlen = Math.hypot(ddx, ddy) || 1;
        let lx = Math.round(vx + (ddx/dlen) * 16);
        let ly = Math.round(vy + (ddy/dlen) * 16);
        lx = Math.max(12, Math.min(lx, canvasW - 12));
        ly = Math.max(12, Math.min(ly, canvasH - 12));
        return { type: 'text', x: lx, y: ly, text: name, fontSize: 13, color: '#1e293b', bold: true, anchor: 'middle' };
      });
      for (const frame of anim.frames) {
        // Insert after last dot element (same approach as the Python fix script)
        let insertPos = 0;
        frame.elements.forEach((el, i) => { if (el.type === 'dot' || el.type === 'polygon') insertPos = i + 1; });
        // Only add labels not already present
        const existing = new Set(frame.elements.filter(e => e.type === 'text').map(e => e.text));
        const toAdd = newLabels.filter(l => !existing.has(l.text));
        frame.elements.splice(insertPos, 0, ...toAdd);
      }
      changed = true;
    }

    // Fix 2: increase offset on overlapping side labels
    if (issue.type === 'SIDE_LABEL_OVERLAP') {
      const { frameIdx, elementText, suggestedOffset } = issue;
      // Apply to ALL frames (labels persist cumulatively)
      for (const frame of anim.frames) {
        for (const el of frame.elements) {
          if (el.type === 'side_label' && el.text === elementText) {
            if ((el.offset || 0) < suggestedOffset) {
              el.offset = suggestedOffset;
              changed = true;
            }
          }
        }
      }
    }
  }

  return changed ? anim : null;
}

// ─── Claude semantic review ───────────────────────────────────────────────────

async function claudeReview(q) {
  const Anthropic = require(path.join(__dirname, '../../ReviewSite/node_modules/@anthropic-ai/sdk'));
  const client = new Anthropic.default({ apiKey: process.env.ANTHROPIC_API_KEY });

  const anim = q.animation || {};
  const diagVertices = (() => {
    try {
      const d = JSON.parse(q.diagram || '{}');
      return d.svgConfig?.vertices || {};
    } catch { return {}; }
  })();

  const prompt = `You are reviewing an SVG animation for an SAT math practice question.

QUESTION: ${q.questionStem}
DOMAIN: ${q.domain} | SKILL: ${q.skill}
${Object.keys(diagVertices).length ? `DIAGRAM VERTICES: ${JSON.stringify(diagVertices)}` : ''}

ANIMATION JSON:
${JSON.stringify(anim, null, 2).slice(0, 3000)}

Check for these issues and respond in JSON:
1. Do polygon coordinates match the diagram vertex coordinates (within 5px)?
2. Are all named vertices (A, B, C…) labelled in frame 0?
3. Do side labels use "side_label" type (not plain "text" on a segment)?
4. Are there any text elements that appear to overlap a polygon side?
5. Does the animation logically support solving the question step by step?
6. Is there anything else visually wrong or confusing?

Respond ONLY with JSON:
{
  "pass": true/false,
  "score": 0-10,
  "issues": [{"type": "...", "severity": "error|warn", "detail": "..."}],
  "summary": "one sentence"
}`;

  const response = await client.messages.create({
    model: 'claude-haiku-4-5',
    max_tokens: 512,
    messages: [{ role: 'user', content: prompt }]
  });
  const raw = response.content[0].text.replace(/^```json\s*/,'').replace(/\s*```$/,'').trim();
  return JSON.parse(raw);
}

// ─── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log('╔══════════════════════════════════════════════════════╗');
  console.log('║  SatEngine — Animation Visual Check                  ║');
  console.log(`║  mode: ${FIX_MODE ? 'FIX' : 'CHECK'} | claude: ${CLAUDE ? 'YES' : 'NO'} | target: ${ONLY_ID || 'ALL GEO'}         ║`);
  console.log('╚══════════════════════════════════════════════════════╝\n');

  // Fetch all questions
  let questions = await fetchJson(`${API_BASE}/api/admin/questions?page=0&size=200`);
  if (!Array.isArray(questions)) questions = questions.content || [];

  // Filter to GEO (or single ID)
  questions = questions.filter(q => {
    if (ONLY_ID) return q.externalId === ONLY_ID || q.externalId?.includes(ONLY_ID);
    return q.externalId?.includes('GEO') && q.animation?.frames?.length > 0;
  });

  if (!questions.length) {
    console.log('No matching questions found.');
    return;
  }

  console.log(`Checking ${questions.length} question(s)...\n`);

  let totalIssues = 0, totalFixed = 0, totalPassed = 0;
  const report = [];

  for (const q of questions) {
    const eid = q.externalId;
    process.stdout.write(`${eid.padEnd(18)}`);

    // Static checks
    const issues = checkAnimation(q);
    const errors = issues.filter(i => i.severity === 'error');
    const warns  = issues.filter(i => i.severity === 'warn');

    // Claude semantic check
    let claudeResult = null;
    if (CLAUDE && process.env.ANTHROPIC_API_KEY) {
      try {
        claudeResult = await claudeReview(q);
        // merge Claude issues
        (claudeResult.issues || []).forEach(i => issues.push(i));
      } catch (e) {
        process.stdout.write(' [Claude ERR] ');
      }
    }

    if (issues.length === 0 && (!claudeResult || claudeResult.pass)) {
      console.log('  ✅ PASS');
      totalPassed++;
    } else {
      const errCount = errors.length + (claudeResult && !claudeResult.pass ? 1 : 0);
      console.log(`  ${errCount > 0 ? '❌' : '⚠️ '} ${errors.length} error(s), ${warns.length} warn(s)${claudeResult ? ` | Claude: ${claudeResult.score}/10` : ''}`);
      for (const issue of issues.slice(0, 4)) {
        console.log(`       ${issue.severity === 'error' ? '🔴' : '🟡'} [${issue.type}] ${issue.detail}`);
      }
      if (claudeResult && claudeResult.summary) {
        console.log(`       🤖 Claude: ${claudeResult.summary}`);
      }
      totalIssues += issues.length;

      // Auto-fix
      if (FIX_MODE) {
        const staticIssues = issues.filter(i => i.type === 'MISSING_VERTEX_LABELS' || i.type === 'SIDE_LABEL_OVERLAP');
        const fix = buildFix(q, staticIssues);
        if (fix) {
          const result = await patchJson(`${API_BASE}/api/admin/questions/${q.id}/animation`, fix);
          if (result.status === 204) {
            console.log(`       🔧 PATCHED (${staticIssues.length} issue(s) fixed)`);
            totalFixed++;
          } else {
            console.log(`       💥 PATCH FAILED (HTTP ${result.status})`);
          }
        }
      }
    }
    report.push({ externalId: eid, issues, claudeResult });
  }

  // Summary
  console.log('\n' + '─'.repeat(56));
  console.log(`Passed: ${totalPassed}/${questions.length}  |  Issues found: ${totalIssues}  |  Fixed: ${totalFixed}`);
  if (!FIX_MODE && totalIssues > 0) {
    console.log('\nRun with --fix to auto-patch fixable issues.');
  }
  if (!CLAUDE) {
    console.log('Run with --claude to also do AI semantic review (needs ANTHROPIC_API_KEY).');
  }
}

main().catch(e => { console.error('\nFATAL:', e.message); process.exit(1); });
