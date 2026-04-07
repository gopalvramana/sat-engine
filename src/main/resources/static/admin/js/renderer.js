// ═══════════════════════════════════════════════════════════════════
// renderer.js — SAT Practice Platform: SVG + Chart.js rendering
// Public API:
//   buildSVG(config)               → SVG string
//   renderChart(canvasId, config)  → Chart.js instance
//   renderDiagram(cfg, hostEl)     → master dispatcher (used by app.js)
//   renderKaTeXIn(el)              → KaTeX re-render helper
// ═══════════════════════════════════════════════════════════════════

'use strict';

// ───────────────────────────────────────────────────────────────────
// SECTION 1 — SHARED UTILITIES
// ───────────────────────────────────────────────────────────────────

/** Clamp a label position so it stays inside the SVG canvas. */
function clampLabel(x, y, width, height, padding = 14) {
  return {
    x: Math.max(padding, Math.min(x, width - padding)),
    y: Math.max(padding, Math.min(y, height - padding))
  };
}

/** Midpoint between two {x,y} points. */
function midpoint(p1, p2) {
  return { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
}

/** Euclidean distance between two {x,y} points. */
function distance(p1, p2) {
  return Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
}

/** Wrap content in an SVG root element. */
function svgWrap(w, h, inner) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${inner}</svg>`;
}

/**
 * Compute a centering <g transform="translate(dx,dy)"> for a set of points.
 * Shifts the entire shape so its bounding box is centered in the canvas.
 * padding reserves space around the edges so labels don't clip.
 * Returns { open, close } — wrap SVG content between them.
 */
function autoCenterTransform(points, w, h, padding = 28) {
  const xs = points.map(p => p.x).filter(Number.isFinite);
  const ys = points.map(p => p.y).filter(Number.isFinite);
  if (!xs.length) return { open: '', close: '' };
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const dx = +((w - (maxX + minX)) / 2).toFixed(2);
  const dy = +((h - (maxY + minY)) / 2).toFixed(2);
  if (Math.abs(dx) < 2 && Math.abs(dy) < 2) return { open: '', close: '' };
  return { open: `<g transform="translate(${dx},${dy})">`, close: `</g>` };
}

/** Build a <text> SVG element with sensible defaults. */
function svgText(x, y, text, opts = {}) {
  const fs  = opts.fontSize   ?? 13;
  const fl  = opts.fill       ?? '#1e293b';
  const ff  = opts.fontFamily ?? 'Georgia, serif';
  const fi  = opts.italic     ? 'italic' : 'normal';
  const fw  = opts.bold       ? '700'    : 'normal';
  const ta  = opts.textAnchor ?? 'middle';
  const dy  = opts.dy         ?? '0.35em';
  return `<text x="${x.toFixed(2)}" y="${y.toFixed(2)}" text-anchor="${ta}" dominant-baseline="auto" dy="${dy}" font-size="${fs}" font-family="${ff}" font-style="${fi}" font-weight="${fw}" fill="${fl}">${text}</text>`;
}

/** Arrowhead polygon at end of a line. */
function arrowHead(x1, y1, x2, y2, color = '#334155') {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  const len = 8, wide = 4;
  const ax = x2 - len * Math.cos(angle);
  const ay = y2 - len * Math.sin(angle);
  const lx = ax - wide * Math.sin(angle), ly = ay + wide * Math.cos(angle);
  const rx = ax + wide * Math.sin(angle), ry = ay - wide * Math.cos(angle);
  return `<polygon points="${x2.toFixed(2)},${y2.toFixed(2)} ${lx.toFixed(2)},${ly.toFixed(2)} ${rx.toFixed(2)},${ry.toFixed(2)}" fill="${color}" stroke="none"/>`;
}

/**
 * Right-angle square marker at vertex V given the two adjacent vertices A and B.
 * Uses unit vectors from V toward A and V toward B to orient the square correctly.
 */
function rightAngleSquare(vx, vy, ax, ay, bx, by, size = 10) {
  const dax = ax - vx, day = ay - vy;
  const dLen = Math.sqrt(dax * dax + day * day) || 1;
  const uax = dax / dLen, uay = day / dLen;

  const dbx = bx - vx, dby = by - vy;
  const bLen = Math.sqrt(dbx * dbx + dby * dby) || 1;
  const ubx = dbx / bLen, uby = dby / bLen;

  const p1x = vx + size * uax, p1y = vy + size * uay;
  const p2x = p1x + size * ubx, p2y = p1y + size * uby;
  const p3x = vx + size * ubx, p3y = vy + size * uby;

  return `<path d="M${p1x.toFixed(2)},${p1y.toFixed(2)} L${p2x.toFixed(2)},${p2y.toFixed(2)} L${p3x.toFixed(2)},${p3y.toFixed(2)}" fill="none" stroke="#1d4ed8" stroke-width="1.8"/>`;
}

/** Tick mark perpendicular to a side (used for equal-side markers). */
function tickMark(x1, y1, x2, y2, count = 1) {
  const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
  const angle = Math.atan2(y2 - y1, x2 - x1) + Math.PI / 2;
  const len = 5;
  let out = '';
  const offsets = count === 1 ? [0] : count === 2 ? [-4, 4] : [-6, 0, 6];
  const lineAngle = Math.atan2(y2 - y1, x2 - x1);
  for (const off of offsets) {
    const ox = off * Math.cos(lineAngle), oy = off * Math.sin(lineAngle);
    const tx1 = mx + ox + len * Math.cos(angle), ty1 = my + oy + len * Math.sin(angle);
    const tx2 = mx + ox - len * Math.cos(angle), ty2 = my + oy - len * Math.sin(angle);
    out += `<line x1="${tx1.toFixed(2)}" y1="${ty1.toFixed(2)}" x2="${tx2.toFixed(2)}" y2="${ty2.toFixed(2)}" stroke="#334155" stroke-width="1.5"/>`;
  }
  return out;
}

/**
 * Evaluate a math function at x, returning y or null for undefined.
 * Supported types: linear, quadratic, cubic, quartic, absolute, square_root,
 *                  exponential, reciprocal, constant
 */
function evaluateFunction(funcConfig, x) {
  const p = funcConfig.params ?? {};
  const type = funcConfig.type ?? 'linear';
  try {
    switch (type) {
      case 'linear':      return (p.m ?? 1) * x + (p.b ?? 0);
      case 'quadratic':   return (p.a ?? 1) * x * x + (p.b ?? 0) * x + (p.c ?? 0);
      case 'cubic':       return (p.a ?? 1) * x * x * x + (p.b ?? 0) * x * x + (p.c ?? 0) * x + (p.d ?? 0);
      case 'quartic':     return (p.a ?? 1) * x**4 + (p.b ?? 0) * x**3 + (p.c ?? 0) * x**2 + (p.d ?? 0) * x + (p.e ?? 0);
      case 'absolute':    return (p.a ?? 1) * Math.abs(x - (p.h ?? 0)) + (p.k ?? 0);
      case 'square_root': {
        const inner = (p.a ?? 1) * (x - (p.h ?? 0));
        return inner >= 0 ? Math.sqrt(inner) + (p.k ?? 0) : null;
      }
      case 'exponential': return (p.a ?? 1) * Math.pow((p.b ?? Math.E), x) + (p.c ?? 0);
      case 'reciprocal':  {
        const denom = x - (p.h ?? 0);
        return Math.abs(denom) < 1e-9 ? null : (p.a ?? 1) / denom + (p.k ?? 0);
      }
      case 'constant':    return p.c ?? p.value ?? 0;
      default:            return null;
    }
  } catch {
    return null;
  }
}

/**
 * Convert math-world coordinates to SVG pixel coordinates.
 * config: { xMin, xMax, yMin, yMax, width, height, padL, padR, padT, padB }
 */
function mathToSVG(x, y, config) {
  const T = makeTransform({
    xMin: config.xMin, xMax: config.xMax,
    yMin: config.yMin, yMax: config.yMax,
    width: config.width, height: config.height,
    padL: config.padL, padR: config.padR,
    padT: config.padT, padB: config.padB
  });
  return T.toSVG(x, y);
}

/**
 * Plot a function as an SVG path string.
 * Returns a string of <path> elements (can have natural breaks for asymptotes).
 */
function plotFunction(funcConfig, cfg, domainMin, domainMax, color = '#334155', strokeWidth = 2, dashArray = '') {
  const steps = 300;
  const xStep = (domainMax - domainMin) / steps;
  const { xMin, xMax, yMin, yMax } = cfg;

  let pathD = '';
  let penDown = false;

  for (let i = 0; i <= steps; i++) {
    const mx = domainMin + i * xStep;
    const my = evaluateFunction(funcConfig, mx);

    if (my === null || !isFinite(my) || my < yMin - (yMax - yMin) || my > yMax + (yMax - yMin)) {
      if (penDown) { pathD += ' '; penDown = false; }
      continue;
    }

    const p = mathToSVG(mx, my, cfg);
    // Clip to viewport with some buffer
    if (p.x < cfg.padL - 4 || p.x > cfg.width - cfg.padR + 4) {
      if (penDown) { pathD += ' '; penDown = false; }
      continue;
    }

    if (!penDown) {
      pathD += `M${p.x.toFixed(2)},${p.y.toFixed(2)}`;
      penDown = true;
    } else {
      pathD += ` L${p.x.toFixed(2)},${p.y.toFixed(2)}`;
    }
  }

  if (!pathD) return '';
  const dash = dashArray ? `stroke-dasharray="${dashArray}"` : '';
  return `<path d="${pathD}" fill="none" stroke="${color}" stroke-width="${strokeWidth}" ${dash} stroke-linecap="round" stroke-linejoin="round"/>`;
}

/**
 * Least-squares linear regression.
 * Returns { slope, intercept }.
 */
function leastSquares(points) {
  const n = points.length;
  if (n < 2) return { slope: 0, intercept: points[0]?.y ?? 0 };
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  for (const p of points) {
    sumX += p.x; sumY += p.y;
    sumXY += p.x * p.y; sumX2 += p.x * p.x;
  }
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

/** Smart tick step for coordinate planes. */
function smartStep(span) {
  if (span <= 5)  return 1;
  if (span <= 12) return 2;
  if (span <= 30) return 5;
  if (span <= 80) return 10;
  return Math.ceil(span / 8 / 5) * 5;
}

/** Convert a CSS hex color to rgba with given opacity. */
function hexAlpha(hex, a) {
  if (!hex || !hex.startsWith('#')) return `rgba(100,100,100,${a})`;
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
}

// ── Render option defaults — all hardcoded pixel values live here ──
const RENDER_DEFAULTS = {
  arcRadius:          18,   // angle arc radius (triangles, circles)
  sideLabelOffset:    14,   // perpendicular offset for side labels
  vertexLabelOffset:  16,   // outward offset for vertex labels
  tickSize:            5,   // half-length of equal-side tick marks
  pointLabelOffset:   14,   // offset for labels on circle points
  padL: 42, padR: 24, padT: 24, padB: 40  // coordinate plane padding
};

/**
 * Merge per-config renderOpts with global defaults.
 * cfg.renderOpts fields override RENDER_DEFAULTS.
 */
function resolveRenderOpts(cfg) {
  return Object.assign({}, RENDER_DEFAULTS, cfg.renderOpts ?? {});
}

// ── SVG Primitive Layer ─────────────────────────────────────────────
// All low-level SVG drawing goes through here.
// Every function takes an optional style object and returns an SVG string.
const Prim = {

  line(x1, y1, x2, y2, style = {}) {
    const sc  = style.stroke      ?? '#334155';
    const sw  = style.strokeWidth ?? 2;
    const da  = style.strokeDasharray ? `stroke-dasharray="${style.strokeDasharray}"` : '';
    const cap = style.strokeLinecap ? `stroke-linecap="${style.strokeLinecap}"` : '';
    return `<line x1="${+x1.toFixed(2)}" y1="${+y1.toFixed(2)}" x2="${+x2.toFixed(2)}" y2="${+y2.toFixed(2)}" stroke="${sc}" stroke-width="${sw}" ${da} ${cap}/>`;
  },

  circle(cx, cy, r, style = {}) {
    const fc = style.fill        ?? 'none';
    const sc = style.stroke      ?? '#334155';
    const sw = style.strokeWidth ?? 2;
    return `<circle cx="${+cx.toFixed(2)}" cy="${+cy.toFixed(2)}" r="${+r.toFixed(2)}" fill="${fc}" stroke="${sc}" stroke-width="${sw}"/>`;
  },

  polygon(points, style = {}) {
    // points: array of {x, y}
    const pts = points.map(p => `${+p.x.toFixed(2)},${+p.y.toFixed(2)}`).join(' ');
    const fc  = style.fill        ?? '#dbeafe';
    const sc  = style.stroke      ?? '#1d4ed8';
    const sw  = style.strokeWidth ?? 2.2;
    return `<polygon points="${pts}" fill="${fc}" stroke="${sc}" stroke-width="${sw}"/>`;
  },

  arc(cx, cy, r, startAngleDeg, endAngleDeg, style = {}) {
    // Draws an arc from startAngleDeg to endAngleDeg (SVG angle space, 0=right, clockwise)
    const sa   = startAngleDeg * Math.PI / 180;
    const ea   = endAngleDeg   * Math.PI / 180;
    let diff   = endAngleDeg - startAngleDeg;
    while (diff >  360) diff -= 360;
    while (diff < -360) diff += 360;
    const large = Math.abs(diff) > 180 ? 1 : 0;
    const sweep = diff > 0 ? 1 : 0;
    const x1 = cx + r * Math.cos(sa), y1 = cy + r * Math.sin(sa);
    const x2 = cx + r * Math.cos(ea), y2 = cy + r * Math.sin(ea);
    const sc  = style.stroke      ?? '#334155';
    const sw  = style.strokeWidth ?? 1.2;
    const fc  = style.fill        ?? 'none';
    const da  = style.strokeDasharray ? `stroke-dasharray="${style.strokeDasharray}"` : '';
    return `<path d="M${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large},${sweep} ${x2.toFixed(2)},${y2.toFixed(2)}" fill="${fc}" stroke="${sc}" stroke-width="${sw}" ${da}/>`;
  },

  path(d, style = {}) {
    const sc = style.stroke      ?? '#334155';
    const sw = style.strokeWidth ?? 2;
    const fc = style.fill        ?? 'none';
    const da = style.strokeDasharray ? `stroke-dasharray="${style.strokeDasharray}"` : '';
    return `<path d="${d}" fill="${fc}" stroke="${sc}" stroke-width="${sw}" ${da} stroke-linecap="round" stroke-linejoin="round"/>`;
  },

  text(x, y, content, opts = {}) {
    // Thin wrapper over svgText — same options, clamped via clampLabel
    const w = opts.svgWidth  ?? 9999;
    const h = opts.svgHeight ?? 9999;
    const pos = clampLabel(x, y, w, h);
    return svgText(pos.x, pos.y, content, opts);
  }
};

// ── Coordinate Transform Factory ───────────────────────────────────
/**
 * Creates a reusable math↔SVG coordinate transform.
 * Usage:
 *   const T = makeTransform({ xMin, xMax, yMin, yMax, width, height, padL, padR, padT, padB });
 *   const {x, y} = T.toSVG(mathX, mathY);
 *   const {x, y} = T.toMath(svgX, svgY);
 */
function makeTransform({ xMin, xMax, yMin, yMax, width, height, padL, padR, padT, padB }) {
  const plotW = width  - padL - padR;
  const plotH = height - padT - padB;
  const xRange = xMax - xMin || 1;
  const yRange = yMax - yMin || 1;
  return {
    toSVG(mx, my) {
      return {
        x: padL + (mx - xMin) / xRange * plotW,
        y: padT + (yMax - my) / yRange * plotH
      };
    },
    toMath(sx, sy) {
      return {
        x: xMin + (sx - padL) / plotW * xRange,
        y: yMax - (sy - padT) / plotH * yRange
      };
    },
    xMin, xMax, yMin, yMax, width, height, padL, padR, padT, padB
  };
}

// ── Label Collision Tracker ─────────────────────────────────────────
/**
 * Tracks placed label bounding boxes and finds non-overlapping positions.
 * Usage:
 *   const tracker = makeLabelTracker();
 *   const {x, y} = tracker.place(preferredX, preferredY, svgWidth, svgHeight, labelText);
 */
function makeLabelTracker() {
  const boxes = [];
  const CHAR_W = 7.5, CHAR_H = 14, PAD = 3;

  function overlaps(ax, ay, aw, ah) {
    return boxes.some(b =>
      ax < b.x + b.w + PAD && ax + aw + PAD > b.x &&
      ay < b.y + b.h + PAD && ay + ah + PAD > b.y
    );
  }

  function register(x, y, text) {
    const w = (text?.length ?? 1) * CHAR_W;
    const h = CHAR_H;
    boxes.push({ x: x - w / 2, y: y - h / 2, w, h });
  }

  return {
    /**
     * Find the best position for a label near (px, py).
     * Tries the preferred position first, then 8 candidate offsets.
     * Always clamps to SVG bounds.
     * @param {number} px - preferred x
     * @param {number} py - preferred y
     * @param {number} svgW - SVG width (for clamping)
     * @param {number} svgH - SVG height (for clamping)
     * @param {string} text - label text (used for width estimation)
     * @param {number} [nudge=14] - offset distance when preferred is blocked
     */
    place(px, py, svgW, svgH, text = '', nudge = 14) {
      const w = (text.length || 1) * CHAR_W;
      const h = CHAR_H;
      const clamp = (x, y) => clampLabel(x, y, svgW, svgH);

      // Candidate positions: preferred first, then 8 directions
      const candidates = [
        { x: px,        y: py        },        // 0: preferred
        { x: px,        y: py - nudge },       // 1: above
        { x: px,        y: py + nudge },       // 2: below
        { x: px - nudge, y: py       },        // 3: left
        { x: px + nudge, y: py       },        // 4: right
        { x: px + nudge, y: py - nudge },      // 5: upper-right
        { x: px - nudge, y: py - nudge },      // 6: upper-left
        { x: px + nudge, y: py + nudge },      // 7: lower-right
        { x: px - nudge, y: py + nudge },      // 8: lower-left
      ];

      for (const c of candidates) {
        const clamped = clamp(c.x, c.y);
        if (!overlaps(clamped.x - w / 2, clamped.y - h / 2, w, h)) {
          register(clamped.x, clamped.y, text);
          return clamped;
        }
      }

      // Fallback: use preferred position even if it overlaps
      const fallback = clamp(px, py);
      register(fallback.x, fallback.y, text);
      return fallback;
    },

    reset() { boxes.length = 0; }
  };
}

/**
 * Advisory schema validation. Never throws. Never mutates.
 * Returns { valid: boolean, errors: string[], warnings: string[] }
 * Call from debug tools or React layer — not called automatically by buildSVG.
 */
function validateConfig(cfg) {
  const errors = [], warnings = [];
  if (!cfg) { errors.push('Config is null or undefined'); return { valid: false, errors, warnings }; }

  const SVG_SHAPES   = ['triangle','right_triangle','circle','number_line','rectangle',
    'parallel_transversal','triangle_with_altitude','coordinate_plane',
    'parallelogram','trapezoid','two_triangles','3d_shape','venn_diagram',
    'normal_curve','regular_polygon'];
  const CHART_TYPES  = ['bar','histogram','line','scatter','pie','boxplot','dotplot'];
  const FN_TYPES     = ['linear','quadratic','cubic','quartic','absolute','square_root',
                        'exponential','reciprocal','constant'];
  const CP_SUBTYPES  = ['basic','function_graph','system_of_equations','inequality','piecewise'];

  if (cfg.shape     && !SVG_SHAPES.includes(cfg.shape))
    errors.push(`Unknown shape: "${cfg.shape}". Valid: ${SVG_SHAPES.join(', ')}`);
  if (cfg.chartType && !CHART_TYPES.includes(cfg.chartType))
    errors.push(`Unknown chartType: "${cfg.chartType}". Valid: ${CHART_TYPES.join(', ')}`);

  if (cfg.shape === 'triangle' || cfg.shape === 'right_triangle') {
    const keys = Object.keys(cfg.vertices ?? {});
    if (keys.length < 3) errors.push('Triangle needs at least 3 vertices');
    for (const s of (cfg.sides ?? [])) {
      if (s.from && !cfg.vertices?.[s.from]) errors.push(`Side "from" vertex "${s.from}" not in vertices`);
      if (s.to   && !cfg.vertices?.[s.to])   errors.push(`Side "to" vertex "${s.to}" not in vertices`);
    }
    for (const a of (cfg.angles ?? [])) {
      if (a.at && !cfg.vertices?.[a.at]) errors.push(`Angle "at" vertex "${a.at}" not in vertices`);
      for (const b of (a.between ?? []))
        if (!cfg.vertices?.[b]) errors.push(`Angle "between" vertex "${b}" not in vertices`);
    }
    for (const am of (cfg.angleMarkers ?? []))
      if (am.at && !cfg.vertices?.[am.at]) errors.push(`angleMarker "at" vertex "${am.at}" not in vertices`);
  }

  if (cfg.shape === 'coordinate_plane' && cfg.subtype && !CP_SUBTYPES.includes(cfg.subtype))
    errors.push(`Unknown coordinate_plane subtype: "${cfg.subtype}"`);

  for (const fn of (cfg.functions ?? [])) {
    if (fn.type && !FN_TYPES.includes(fn.type)) errors.push(`Unknown function type: "${fn.type}"`);
    if (fn.type === 'linear' && fn.params?.slope != null && fn.params?.m == null)
      warnings.push(`Linear function uses "slope" — should be "m". normalizeConfig() will fix this.`);
  }

  return { valid: errors.length === 0, errors, warnings };
}

// ───────────────────────────────────────────────────────────────────
// SECTION 2 — SVG SHAPE RENDERERS
// ───────────────────────────────────────────────────────────────────

// ── normalizeConfig ─────────────────────────────────────────────────
/**
 * Upgrade legacy config fields to the current schema.
 * Pure function — returns a new object, never mutates input.
 * Called automatically by buildSVG before any draw function runs.
 *
 * Migrations:
 *   rightAngleAt              → angleMarkers[{ at, type:"right" }]
 *   sides[].highlight         → sides[].style.stroke / strokeWidth
 *   functions[].color         → functions[].style.stroke
 *   functions[].strokeWidth   → functions[].style.strokeWidth
 *   params.slope (linear)     → params.m  (common AI generator typo)
 */
function normalizeConfig(cfg) {
  if (!cfg) return cfg;
  const c = Object.assign({}, cfg);

  // rightAngleAt → angleMarkers
  if (c.rightAngleAt != null && !c.angleMarkers) {
    c.angleMarkers = [{ at: c.rightAngleAt, type: 'right' }];
  }

  // sides[].highlight / highlightColor → sides[].style
  if (Array.isArray(c.sides)) {
    c.sides = c.sides.map(s => {
      if (!s.highlight) return s;
      const ns = Object.assign({}, s);
      ns.style = Object.assign(
        { stroke: s.highlightColor ?? '#2563eb', strokeWidth: 2.5 },
        s.style
      );
      return ns;
    });
  }

  // functions[].color / strokeWidth → functions[].style
  if (Array.isArray(c.functions)) {
    c.functions = c.functions.map(fn => {
      if (!fn.color && !fn.strokeWidth) return fn;
      const nf = Object.assign({}, fn);
      if (!nf.style) {
        nf.style = {
          stroke:      fn.color       ?? '#334155',
          strokeWidth: fn.strokeWidth ?? 2
        };
      }
      return nf;
    });
  }

  // params.slope → params.m for linear functions (AI generator typo)
  if (Array.isArray(c.functions)) {
    c.functions = c.functions.map(fn => {
      if (fn.type === 'linear' && fn.params?.slope != null && fn.params?.m == null) {
        const nf = Object.assign({}, fn);
        nf.params = Object.assign({}, fn.params, { m: fn.params.slope });
        return nf;
      }
      return fn;
    });
  }

  return c;
}

// ── Shape: triangle ────────────────────────────────────────────────
function drawTriangle(cfg) {
  const V = cfg.vertices ?? {};
  const keys = Object.keys(V);
  if (keys.length < 3) return svgWrap(cfg.width ?? 240, cfg.height ?? 200, '');

  const w = cfg.width ?? 240, h = cfg.height ?? 200;

  // Centroid
  const cx = keys.reduce((s, k) => s + V[k].x, 0) / keys.length;
  const cy = keys.reduce((s, k) => s + V[k].y, 0) / keys.length;

  // Label collision tracker
  const labelTracker = makeLabelTracker();

  let out = '';
  // Triangle body — drawn first (background)
  out += Prim.polygon(keys.map(k => ({ x: V[k].x, y: V[k].y })), cfg.style ?? {});

  // Highlighted sides (draw on top later)
  const normalSides = [], highlightSides = [];
  for (const s of (cfg.sides ?? [])) {
    (s.highlight ? highlightSides : normalSides).push(s);
  }

  // Side labels — offset perpendicular to side, outward from centroid
  for (const s of [...normalSides, ...highlightSides]) {
    const p1 = V[s.from], p2 = V[s.to];
    if (!p1 || !p2) continue;
    // New: style object (from new schema or normalizeConfig)
    if (s.style) {
      out += Prim.line(p1.x, p1.y, p2.x, p2.y, {
        stroke: s.style.stroke ?? '#2563eb',
        strokeWidth: s.style.strokeWidth ?? 2.5
      });
    } else if (s.highlight) {
      // Legacy fallback (for any config that bypassed normalizeConfig)
      out += Prim.line(p1.x, p1.y, p2.x, p2.y, {
        stroke: s.highlightColor ?? '#2563eb',
        strokeWidth: 2.5
      });
    }
    if (s.label) {
      const mid = midpoint(p1, p2);
      // Perpendicular direction, pointed away from centroid
      const dx = p2.x - p1.x, dy = p2.y - p1.y;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      let nx = -dy / len, ny = dx / len; // perpendicular unit vector
      // Ensure it points away from centroid
      const toCx = mid.x - cx, toCy = mid.y - cy;
      if (nx * toCx + ny * toCy < 0) { nx = -nx; ny = -ny; }
      // Auto-offset: ensure label clears the segment for any text length.
      // Mirrors the capped formula used in the animation renderer so both
      // the question diagram and animation labels stay off the sides.
      const _fs  = 13;
      const _htw = (s.label.length * _fs * 0.55) / 2;
      const _hth = _fs * 0.5;
      const _minX = Math.abs(nx) > 0.15 ? Math.min((_htw + 5) / Math.abs(nx), _htw + 8) : 0;
      const _minY = Math.abs(ny) > 0.15 ? Math.min((_hth + 4) / Math.abs(ny), _hth + 6) : 0;
      const offset = Math.max(14, _minX, _minY);
      const lpos = labelTracker.place(mid.x + nx * offset, mid.y + ny * offset, w, h, s.label ?? '');
      out += svgText(lpos.x, lpos.y, s.label, { fontSize: 13 });
    }
  }

  // Equal side tick marks
  if (cfg.equalSides) {
    // Build tick count per group
    const tickCounts = {};
    cfg.equalSides.forEach((group, gi) => {
      for (const key of group) {
        tickCounts[key] = gi + 1;
      }
    });
    for (const s of (cfg.sides ?? [])) {
      const key1 = s.from + s.to, key2 = s.to + s.from;
      const count = tickCounts[key1] ?? tickCounts[key2];
      if (count !== undefined) {
        const p1 = V[s.from], p2 = V[s.to];
        out += tickMark(p1.x, p1.y, p2.x, p2.y, count);
      }
    }
  }

  // Right angle marker
  if (cfg.rightAngleAt) {
    const vKey = cfg.rightAngleAt;
    const vx = V[vKey].x, vy = V[vKey].y;
    const others = keys.filter(k => k !== vKey);
    if (others.length >= 2) {
      out += rightAngleSquare(vx, vy, V[others[0]].x, V[others[0]].y, V[others[1]].x, V[others[1]].y);
    }
  }

  // New: angleMarkers array (multiple markers, multiple types)
  const _ropts = resolveRenderOpts(cfg);
  for (const am of (cfg.angleMarkers ?? [])) {
    const vKey = am.at;
    if (!V[vKey]) continue;
    const _vx = V[vKey].x, _vy = V[vKey].y;
    const _others = keys.filter(k => k !== vKey);
    if (_others.length < 2) continue;
    if (am.type === 'right') {
      out += rightAngleSquare(_vx, _vy, V[_others[0]].x, V[_others[0]].y, V[_others[1]].x, V[_others[1]].y);
    } else if (am.type === 'arc' || am.type === 'double_arc') {
      const arcCount = am.type === 'double_arc' ? 2 : 1;
      const adj1 = V[_others[0]], adj2 = V[_others[1]];
      const _d1x = adj1.x - _vx, _d1y = adj1.y - _vy, _l1 = Math.sqrt(_d1x*_d1x + _d1y*_d1y) || 1;
      const _d2x = adj2.x - _vx, _d2y = adj2.y - _vy, _l2 = Math.sqrt(_d2x*_d2x + _d2y*_d2y) || 1;
      const _u1x = _d1x/_l1, _u1y = _d1y/_l1, _u2x = _d2x/_l2, _u2y = _d2y/_l2;
      const _saDeg = Math.atan2(_u1y, _u1x) * 180 / Math.PI;
      let _eaDeg = Math.atan2(_u2y, _u2x) * 180 / Math.PI;
      let _diff = _eaDeg - _saDeg;
      while (_diff > 180) _diff -= 360;
      while (_diff < -180) _diff += 360;
      _eaDeg = _saDeg + _diff;
      for (let _ai = 0; _ai < arcCount; _ai++) {
        const _ar = (_ropts.arcRadius ?? 18) + _ai * 6;
        out += Prim.arc(_vx, _vy, _ar, _saDeg, _eaDeg);
      }
    }
  }

  // Angle labels + arcs — placed INSIDE the angle, along the bisector
  for (const a of (cfg.angles ?? [])) {
    const vx = V[a.at]?.x, vy = V[a.at]?.y;
    if (vx == null) continue;
    // Find the two adjacent vertices (honor a.between if provided)
    let adj1, adj2;
    if (a.between && a.between.length === 2) {
      adj1 = V[a.between[0]];
      adj2 = V[a.between[1]];
    } else {
      const adjKeys = keys.filter(k => k !== a.at);
      adj1 = V[adjKeys[0]];
      adj2 = V[adjKeys[1]];
    }
    if (!adj1 || !adj2) continue;
    // Unit vectors from vertex toward each adjacent vertex
    const d1x = adj1.x - vx, d1y = adj1.y - vy;
    const l1 = Math.sqrt(d1x*d1x + d1y*d1y) || 1;
    const u1x = d1x/l1, u1y = d1y/l1;
    const d2x = adj2.x - vx, d2y = adj2.y - vy;
    const l2 = Math.sqrt(d2x*d2x + d2y*d2y) || 1;
    const u2x = d2x/l2, u2y = d2y/l2;
    // Bisector = sum of unit vectors, normalized
    let bx = u1x + u2x, by = u1y + u2y;
    const bl = Math.sqrt(bx*bx + by*by) || 1;
    bx /= bl; by /= bl;
    // Draw angle arc via Prim
    const arcR = resolveRenderOpts(cfg).arcRadius;
    const startADeg = Math.atan2(u1y, u1x) * 180 / Math.PI;
    let endADeg = Math.atan2(u2y, u2x) * 180 / Math.PI;
    let diff = endADeg - startADeg;
    while (diff > 180) diff -= 360;
    while (diff < -180) diff += 360;
    endADeg = startADeg + diff;
    out += Prim.arc(vx, vy, arcR, startADeg, endADeg);
    // Label past the arc along bisector
    const loff = arcR + 13;
    const isGreek = /[θαβγδεφ]/.test(a.label);
    const lpos = labelTracker.place(vx + bx * loff, vy + by * loff, w, h, a.label ?? '');
    out += svgText(lpos.x, lpos.y, a.label, { italic: isGreek, fontSize: 13, textAnchor: 'middle', dominantBaseline: 'middle' });
  }

  // Vertex labels — place outward from centroid through vertex
  for (const key of keys) {
    const vx = V[key].x, vy = V[key].y;
    const dx = vx - cx, dy = vy - cy;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const ux = dx / len, uy = dy / len;
    const offset = 16;
    const lpos = labelTracker.place(vx + ux * offset, vy + uy * offset, w, h, V[key].label ?? key);
    out += svgText(lpos.x, lpos.y, V[key].label ?? key, { bold: true, fontSize: 13 });
  }

  const ct = autoCenterTransform(keys.map(k => ({ x: V[k].x, y: V[k].y })), w, h);
  return svgWrap(w, h, ct.open + out + ct.close);
}

// ── Shape: circle ───────────────────────────────────────────────────
function drawCircle(cfg) {
  const w  = cfg.width  ?? 240, h  = cfg.height ?? 240;
  const cx = cfg.cx     ?? w / 2, cy = cfg.cy  ?? h / 2;
  const r  = cfg.radius ?? Math.min(w, h) / 2 - 20;
  let out = '';

  // Sectors (draw before circle outline so it's inside)
  for (const sec of (cfg.sectors ?? [])) {
    const startRad = sec.fromAngle * Math.PI / 180;
    const endRad   = sec.toAngle   * Math.PI / 180;
    const x1 = cx + r * Math.cos(startRad), y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad),   y2 = cy + r * Math.sin(endRad);
    const sweep = ((sec.toAngle - sec.fromAngle + 360) % 360);
    const large = sweep > 180 ? 1 : 0;
    out += `<path d="M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large},1 ${x2.toFixed(2)},${y2.toFixed(2)} Z" fill="${sec.fillColor ?? '#dbeafe'}" stroke="none"/>`;
    if (sec.label) {
      const midAngle = (sec.fromAngle + sec.toAngle) / 2 * Math.PI / 180;
      const lx = cx + r * 0.6 * Math.cos(midAngle);
      const ly = cy + r * 0.6 * Math.sin(midAngle);
      const lpos = clampLabel(lx, ly, w, h);
      out += svgText(lpos.x, lpos.y, sec.label, { fontSize: 11, bold: true, fill: '#1e293b' });
    }
    // Central angle arc — small arc near center showing the angle with its degree value
    const angleVal = sec.centralAngle ?? sec.angle ?? null;
    if (angleVal != null) {
      const arcSweep = ((sec.toAngle - sec.fromAngle) + 360) % 360 || 360;
      const smallR   = Math.min(r * 0.22, 26);
      const startR2  = sec.fromAngle * Math.PI / 180;
      const endR2    = sec.toAngle   * Math.PI / 180;
      const ax1 = cx + smallR * Math.cos(startR2), ay1 = cy + smallR * Math.sin(startR2);
      const ax2 = cx + smallR * Math.cos(endR2),   ay2 = cy + smallR * Math.sin(endR2);
      const lg2 = arcSweep > 180 ? 1 : 0;
      out += `<path d="M${ax1.toFixed(2)},${ay1.toFixed(2)} A${smallR},${smallR} 0 ${lg2},1 ${ax2.toFixed(2)},${ay2.toFixed(2)}" fill="none" stroke="#334155" stroke-width="1.3"/>`;
      // Degree label outside the small arc along the bisector
      const midA2 = ((sec.fromAngle + sec.toAngle) / 2) * Math.PI / 180;
      const aLoff = smallR + 14;
      const aLpos = clampLabel(cx + aLoff * Math.cos(midA2), cy + aLoff * Math.sin(midA2), w, h);
      out += svgText(aLpos.x, aLpos.y, String(angleVal), { fontSize: 11, italic: true, fill: '#334155' });
    }
  }

  // Circle outline
  out += Prim.circle(cx, cy, r);

  // Arcs
  for (const arc of (cfg.arcs ?? [])) {
    const arcSC = arc.style?.stroke ?? arc.color ?? '#334155';
    const arcSW = arc.style?.strokeWidth ?? 1.5;
    // Use always-clockwise sweep (mimicking original behavior: sweep=1 always for arcs)
    let arcDiff = ((arc.toAngle - arc.fromAngle) % 360 + 360) % 360;
    out += Prim.arc(cx, cy, r, arc.fromAngle, arc.fromAngle + arcDiff, {
      stroke: arcSC, strokeWidth: arcSW
    });
    if (arc.label) {
      const midAngle = ((arc.fromAngle + arc.toAngle) / 2) * Math.PI / 180;
      const lx = cx + (r + 14) * Math.cos(midAngle);
      const ly = cy + (r + 14) * Math.sin(midAngle);
      const lpos = clampLabel(lx, ly, w, h);
      out += svgText(lpos.x, lpos.y, arc.label, { fontSize: 11 });
    }
  }

  // Radii
  for (const rad of (cfg.radii ?? [])) {
    const angle = rad.angle * Math.PI / 180;
    const ex = cx + r * Math.cos(angle), ey = cy + r * Math.sin(angle);
    const sc = rad.style?.stroke      ?? '#334155';
    const sw = rad.style?.strokeWidth ?? 1.5;
    out += `<line x1="${cx}" y1="${cy}" x2="${ex.toFixed(2)}" y2="${ey.toFixed(2)}" stroke="${sc}" stroke-width="${sw}"/>`;
    if (rad.label) {
      const lx = cx + (r / 2) * Math.cos(angle);
      const ly = cy + (r / 2) * Math.sin(angle);
      // Offset perpendicular to radius for label
      const perpX = -Math.sin(angle) * 10, perpY = Math.cos(angle) * 10;
      const lpos = clampLabel(lx + perpX, ly + perpY, w, h);
      out += svgText(lpos.x, lpos.y, rad.label, { italic: true, fontSize: 13 });
    }
  }

  // Chords
  for (const ch of (cfg.chords ?? [])) {
    const startRad = (ch.fromAngle ?? 0) * Math.PI / 180;
    const endRad   = (ch.toAngle   ?? 90) * Math.PI / 180;
    const x1 = cx + r * Math.cos(startRad), y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad),   y2 = cy + r * Math.sin(endRad);
    const chSC = ch.style?.stroke      ?? '#334155';
    const chSW = ch.style?.strokeWidth ?? 1.5;
    const chDA = (typeof ch.style === 'string' && ch.style === 'dashed') ? '5,4' : (ch.style?.strokeDasharray ?? undefined);
    out += Prim.line(x1, y1, x2, y2, { stroke: chSC, strokeWidth: chSW, strokeDasharray: chDA });
    if (ch.label) {
      const midAngle = ((ch.fromAngle + ch.toAngle) / 2) * Math.PI / 180;
      const lx = cx + (r * 0.5) * Math.cos(midAngle);
      const ly = cy + (r * 0.5) * Math.sin(midAngle);
      const lpos = clampLabel(lx, ly, w, h);
      out += svgText(lpos.x, lpos.y, ch.label, { fontSize: 11 });
    }
  }

  // Tangents
  for (const tan of (cfg.tangents ?? [])) {
    const angle = tan.angle * Math.PI / 180;
    // Point of tangency on the circle
    const tx = cx + r * Math.cos(angle), ty = cy + r * Math.sin(angle);
    // Tangent direction is perpendicular to the radius
    const tDirX = -Math.sin(angle), tDirY = Math.cos(angle);
    const len = tan.length ?? 60;
    const ta1x = tx + tDirX * len, ta1y = ty + tDirY * len;
    const ta2x = tx - tDirX * len, ta2y = ty - tDirY * len;
    const tanSC = tan.style?.stroke      ?? '#334155';
    const tanSW = tan.style?.strokeWidth ?? 1.5;
    out += Prim.line(ta1x, ta1y, ta2x, ta2y, { stroke: tanSC, strokeWidth: tanSW });
    // Right angle marker at tangency point (between radius and tangent)
    out += rightAngleSquare(tx, ty, cx, cy, ta1x, ta1y);
    // Tangency point dot
    out += `<circle cx="${tx.toFixed(2)}" cy="${ty.toFixed(2)}" r="3" fill="#334155"/>`;
    if (tan.label) {
      const lpos = clampLabel(tx + tDirX * (len + 14), ty + tDirY * (len + 14), w, h);
      out += svgText(lpos.x, lpos.y, tan.label, { italic: true, fontSize: 13 });
    }
  }

  // Inscribed angles
  for (const ia of (cfg.inscribedAngles ?? [])) {
    const vAngle = ia.vertex * Math.PI / 180;
    const fromAngle = ia.from * Math.PI / 180;
    const toAngle = ia.to * Math.PI / 180;
    // Vertex point, from point, to point — all on the circle
    const vx = cx + r * Math.cos(vAngle), vy = cy + r * Math.sin(vAngle);
    const fpx = cx + r * Math.cos(fromAngle), fpy = cy + r * Math.sin(fromAngle);
    const tpx = cx + r * Math.cos(toAngle), tpy = cy + r * Math.sin(toAngle);
    // Lines from vertex to both points
    out += `<line x1="${vx.toFixed(2)}" y1="${vy.toFixed(2)}" x2="${fpx.toFixed(2)}" y2="${fpy.toFixed(2)}" stroke="#334155" stroke-width="1.5"/>`;
    out += `<line x1="${vx.toFixed(2)}" y1="${vy.toFixed(2)}" x2="${tpx.toFixed(2)}" y2="${tpy.toFixed(2)}" stroke="#334155" stroke-width="1.5"/>`;
    // Vertex dot
    out += `<circle cx="${vx.toFixed(2)}" cy="${vy.toFixed(2)}" r="3" fill="#334155"/>`;
    // Angle arc at vertex
    if (ia.label) {
      out += drawAngleArcLabel(vx, vy, { x: fpx, y: fpy }, { x: tpx, y: tpy }, ia.label, w, h);
    }
  }

  // Annulus — inner circle (ring / donut shape)
  if (cfg.innerRadius != null) {
    const ir = cfg.innerRadius;
    out += `<circle cx="${cx}" cy="${cy}" r="${ir.toFixed ? ir.toFixed(2) : ir}" fill="#f8fafc" stroke="#334155" stroke-width="1.5"/>`;
    // Inner radius label
    if (cfg.labels?.innerRadius) {
      out += svgText(cx + ir / 2, cy - 6, cfg.labels.innerRadius, { italic: true, fontSize: 12 });
    }
    // Outer radius label (along a radius, avoiding inner circle)
    if (cfg.labels?.outerRadius ?? cfg.labels?.radius) {
      const lbl = cfg.labels.outerRadius ?? cfg.labels.radius;
      out += svgText(cx + (r + ir) / 2 + 4, cy - 6, lbl, { italic: true, fontSize: 12 });
    }
  }

  // Inscribed polygon (polygon whose vertices all lie on the circle)
  if (cfg.inscribedPolygon) {
    const ip = cfg.inscribedPolygon;
    const n  = ip.sides ?? 3;
    const rotRad = ((ip.rotationDeg ?? 90) - 90) * Math.PI / 180;
    const verts  = Array.from({length: n}, (_, i) => {
      const a = rotRad + (2 * Math.PI * i) / n;
      return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a), a };
    });
    const pts = verts.map(v => `${v.x.toFixed(2)},${v.y.toFixed(2)}`).join(' ');
    out += `<polygon points="${pts}" fill="none" stroke="#334155" stroke-width="1.5"/>`;
    // Vertex labels
    const vlabels = ip.vertexLabels ?? [];
    verts.forEach((v, i) => {
      const lbl = vlabels[i];
      if (!lbl) return;
      const lpos = clampLabel(cx + (r + 14) * Math.cos(v.a), cy + (r + 14) * Math.sin(v.a), w, h);
      out += svgText(lpos.x, lpos.y, lbl, { bold: true, fontSize: 13 });
    });
    // Side labels
    const slabels = ip.sideLabels ?? [];
    verts.forEach((v, i) => {
      const next = verts[(i + 1) % n];
      const lbl  = slabels[i];
      if (!lbl) return;
      const mx = (v.x + next.x) / 2, my = (v.y + next.y) / 2;
      // Offset toward center
      const dx = cx - mx, dy = cy - my;
      const dl = Math.sqrt(dx*dx + dy*dy) || 1;
      const lpos = clampLabel(mx + (dx/dl)*14, my + (dy/dl)*14, w, h);
      out += svgText(lpos.x, lpos.y, lbl, { italic: true, fontSize: 12 });
    });
  }

  // Circumscribed polygon (polygon whose sides are all tangent to the circle)
  if (cfg.circumscribedPolygon) {
    const cp2 = cfg.circumscribedPolygon;
    const n   = cp2.sides ?? 4;
    const rotRad = ((cp2.rotationDeg ?? 0) - 90) * Math.PI / 180;
    // Each side is tangent to the circle at radius r; vertex distance = r / cos(π/n)
    const vr = r / Math.cos(Math.PI / n);
    const verts = Array.from({length: n}, (_, i) => {
      const a = rotRad + (2 * Math.PI * i) / n;
      return { x: cx + vr * Math.cos(a), y: cy + vr * Math.sin(a), a };
    });
    const pts = verts.map(v => `${v.x.toFixed(2)},${v.y.toFixed(2)}`).join(' ');
    out += `<polygon points="${pts}" fill="none" stroke="#334155" stroke-width="1.5"/>`;
    const vlabels = cp2.vertexLabels ?? [];
    verts.forEach((v, i) => {
      const lbl = vlabels[i];
      if (!lbl) return;
      const lpos = clampLabel(cx + (vr + 14) * Math.cos(v.a), cy + (vr + 14) * Math.sin(v.a), w, h);
      out += svgText(lpos.x, lpos.y, lbl, { bold: true, fontSize: 13 });
    });
  }

  // Center dot + label
  if (cfg.center?.show) {
    out += `<circle cx="${cx}" cy="${cy}" r="3" fill="#334155"/>`;
    const lpos = clampLabel(cx - 12, cy - 10, w, h);
    out += svgText(lpos.x, lpos.y, cfg.center.label ?? 'O', { bold: true, fontSize: 13 });
  }

  // Points on circle (ALWAYS calculated from angle)
  for (const pt of (cfg.points ?? [])) {
    const angle = (pt.angle ?? 0) * Math.PI / 180;
    const px = cx + r * Math.cos(angle), py = cy + r * Math.sin(angle);
    out += `<circle cx="${px.toFixed(2)}" cy="${py.toFixed(2)}" r="3.5" fill="#334155"/>`;
    if (pt.label) {
      const _opts = resolveRenderOpts(cfg);
      const _off = _opts.pointLabelOffset;
      const _prad = (pt.angle ?? 0) * Math.PI / 180;
      let lx, ly;
      switch (pt.labelPosition) {
        case 'above': lx = px;        ly = py - _off; break;
        case 'below': lx = px;        ly = py + _off; break;
        case 'left':  lx = px - _off; ly = py;        break;
        case 'right': lx = px + _off; ly = py;        break;
        default: // auto — radial outward (existing behavior)
          lx = cx + (r + _off) * Math.cos(_prad);
          ly = cy + (r + _off) * Math.sin(_prad);
      }
      const lpos = clampLabel(lx, ly, w, h);
      out += svgText(lpos.x, lpos.y, pt.label, { bold: true, fontSize: 13 });
    }
  }

  return svgWrap(w, h, out);
}

// ── Shape: number_line ──────────────────────────────────────────────
function drawNumberLine(cfg) {
  const W = cfg.width ?? 320, H = cfg.height ?? 80;
  const pad = 36, lineY = H / 2 + 2;
  const min = cfg.min ?? -4, max = cfg.max ?? 4, step = cfg.step ?? 1;
  const scale = (W - 2 * pad) / (max - min);

  function toX(v) { return pad + (v - min) * scale; }

  let out = '';

  // Shading
  for (const sh of (cfg.shading ?? [])) {
    const x1 = toX(sh.from), x2 = toX(sh.to);
    out += `<rect x="${x1.toFixed(2)}" y="${(lineY - 10).toFixed(2)}" width="${(x2 - x1).toFixed(2)}" height="20" fill="${sh.color ?? '#dbeafe'}" rx="2"/>`;
  }

  // Line + arrowheads
  out += Prim.line(pad - 14, lineY, W - pad + 14, lineY, { strokeWidth: 1.5 });
  out += arrowHead(pad - 14, lineY, W - pad + 16, lineY, '#334155');
  out += arrowHead(W - pad + 14, lineY, pad - 16, lineY, '#334155');

  // Ticks + labels
  for (let v = min; v <= max + 0.001; v += step) {
    const x = toX(v);
    out += Prim.line(x, lineY - 5, x, lineY + 5, { strokeWidth: 1.5 });
    out += svgText(x, lineY + 18, v.toString(), { fontSize: 11, fill: '#475569' });
  }

  // Points
  for (const pt of (cfg.points ?? [])) {
    const x = toX(pt.value);
    const color = pt.color ?? '#334155';
    if (pt.type === 'open') {
      out += Prim.circle(x, lineY, 6, { fill: '#fff', stroke: color, strokeWidth: 2 });
    } else {
      out += Prim.circle(x, lineY, 6, { fill: color, stroke: color, strokeWidth: 1 });
    }
    if (pt.label) {
      const lpos = clampLabel(x, lineY - 16, W, H);
      out += svgText(lpos.x, lpos.y, pt.label, { fontSize: 11, bold: true, fill: color });
    }
  }

  return svgWrap(W, H, out);
}

// ── Shape: rectangle ────────────────────────────────────────────────
function drawRectangle(cfg) {
  const w = cfg.width ?? 260, h = cfg.height ?? 200;
  const shapeFill   = cfg.style?.fill        ?? '#dbeafe';
  const shapeStroke = cfg.style?.stroke      ?? '#1d4ed8';
  const shapeSW     = cfg.style?.strokeWidth ?? 2.2;
  let out = '';

  // ── Vertex-based rendering (modern format: vertices + sides[]) ──────
  // When the diagram was generated with explicit vertex coordinates
  // (same format as triangles and parallelograms), use those directly
  // so the question diagram shows labels and measurements.
  const V = cfg.vertices ?? {};
  const vkeys = Object.keys(V);
  if (vkeys.length >= 4) {
    const pts = vkeys.map(k => `${V[k].x},${V[k].y}`).join(' ');
    out += `<polygon points="${pts}" fill="${shapeFill}" stroke="${shapeStroke}" stroke-width="${shapeSW}"/>`;

    // Centroid for outward label placement
    const cx = vkeys.reduce((s, k) => s + V[k].x, 0) / vkeys.length;
    const cy = vkeys.reduce((s, k) => s + V[k].y, 0) / vkeys.length;

    // Side labels from sides[] array
    for (const s of (cfg.sides ?? [])) {
      const p1 = V[s.from], p2 = V[s.to];
      if (!p1 || !p2 || !s.label) continue;
      const mid = midpoint(p1, p2);
      const dx = p2.x - p1.x, dy = p2.y - p1.y;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      let nx = -dy / len, ny = dx / len;
      // Push outward from centroid
      const toCx = mid.x - cx, toCy = mid.y - cy;
      if (nx * toCx + ny * toCy < 0) { nx = -nx; ny = -ny; }
      // Auto-offset: scale with text length so long labels clear the side
      const _fs = 13, _htw = (s.label.length * _fs * 0.55) / 2, _hth = _fs * 0.5;
      const _minX = Math.abs(nx) > 0.15 ? Math.min((_htw + 5) / Math.abs(nx), _htw + 8) : 0;
      const _minY = Math.abs(ny) > 0.15 ? Math.min((_hth + 4) / Math.abs(ny), _hth + 6) : 0;
      const offset = Math.max(16, _minX, _minY);
      const lpos = clampLabel(mid.x + nx * offset, mid.y + ny * offset, w, h);
      const color = s.color ?? '#2563eb';
      out += svgText(lpos.x, lpos.y, s.label, { fontSize: 13, fill: color });
    }

    // Vertex dots
    for (const k of vkeys) {
      out += `<circle cx="${V[k].x}" cy="${V[k].y}" r="4" fill="#1e293b"/>`;
    }

    // Vertex labels pushed 16px outward from centroid
    for (const k of vkeys) {
      const vx = V[k].x, vy = V[k].y;
      const ddx = vx - cx, ddy = vy - cy;
      const dlen = Math.sqrt(ddx * ddx + ddy * ddy) || 1;
      const lpos = clampLabel(vx + (ddx / dlen) * 16, vy + (ddy / dlen) * 16, w, h);
      out += svgText(lpos.x, lpos.y, k, { fontSize: 13, bold: true, textAnchor: 'middle', dominantBaseline: 'middle' });
    }

    const vpts = vkeys.map(k => ({ x: V[k].x, y: V[k].y }));
    const ct = autoCenterTransform(vpts, w, h);
    return svgWrap(w, h, ct.open + out + ct.close);
  }

  // ── Legacy rendering (older format: x/y/rectWidth/rectHeight) ───────
  const x = cfg.x ?? 30, y = cfg.y ?? 30;
  const rw = cfg.rectWidth ?? 180, rh = cfg.rectHeight ?? 120;

  out += `<rect x="${x}" y="${y}" width="${rw}" height="${rh}" fill="${shapeFill}" stroke="${shapeStroke}" stroke-width="${shapeSW}"/>`;

  const corners = {
    topLeft:     { x: x,      y: y      },
    topRight:    { x: x + rw, y: y      },
    bottomLeft:  { x: x,      y: y + rh },
    bottomRight: { x: x + rw, y: y + rh }
  };

  // Diagonals
  for (const d of (cfg.diagonals ?? [])) {
    const p1 = corners[d.from], p2 = corners[d.to];
    if (!p1 || !p2) continue;
    const dash  = d.style === 'dashed' ? 'stroke-dasharray="5,4"' : '';
    const color = d.color ?? '#334155';
    out += `<line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="${color}" stroke-width="1.5" ${dash}/>`;
    if (d.label) {
      const mid = midpoint(p1, p2);
      const lpos = clampLabel(mid.x + 10, mid.y - 8, w, h);
      out += svgText(lpos.x, lpos.y, d.label, { fontSize: 12, italic: true });
    }
  }

  // Right angle markers
  if (cfg.showRightAngles) {
    const sz = 10;
    out += rightAngleSquare(x,      y,      x + rw, y,      x,      y + rh, sz);
    out += rightAngleSquare(x + rw, y,      x,      y,      x + rw, y + rh, sz);
    out += rightAngleSquare(x,      y + rh, x,      y,      x + rw, y + rh, sz);
    out += rightAngleSquare(x + rw, y + rh, x + rw, y,      x,      y + rh, sz);
  }

  // Side labels (legacy top/bottom/left/right format)
  const lbs = cfg.labels ?? {};
  const rcx = x + rw / 2, rcy = y + rh / 2;
  if (lbs.top)    { const lp = clampLabel(rcx, y - 10,      w, h); out += svgText(lp.x, lp.y, lbs.top.text,    { fontSize: 13 }); }
  if (lbs.bottom) { const lp = clampLabel(rcx, y + rh + 14, w, h); out += svgText(lp.x, lp.y, lbs.bottom.text, { fontSize: 13 }); }
  if (lbs.left)   { const lp = clampLabel(x - 14, rcy,      w, h); out += svgText(lp.x, lp.y, lbs.left.text,   { fontSize: 13 }); }
  if (lbs.right)  { const lp = clampLabel(x + rw + 14, rcy, w, h); out += svgText(lp.x, lp.y, lbs.right.text,  { fontSize: 13 }); }

  const rectPoints = [{ x, y }, { x: x + rw, y }, { x, y: y + rh }, { x: x + rw, y: y + rh }];
  const ct = autoCenterTransform(rectPoints, w, h);
  return svgWrap(w, h, ct.open + out + ct.close);
}

// ── Shape: parallel_transversal ─────────────────────────────────────
function drawParallelTransversal(cfg) {
  const w = cfg.width ?? 260, h = cfg.height ?? 220;
  const line1Y  = cfg.line1Y  ?? 70;
  const line2Y  = cfg.line2Y  ?? 150;
  const tx1     = cfg.transversalX1 ?? 60;
  const tx2     = cfg.transversalX2 ?? 180;
  let out = '';

  // Parallel line tick marks (2 ticks on each)
  function parallelTick(y, x1, x2, n) {
    const mx = (x1 + x2) / 2, my = y;
    const ang = Math.atan2(0, x2 - x1); // horizontal
    const perpA = Math.PI / 2;
    const len = 7;
    const offsets = n === 1 ? [0] : [-5, 5];
    let s = '';
    for (const off of offsets) {
      const ox = off * Math.cos(ang);
      const t1x = mx + ox + len * Math.cos(perpA), t1y = my + len * Math.sin(perpA);
      const t2x = mx + ox - len * Math.cos(perpA), t2y = my - len * Math.sin(perpA);
      s += `<line x1="${t1x.toFixed(2)}" y1="${t1y.toFixed(2)}" x2="${t2x.toFixed(2)}" y2="${t2y.toFixed(2)}" stroke="#334155" stroke-width="1.5"/>`;
    }
    return s;
  }

  // Lines
  out += `<line x1="14" y1="${line1Y}" x2="${w - 14}" y2="${line1Y}" stroke="#334155" stroke-width="2"/>`;
  out += `<line x1="14" y1="${line2Y}" x2="${w - 14}" y2="${line2Y}" stroke="#334155" stroke-width="2"/>`;
  // Transversal
  const slope = (line2Y - line1Y) / (tx2 - tx1);
  const extX1 = 14, extX2 = w - 14;
  const extY1 = line1Y + slope * (extX1 - tx1);
  const extY2 = line1Y + slope * (extX2 - tx1);
  out += `<line x1="${extX1}" y1="${extY1.toFixed(2)}" x2="${extX2}" y2="${extY2.toFixed(2)}" stroke="#334155" stroke-width="2"/>`;

  // Parallel tick marks
  out += parallelTick(line1Y, 14, w - 14, 1);
  out += parallelTick(line2Y, 14, w - 14, 2);

  // Find intersection points
  function lineIntersectH(y, lx1, ly1, lx2, ly2) {
    const t = (y - ly1) / (ly2 - ly1);
    return lx1 + t * (lx2 - lx1);
  }
  const topX    = lineIntersectH(line1Y, extX1, extY1, extX2, extY2);
  const bottomX = lineIntersectH(line2Y, extX1, extY1, extX2, extY2);

  // Actual transversal angle: direction going right-downward (radians, SVG y-down space)
  const tA = Math.atan2(extY2 - extY1, extX2 - extX1);

  // Clockwise arc (sweep=1) from startA to endA, auto large-arc flag
  function drawAngleArc(cx, cy, r, startA, endA) {
    let end = endA;
    while (end <= startA) end += 2 * Math.PI;
    const span = end - startA;
    const largeArc = span > Math.PI ? 1 : 0;
    const x1 = (cx + r * Math.cos(startA)).toFixed(2);
    const y1 = (cy + r * Math.sin(startA)).toFixed(2);
    const x2 = (cx + r * Math.cos(end)).toFixed(2);
    const y2 = (cy + r * Math.sin(end)).toFixed(2);
    return `<path d="M${x1},${y1} A${r},${r} 0 ${largeArc},1 ${x2},${y2}" fill="none" stroke="#334155" stroke-width="1.2"/>`;
  }

  // Each position maps to a clockwise arc between two of the four ray directions:
  //   0       = right horizontal
  //   tA      = transversal going down-right
  //   π       = left horizontal
  //   π + tA  = transversal going up-left
  //   2π      = back to right (= 0)
  // bisA = angle of the sector bisector → used to place the label
  const positionDefs = {
    bottomRight: { startA: 0,            endA: tA,               bisA: tA / 2                    },
    bottomLeft:  { startA: tA,           endA: Math.PI,          bisA: (tA + Math.PI) / 2        },
    topLeft:     { startA: Math.PI,      endA: Math.PI + tA,     bisA: Math.PI + tA / 2          },
    topRight:    { startA: Math.PI + tA, endA: 2 * Math.PI,      bisA: 1.5 * Math.PI + tA / 2   }
  };
  const arcR    = 14;
  const labelR  = 26;

  for (const al of (cfg.angleLabels ?? [])) {
    const ix  = al.intersection === 'top' ? topX    : bottomX;
    const iy  = al.intersection === 'top' ? line1Y  : line2Y;
    const def = positionDefs[al.position];
    if (def) {
      out += drawAngleArc(ix, iy, arcR, def.startA, def.endA);
      const lx   = ix + labelR * Math.cos(def.bisA);
      const ly   = iy + labelR * Math.sin(def.bisA);
      const lpos = clampLabel(lx, ly, w, h);
      out += svgText(lpos.x, lpos.y, al.label, { fontSize: 12 });
    }
  }

  return svgWrap(w, h, out);
}

// ── Shape: triangle_with_altitude ───────────────────────────────────
function drawTriangleWithAltitude(cfg) {
  const V = cfg.vertices ?? {};
  const keys = Object.keys(V);
  const w = cfg.width ?? 280, h = cfg.height ?? 220;
  const pts = keys.map(k => `${V[k].x},${V[k].y}`).join(' ');
  const shapeFill   = cfg.style?.fill        ?? '#dbeafe';
  const shapeStroke = cfg.style?.stroke      ?? '#1d4ed8';
  const shapeSW     = cfg.style?.strokeWidth ?? 2.2;

  let out = '';
  out += `<polygon points="${pts}" fill="${shapeFill}" stroke="${shapeStroke}" stroke-width="${shapeSW}"/>`;

  // Calculate foot of altitude from altitudeFrom to the opposite side
  const fromKey  = cfg.altitudeFrom ?? 'C';
  const fromPt   = V[fromKey];
  const baseKeys = keys.filter(k => k !== fromKey);
  const p1 = V[baseKeys[0]], p2 = V[baseKeys[1]];

  // Project fromPt onto line p1-p2
  const dx = p2.x - p1.x, dy = p2.y - p1.y;
  const t = ((fromPt.x - p1.x) * dx + (fromPt.y - p1.y) * dy) / (dx * dx + dy * dy);
  const footX = p1.x + t * dx, footY = p1.y + t * dy;

  // Altitude line
  out += `<line x1="${fromPt.x}" y1="${fromPt.y}" x2="${footX.toFixed(2)}" y2="${footY.toFixed(2)}" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5,4"/>`;

  // Right angle at foot (between altitude and base)
  out += rightAngleSquare(footX, footY, fromPt.x, fromPt.y, p2.x, p2.y);

  // Altitude label at midpoint
  const altLabel = cfg.altitudeLabel ?? 'h';
  const midX = (fromPt.x + footX) / 2, midY = (fromPt.y + footY) / 2;
  const perpX = -(footY - fromPt.y) / (distance(fromPt, { x: footX, y: footY }) || 1) * 12;
  const perpY =  (footX - fromPt.x) / (distance(fromPt, { x: footX, y: footY }) || 1) * 12;
  const lpos = clampLabel(midX + perpX, midY + perpY, w, h);
  out += svgText(lpos.x, lpos.y, altLabel, { italic: true, fontSize: 13 });

  // Foot label
  const footLabel = cfg.footLabel ?? 'D';
  const footDir = { x: footX - (p1.x + p2.x) / 2, y: footY - (p1.y + p2.y) / 2 };
  const fdLen = Math.sqrt(footDir.x ** 2 + footDir.y ** 2) || 1;
  const flpos = clampLabel(footX + (footDir.x / fdLen) * 16, footY + (footDir.y / fdLen) * 16, w, h);
  out += svgText(flpos.x, flpos.y, footLabel, { bold: true, fontSize: 13 });

  // Side labels
  for (const s of (cfg.sides ?? [])) {
    const sp1 = V[s.from], sp2 = V[s.to];
    if (!sp1 || !sp2) continue;
    const mid = midpoint(sp1, sp2);
    const centX = keys.reduce((sum, k) => sum + V[k].x, 0) / keys.length;
    const centY = keys.reduce((sum, k) => sum + V[k].y, 0) / keys.length;
    const sdx = sp2.x - sp1.x, sdy = sp2.y - sp1.y;
    const slen = Math.sqrt(sdx * sdx + sdy * sdy) || 1;
    let snx = -sdy / slen, sny = sdx / slen;
    const toCx = mid.x - centX, toCy = mid.y - centY;
    if (snx * toCx + sny * toCy < 0) { snx = -snx; sny = -sny; }
    const slpos = clampLabel(mid.x + snx * 14, mid.y + sny * 14, w, h);
    out += svgText(slpos.x, slpos.y, s.label, { italic: true, fontSize: 13 });
  }

  // Centroid for vertex label placement
  const cx = keys.reduce((s, k) => s + V[k].x, 0) / keys.length;
  const cy = keys.reduce((s, k) => s + V[k].y, 0) / keys.length;
  for (const key of keys) {
    const vx = V[key].x, vy = V[key].y;
    const ddx = vx - cx, ddy = vy - cy;
    const dlen = Math.sqrt(ddx * ddx + ddy * ddy) || 1;
    const vlpos = clampLabel(vx + (ddx / dlen) * 16, vy + (ddy / dlen) * 16, w, h);
    out += svgText(vlpos.x, vlpos.y, key, { bold: true, fontSize: 13 });
  }

  const ct = autoCenterTransform(keys.map(k => ({ x: V[k].x, y: V[k].y })), w, h);
  return svgWrap(w, h, ct.open + out + ct.close);
}

// ── Shape: coordinate_plane ─────────────────────────────────────────
function drawCoordinatePlane(cfg) {
  const W = cfg.width ?? 280, H = cfg.height ?? 260;
  const _cp_opts = resolveRenderOpts(cfg);
  const padL = _cp_opts.padL, padR = _cp_opts.padR, padT = _cp_opts.padT, padB = _cp_opts.padB;
  const xMin = cfg.xMin ?? -5, xMax = cfg.xMax ?? 5;
  const yMin = cfg.yMin ?? -5, yMax = cfg.yMax ?? 5;
  const xSpan = xMax - xMin, ySpan = yMax - yMin;

  const planeCfg = { xMin, xMax, yMin, yMax, width: W, height: H, padL, padR, padT, padB };

  const T = makeTransform({ xMin, xMax, yMin, yMax, width: W, height: H, padL, padR, padT, padB });
  const toSVG = (mx, my) => T.toSVG(mx, my);

  const xStep = cfg.xStep ?? smartStep(xSpan);
  const yStep = cfg.yStep ?? smartStep(ySpan);

  const xAxisY = (yMin <= 0 && 0 <= yMax) ? 0 : yMin;
  const yAxisX = (xMin <= 0 && 0 <= xMax) ? 0 : xMin;

  let out = '';

  // ── Grid lines
  if (cfg.gridLines !== false) {
    const gxStart = Math.ceil(xMin / xStep) * xStep;
    for (let gx = gxStart; gx <= xMax + 0.001; gx += xStep) {
      const p1 = toSVG(gx, yMin), p2 = toSVG(gx, yMax);
      out += `<line x1="${p1.x.toFixed(2)}" y1="${p1.y.toFixed(2)}" x2="${p2.x.toFixed(2)}" y2="${p2.y.toFixed(2)}" stroke="#e2e8f0" stroke-width="0.5"/>`;
    }
    const gyStart = Math.ceil(yMin / yStep) * yStep;
    for (let gy = gyStart; gy <= yMax + 0.001; gy += yStep) {
      const p1 = toSVG(xMin, gy), p2 = toSVG(xMax, gy);
      out += `<line x1="${p1.x.toFixed(2)}" y1="${p1.y.toFixed(2)}" x2="${p2.x.toFixed(2)}" y2="${p2.y.toFixed(2)}" stroke="#e2e8f0" stroke-width="0.5"/>`;
    }
  }

  // ── Subtype-specific content
  const subtype = cfg.subtype ?? 'basic';

  if (subtype === 'inequality') {
    // Draw shading BEFORE lines
    for (const ineq of (cfg.inequalities ?? [])) {
      const fc = ineq.fillColor ?? '#dbeafe';
      const bc = ineq.borderColor ?? '#2563eb';
      const lineStyle = ineq.lineStyle ?? (ineq.operator?.includes('e') ? 'solid' : 'dashed');

      // Build fill polygon: trace the function, then go to top/bottom edge
      const shadeAbove = ineq.shadeAbove ?? (ineq.operator === 'gt' || ineq.operator === 'gte');
      const steps = 200;
      const xStepF = xSpan / steps;
      const polyPts = [];
      const validPts = [];

      for (let i = 0; i <= steps; i++) {
        const mx = xMin + i * xStepF;
        const my = evaluateFunction(ineq, mx);
        if (my === null || !isFinite(my)) continue;
        const p = toSVG(mx, Math.max(yMin, Math.min(yMax, my)));
        validPts.push(p);
        polyPts.push(`${p.x.toFixed(2)},${p.y.toFixed(2)}`);
      }

      if (validPts.length > 1) {
        const topEdgeY = toSVG(xMin, yMax).y;
        const botEdgeY = toSVG(xMin, yMin).y;
        const edgeY    = shadeAbove ? topEdgeY : botEdgeY;
        const firstX   = validPts[0].x, lastX = validPts[validPts.length - 1].x;

        const fullPoly = [
          ...polyPts,
          `${lastX.toFixed(2)},${edgeY.toFixed(2)}`,
          `${firstX.toFixed(2)},${edgeY.toFixed(2)}`
        ].join(' ');

        out += `<polygon points="${fullPoly}" fill="${fc}" fill-opacity="0.4" stroke="none"/>`;
        const dash = lineStyle === 'dashed' ? 'stroke-dasharray="5,4"' : '';
        // Draw boundary line
        for (const fi of (cfg.inequalities ?? [])) {
          if (fi !== ineq) continue;
          out += plotFunction(ineq, planeCfg, xMin, xMax, bc, 2, lineStyle === 'dashed' ? '5,4' : '');
        }
      }
    }
  }

  if (subtype === 'piecewise') {
    for (const piece of (cfg.pieces ?? [])) {
      const dMin = piece.domainMin ?? xMin, dMax = piece.domainMax ?? xMax;
      const color = piece.color ?? '#2563eb';
      out += plotFunction(piece, planeCfg, dMin, dMax, color, 2);

      // Endpoint markers
      const endpointTypes = [
        { domain: dMin, type: piece.leftEndpoint  ?? 'none' },
        { domain: dMax, type: piece.rightEndpoint ?? 'none' }
      ];
      for (const ep of endpointTypes) {
        if (ep.type === 'none') continue;
        const y = evaluateFunction(piece, ep.domain);
        if (y === null) continue;
        const pp = toSVG(ep.domain, y);
        if (ep.type === 'open') {
          out += `<circle cx="${pp.x.toFixed(2)}" cy="${pp.y.toFixed(2)}" r="4" fill="#fff" stroke="${color}" stroke-width="2"/>`;
        } else if (ep.type === 'closed') {
          out += `<circle cx="${pp.x.toFixed(2)}" cy="${pp.y.toFixed(2)}" r="4" fill="${color}"/>`;
        }
      }
    }
  }

  // ── Between-curves shading (works on any subtype)
  for (const region of (cfg.regions ?? [])) {
    const fc   = region.fillColor ?? '#dbeafe';
    const steps = 200;
    const rxMin = region.xMin ?? xMin, rxMax = region.xMax ?? xMax;
    const xStep = (rxMax - rxMin) / steps;
    // Build polygon: trace fn1 left→right, then fn2 right→left
    const topPts = [], botPts = [];
    for (let i = 0; i <= steps; i++) {
      const mx = rxMin + i * xStep;
      const y1 = evaluateFunction(region.function1, mx);
      const y2 = evaluateFunction(region.function2, mx);
      if (y1 === null || y2 === null || !isFinite(y1) || !isFinite(y2)) continue;
      const upper = Math.min(yMax, Math.max(yMin, Math.max(y1, y2)));
      const lower = Math.min(yMax, Math.max(yMin, Math.min(y1, y2)));
      const pTop = toSVG(mx, upper);
      const pBot = toSVG(mx, lower);
      topPts.push(`${pTop.x.toFixed(2)},${pTop.y.toFixed(2)}`);
      botPts.push(`${pBot.x.toFixed(2)},${pBot.y.toFixed(2)}`);
    }
    if (topPts.length > 1) {
      const poly = [...topPts, ...[...botPts].reverse()].join(' ');
      out += `<polygon points="${poly}" fill="${fc}" fill-opacity="0.45" stroke="none"/>`;
    }
    // Draw both boundary curves
    if (region.function1) out += plotFunction(region.function1, planeCfg, rxMin, rxMax, region.color1 ?? '#2563eb', 2);
    if (region.function2) out += plotFunction(region.function2, planeCfg, rxMin, rxMax, region.color2 ?? '#dc2626', 2);
    // Region label at midpoint
    if (region.label) {
      const midX = (rxMin + rxMax) / 2;
      const y1m  = evaluateFunction(region.function1, midX) ?? 0;
      const y2m  = evaluateFunction(region.function2, midX) ?? 0;
      const midY = (y1m + y2m) / 2;
      const lp   = toSVG(midX, midY);
      out += svgText(lp.x, lp.y, region.label, { fontSize: 11, fill: '#475569', bold: true });
    }
  }

  if (subtype === 'function_graph' || subtype === 'system_of_equations') {
    for (const fn of (cfg.functions ?? [])) {
      const sc = fn.style?.stroke          ?? fn.color       ?? '#334155';
      const sw = fn.style?.strokeWidth     ?? fn.strokeWidth ?? 2;
      const da = fn.style?.strokeDasharray ?? '';
      out += plotFunction(fn, planeCfg, xMin, xMax, sc, sw, da);
      // Optional function label at a specific coordinate
      if (fn.label && fn.labelAt) {
        const _flp = toSVG(fn.labelAt.x, fn.labelAt.y);
        const _fpos = clampLabel(_flp.x + 6, _flp.y - 6, W, H);
        out += svgText(_fpos.x, _fpos.y, fn.label, { fontSize: 11, fill: sc, textAnchor: 'start' });
      }
    }
  }

  if (subtype === 'basic') {
    // Named segments
    for (const seg of (cfg.segments ?? [])) {
      const sp1 = toSVG(seg.from.x, seg.from.y), sp2 = toSVG(seg.to.x, seg.to.y);
      const dash = seg.style === 'dashed' ? 'stroke-dasharray="5,4"' : '';
      out += `<line x1="${sp1.x.toFixed(2)}" y1="${sp1.y.toFixed(2)}" x2="${sp2.x.toFixed(2)}" y2="${sp2.y.toFixed(2)}" stroke="${seg.color ?? '#334155'}" stroke-width="1.5" ${dash}/>`;
    }
  }

  // ── Axes
  const axisXStart = toSVG(xMin, xAxisY), axisXEnd = toSVG(xMax, xAxisY);
  const axisYStart = toSVG(yAxisX, yMin), axisYEnd = toSVG(yAxisX, yMax);

  out += `<line x1="${axisXStart.x.toFixed(2)}" y1="${axisXStart.y.toFixed(2)}" x2="${axisXEnd.x.toFixed(2)}" y2="${axisXEnd.y.toFixed(2)}" stroke="#334155" stroke-width="1.5"/>`;
  out += `<line x1="${axisYStart.x.toFixed(2)}" y1="${axisYStart.y.toFixed(2)}" x2="${axisYEnd.x.toFixed(2)}" y2="${axisYEnd.y.toFixed(2)}" stroke="#334155" stroke-width="1.5"/>`;
  out += arrowHead(axisXStart.x, axisXStart.y, axisXEnd.x + 10, axisXEnd.y);
  out += arrowHead(axisYStart.x, axisYStart.y, axisYEnd.x, axisYEnd.y - 10);

  // ── X-axis ticks + labels
  const xTickStart = Math.ceil(xMin / xStep) * xStep;
  for (let gx = xTickStart; gx <= xMax + 0.001; gx += xStep) {
    const p = toSVG(gx, xAxisY);
    out += `<line x1="${p.x.toFixed(2)}" y1="${(p.y - 4).toFixed(2)}" x2="${p.x.toFixed(2)}" y2="${(p.y + 4).toFixed(2)}" stroke="#334155" stroke-width="1"/>`;
    // Skip origin label if both axes cross at 0
    if (Math.abs(gx) < 0.001 && Math.abs(yAxisX) < 0.001 && Math.abs(xAxisY) < 0.001) continue;
    out += svgText(p.x, p.y + 14, gx.toString(), { fontSize: 10, fill: '#64748b' });
  }

  // ── Y-axis ticks + labels
  const yTickStart = Math.ceil(yMin / yStep) * yStep;
  for (let gy = yTickStart; gy <= yMax + 0.001; gy += yStep) {
    const p = toSVG(yAxisX, gy);
    out += `<line x1="${(p.x - 4).toFixed(2)}" y1="${p.y.toFixed(2)}" x2="${(p.x + 4).toFixed(2)}" y2="${p.y.toFixed(2)}" stroke="#334155" stroke-width="1"/>`;
    if (Math.abs(gy) < 0.001 && Math.abs(yAxisX) < 0.001 && Math.abs(xAxisY) < 0.001) continue;
    out += svgText(p.x - 8, p.y, gy.toString(), { fontSize: 10, fill: '#64748b', textAnchor: 'end' });
  }

  // ── Axis labels
  const xLabelText   = cfg.xAxis?.label ?? 'x';
  const xLabelItalic = !cfg.xAxis?.label;
  out += svgText((axisXStart.x + axisXEnd.x) / 2, H - 6, xLabelText, { fontSize: 10, fill: '#475569', italic: xLabelItalic });

  const yLabelText   = cfg.yAxis?.label ?? 'y';
  const yLabelItalic = !cfg.yAxis?.label;
  const ylx = 10, yly = (axisYStart.y + axisYEnd.y) / 2;
  out += `<text x="${ylx}" y="${yly.toFixed(2)}" text-anchor="middle" dominant-baseline="middle" font-size="10" font-family="system-ui, sans-serif" font-style="${yLabelItalic ? 'italic' : 'normal'}" fill="#475569" transform="rotate(-90, ${ylx}, ${yly.toFixed(2)})">${yLabelText}</text>`;

  // ── Data points (all subtypes)
  for (const pt of (cfg.points ?? [])) {
    const p = toSVG(pt.x, pt.y);
    const ptColor = pt.color ?? '#2563eb';
    out += `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="${cfg.pointRadius ?? 4}" fill="${ptColor}"/>`;
    if (pt.label) {
      const lpos = clampLabel(p.x + 8, p.y - 8, W, H);
      out += svgText(lpos.x, lpos.y, pt.label, { fontSize: 11, fill: ptColor, textAnchor: 'start' });
    }
  }

  // ── Regression line (svg_programmatic scatter diagrams)
  if (cfg.regressionLine) {
    const rl = cfg.regressionLine;
    const rlSlope = rl.slope ?? 0, rlInt = rl.intercept ?? 0;
    const rlColor = rl.color ?? '#dc2626';
    const rlWidth = rl.strokeWidth ?? rl['stroke-width'] ?? 2;
    // Clip line to visible x and y range
    let rxLo = xMin, rxHi = xMax;
    if (Math.abs(rlSlope) > 1e-9) {
      const xAtYMin = (yMin - rlInt) / rlSlope;
      const xAtYMax = (yMax - rlInt) / rlSlope;
      rxLo = Math.max(rxLo, Math.min(xAtYMin, xAtYMax));
      rxHi = Math.min(rxHi, Math.max(xAtYMin, xAtYMax));
    }
    if (rxLo < rxHi) {
      const p1 = toSVG(rxLo, rlSlope * rxLo + rlInt);
      const p2 = toSVG(rxHi, rlSlope * rxHi + rlInt);
      out += `<line x1="${p1.x.toFixed(2)}" y1="${p1.y.toFixed(2)}" x2="${p2.x.toFixed(2)}" y2="${p2.y.toFixed(2)}" stroke="${rlColor}" stroke-width="${rlWidth}" stroke-dasharray="5,4"/>`;
    }
  }

  // ── Intersection points (system_of_equations)
  for (const inter of (cfg.intersections ?? [])) {
    const p = toSVG(inter.x, inter.y);
    out += `<circle cx="${p.x.toFixed(2)}" cy="${p.y.toFixed(2)}" r="4.5" fill="#7c3aed"/>`;
    if (inter.label) {
      const lpos = clampLabel(p.x + 9, p.y - 9, W, H);
      out += svgText(lpos.x, lpos.y, inter.label, { fontSize: 11, fill: '#7c3aed', textAnchor: 'start' });
    }
  }

  return svgWrap(W, H, out);
}

// ── Generic elements[] fallback ─────────────────────────────────────
function renderSVGElements(cfg) {
  const w = cfg.width ?? 300, h = cfg.height ?? 200;
  let out = '';
  for (const el of (cfg.elements ?? [])) {
    const sw = el.strokeWidth ?? el['stroke-width'] ?? 1;
    const sc = el.stroke ?? 'none';
    const fc = el.fill ?? 'none';
    switch (el.type) {
      case 'line':
        out += `<line x1="${el.x1}" y1="${el.y1}" x2="${el.x2}" y2="${el.y2}" stroke="${sc}" stroke-width="${sw}"/>`;
        break;
      case 'rect':
        out += `<rect x="${el.x}" y="${el.y}" width="${el.width}" height="${el.height}" fill="${fc}" stroke="${sc}" stroke-width="${sw}" rx="${el.rx ?? 0}"/>`;
        break;
      case 'circle':
        out += `<circle cx="${el.cx ?? el.x}" cy="${el.cy ?? el.y}" r="${el.r ?? el.radius ?? 10}" fill="${fc}" stroke="${sc}" stroke-width="${sw}"/>`;
        break;
      case 'polygon':
        out += `<polygon points="${el.points}" fill="${fc}" stroke="${sc}" stroke-width="${sw}"/>`;
        break;
      case 'ellipse':
        out += `<ellipse cx="${el.cx}" cy="${el.cy}" rx="${el.rx}" ry="${el.ry}" fill="${fc}" stroke="${sc}" stroke-width="${sw}"/>`;
        break;
      case 'path':
        out += `<path d="${el.d}" fill="${fc}" stroke="${sc}" stroke-width="${sw}"/>`;
        break;
      case 'arc': {
        // Circular arc: startAngle/endAngle in degrees, 0°=right, clockwise (SVG coords)
        const ar = el.r ?? el.radius ?? 30;
        const sa = (el.startAngle ?? 0) * Math.PI / 180;
        const ea = (el.endAngle   ?? 90) * Math.PI / 180;
        const ax1 = (el.cx ?? el.x ?? 0) + ar * Math.cos(sa);
        const ay1 = (el.cy ?? el.y ?? 0) + ar * Math.sin(sa);
        const ax2 = (el.cx ?? el.x ?? 0) + ar * Math.cos(ea);
        const ay2 = (el.cy ?? el.y ?? 0) + ar * Math.sin(ea);
        const largeArc = Math.abs((el.endAngle ?? 90) - (el.startAngle ?? 0)) > 180 ? 1 : 0;
        out += `<path d="M ${ax1} ${ay1} A ${ar} ${ar} 0 ${largeArc} 1 ${ax2} ${ay2}" fill="${fc}" stroke="${sc}" stroke-width="${sw}"/>`;
        break;
      }
      case 'text': {
        const fs  = el.fontSize  ?? 13;
        const fw  = el.fontWeight ?? 'normal';
        const fst = el.fontStyle ?? 'normal';
        const ta  = el.textAnchor ?? el['text-anchor'] ?? 'start';
        const tc  = el.fill ?? '#1e293b';
        out += `<text x="${el.x}" y="${el.y}" font-size="${fs}" font-weight="${fw}" font-style="${fst}" text-anchor="${ta}" fill="${tc}" font-family="Georgia, serif">${el.text ?? ''}</text>`;
        break;
      }
    }
  }
  return svgWrap(w, h, out);
}

// ── SVG Pie chart (sections-based, for svg_programmatic) ────────────
function renderSVGPieChart(cfg) {
  const w = cfg.width ?? 300, h = cfg.height ?? 300;
  const cx = cfg.centerX ?? w / 2, cy = cfg.centerY ?? h / 2;
  const r  = cfg.radius  ?? Math.min(w, h) / 2 - 30;
  const sections = cfg.sections ?? [];
  let out = '';

  if (cfg.title) {
    out += svgText(w / 2, 14, cfg.title, { fontSize: 11, bold: true });
  }

  sections.forEach(sec => {
    const startRad = (sec.startAngle - 90) * Math.PI / 180;
    const endRad   = (sec.startAngle + sec.angle - 90) * Math.PI / 180;
    const x1 = cx + r * Math.cos(startRad), y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad),   y2 = cy + r * Math.sin(endRad);
    const large = sec.angle > 180 ? 1 : 0;
    out += `<path d="M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large},1 ${x2.toFixed(2)},${y2.toFixed(2)} Z" fill="${sec.color ?? '#94a3b8'}" stroke="#fff" stroke-width="1.5"/>`;
    const midRad = (sec.startAngle + sec.angle / 2 - 90) * Math.PI / 180;
    const lx = cx + (r * 0.65) * Math.cos(midRad), ly = cy + (r * 0.65) * Math.sin(midRad);
    if (sec.percentage) {
      out += svgText(lx, ly, sec.percentage, { fontSize: 11, bold: true, fill: '#fff' });
    }
  });

  if (cfg.legend) {
    const legendY = cy + r + 18;
    let lx = 10;
    sections.forEach(sec => {
      const labelW = (sec.label?.length ?? 0) * 7 + 22;
      if (lx + labelW > w) return;
      out += `<rect x="${lx}" y="${legendY}" width="12" height="12" fill="${sec.color ?? '#94a3b8'}" rx="2"/>`;
      out += svgText(lx + 15, legendY + 6, sec.label ?? '', { fontSize: 10, fill: '#334155', textAnchor: 'start', dy: '0.35em' });
      lx += labelW;
    });
  }
  return svgWrap(w, h, out);
}

// ── Shared helper: draw angle arc + label inside an angle ────────────
/**
 * Draw an angle arc at vertex (vx,vy) between directions toward adj1 and adj2.
 * Places label along the bisector inside the angle.
 * Returns SVG string fragment.
 */
function drawAngleArcLabel(vx, vy, adj1, adj2, label, w, h) {
  let out = '';
  const d1x = adj1.x - vx, d1y = adj1.y - vy;
  const l1 = Math.sqrt(d1x*d1x + d1y*d1y) || 1;
  const u1x = d1x/l1, u1y = d1y/l1;
  const d2x = adj2.x - vx, d2y = adj2.y - vy;
  const l2 = Math.sqrt(d2x*d2x + d2y*d2y) || 1;
  const u2x = d2x/l2, u2y = d2y/l2;
  let bx = u1x + u2x, by = u1y + u2y;
  const bl = Math.sqrt(bx*bx + by*by) || 1;
  bx /= bl; by /= bl;
  const arcR = 18;
  const startA = Math.atan2(u1y, u1x);
  let endA = Math.atan2(u2y, u2x);
  let diff = endA - startA;
  while (diff > Math.PI) diff -= 2 * Math.PI;
  while (diff < -Math.PI) diff += 2 * Math.PI;
  endA = startA + diff;
  const arcX1 = (vx + arcR * Math.cos(startA)).toFixed(2);
  const arcY1 = (vy + arcR * Math.sin(startA)).toFixed(2);
  const arcX2 = (vx + arcR * Math.cos(endA)).toFixed(2);
  const arcY2 = (vy + arcR * Math.sin(endA)).toFixed(2);
  const sweep = diff > 0 ? 1 : 0;
  out += `<path d="M${arcX1},${arcY1} A${arcR},${arcR} 0 0,${sweep} ${arcX2},${arcY2}" fill="none" stroke="#334155" stroke-width="1.2"/>`;
  const loff = arcR + 13;
  const isGreek = /[θαβγδεφ]/.test(label);
  const lpos = clampLabel(vx + bx * loff, vy + by * loff, w, h);
  out += svgText(lpos.x, lpos.y, label, { italic: isGreek, fontSize: 13, textAnchor: 'middle', dominantBaseline: 'middle' });
  return out;
}

// ── Shape: parallelogram / trapezoid ────────────────────────────────
function drawParallelogram(cfg) {
  const V = cfg.vertices ?? {};
  const keys = Object.keys(V);
  if (keys.length < 4) return svgWrap(cfg.width ?? 280, cfg.height ?? 200, '');

  const w = cfg.width ?? 280, h = cfg.height ?? 200;
  const pts = keys.map(k => `${V[k].x},${V[k].y}`).join(' ');
  const shapeFill   = cfg.style?.fill        ?? '#dbeafe';
  const shapeStroke = cfg.style?.stroke      ?? '#1d4ed8';
  const shapeSW     = cfg.style?.strokeWidth ?? 2.2;

  // Centroid
  const cx = keys.reduce((s, k) => s + V[k].x, 0) / keys.length;
  const cy = keys.reduce((s, k) => s + V[k].y, 0) / keys.length;

  let out = '';
  out += `<polygon points="${pts}" fill="${shapeFill}" stroke="${shapeStroke}" stroke-width="${shapeSW}"/>`;

  // Side labels
  for (const s of (cfg.sides ?? [])) {
    const p1 = V[s.from], p2 = V[s.to];
    if (!p1 || !p2) continue;
    const mid = midpoint(p1, p2);
    const dx = p2.x - p1.x, dy = p2.y - p1.y;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    let nx = -dy / len, ny = dx / len;
    const toCx = mid.x - cx, toCy = mid.y - cy;
    if (nx * toCx + ny * toCy < 0) { nx = -nx; ny = -ny; }
    // Auto-offset: scale with text length so long labels clear the side
    const _fs = 13, _htw = (s.label.length * _fs * 0.55) / 2, _hth = _fs * 0.5;
    const _minX = Math.abs(nx) > 0.15 ? Math.min((_htw + 5) / Math.abs(nx), _htw + 8) : 0;
    const _minY = Math.abs(ny) > 0.15 ? Math.min((_hth + 4) / Math.abs(ny), _hth + 6) : 0;
    const offset = Math.max(14, _minX, _minY);
    const lpos = clampLabel(mid.x + nx * offset, mid.y + ny * offset, w, h);
    const isGreek = /[θαβγδεφ]/.test(s.label);
    out += svgText(lpos.x, lpos.y, s.label, { italic: isGreek, fontSize: 13 });
  }

  // Parallel pair tick arrows (chevrons)
  for (let gi = 0; gi < (cfg.parallelPairs ?? []).length; gi++) {
    const pair = cfg.parallelPairs[gi];
    const tickCount = gi + 1; // 1 chevron for first pair, 2 for second
    for (const sideName of pair) {
      // sideName like "AB" — look up from/to from vertices
      const fromKey = sideName[0], toKey = sideName[1];
      const p1 = V[fromKey], p2 = V[toKey];
      if (!p1 || !p2) continue;
      const mx = (p1.x + p2.x) / 2, my = (p1.y + p2.y) / 2;
      const dx = p2.x - p1.x, dy = p2.y - p1.y;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      const ux = dx / len, uy = dy / len;
      // Draw chevron(s) at midpoint in direction of side
      for (let ci = 0; ci < tickCount; ci++) {
        const offset = (ci - (tickCount - 1) / 2) * 8;
        const bx = mx + ux * offset, by = my + uy * offset;
        const sz = 5;
        // Chevron: two lines meeting at a point
        out += `<polyline points="${(bx - ux*sz - uy*sz/2).toFixed(2)},${(by - uy*sz + ux*sz/2).toFixed(2)} ${bx.toFixed(2)},${by.toFixed(2)} ${(bx - ux*sz + uy*sz/2).toFixed(2)},${(by - uy*sz - ux*sz/2).toFixed(2)}" fill="none" stroke="#334155" stroke-width="1.5" stroke-linejoin="round"/>`;
      }
    }
  }

  // Height line
  if (cfg.showHeight) {
    // Find the vertex with label key "D" or "C" (top-left), project to base
    const heightFromKey = keys.find(k => k === 'D') ?? keys.find(k => k === 'C') ?? keys[3];
    const heightFrom = V[heightFromKey];
    // Base: find the bottom edge (from A to B, or keys[0] to keys[1])
    const baseKey1 = keys[0], baseKey2 = keys[1];
    const bp1 = V[baseKey1], bp2 = V[baseKey2];
    const bdx = bp2.x - bp1.x, bdy = bp2.y - bp1.y;
    const bt = ((heightFrom.x - bp1.x) * bdx + (heightFrom.y - bp1.y) * bdy) / (bdx * bdx + bdy * bdy);
    const footX = bp1.x + bt * bdx, footY = bp1.y + bt * bdy;
    out += `<line x1="${heightFrom.x}" y1="${heightFrom.y}" x2="${footX.toFixed(2)}" y2="${footY.toFixed(2)}" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5,4"/>`;
    out += rightAngleSquare(footX, footY, heightFrom.x, heightFrom.y, bp2.x, bp2.y);
    if (cfg.heightLabel) {
      const hmx = (heightFrom.x + footX) / 2, hmy = (heightFrom.y + footY) / 2;
      const hperpX = -(footY - heightFrom.y) / (distance(heightFrom, { x: footX, y: footY }) || 1) * 10;
      const hperpY = (footX - heightFrom.x) / (distance(heightFrom, { x: footX, y: footY }) || 1) * 10;
      const hlpos = clampLabel(hmx + hperpX, hmy + hperpY, w, h);
      out += svgText(hlpos.x, hlpos.y, cfg.heightLabel, { italic: true, fontSize: 13 });
    }
  }

  // Angle arcs + labels
  for (const a of (cfg.angles ?? [])) {
    const vx = V[a.at]?.x, vy = V[a.at]?.y;
    if (vx == null) continue;
    // For a polygon, find the two adjacent vertices (previous and next in key order)
    const idx = keys.indexOf(a.at);
    const prevKey = keys[(idx - 1 + keys.length) % keys.length];
    const nextKey = keys[(idx + 1) % keys.length];
    const adj1 = V[prevKey], adj2 = V[nextKey];
    out += drawAngleArcLabel(vx, vy, adj1, adj2, a.label, w, h);
  }

  // Vertex labels outward from centroid
  for (const key of keys) {
    const vx = V[key].x, vy = V[key].y;
    const dx = vx - cx, dy = vy - cy;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const lpos = clampLabel(vx + (dx / len) * 16, vy + (dy / len) * 16, w, h);
    out += svgText(lpos.x, lpos.y, V[key].label ?? key, { bold: true, fontSize: 13 });
  }

  const ct = autoCenterTransform(keys.map(k => ({ x: V[k].x, y: V[k].y })), w, h);
  return svgWrap(w, h, ct.open + out + ct.close);
}

// ── Shape: two_triangles ─────────────────────────────────────────────
function drawTwoTriangles(cfg) {
  const w = cfg.width ?? 320, h = cfg.height ?? 200;
  let out = '';

  // Helper to draw a single triangle group
  function drawSingleTri(triCfg, allCongruentSides, allCongruentAngles, similarity) {
    const V = triCfg.vertices ?? {};
    const keys = Object.keys(V);
    if (keys.length < 3) return '';
    const pts = keys.map(k => `${V[k].x},${V[k].y}`).join(' ');
    const cx = keys.reduce((s, k) => s + V[k].x, 0) / keys.length;
    const cy = keys.reduce((s, k) => s + V[k].y, 0) / keys.length;
    const shapeFill   = triCfg.style?.fill        ?? cfg.style?.fill        ?? '#dbeafe';
    const shapeStroke = triCfg.style?.stroke      ?? cfg.style?.stroke      ?? '#1d4ed8';
    const shapeSW     = triCfg.style?.strokeWidth ?? cfg.style?.strokeWidth ?? 2.2;
    let s = '';
    s += `<polygon points="${pts}" fill="${shapeFill}" stroke="${shapeStroke}" stroke-width="${shapeSW}"/>`;

    // Congruent side tick marks
    // allCongruentSides is array of pairs like ["AB","DE"]; find which groups this triangle's sides belong to
    const tickCountMap = {};
    for (let gi = 0; gi < (allCongruentSides ?? []).length; gi++) {
      const [s1, s2] = allCongruentSides[gi];
      const count = gi + 1;
      [s1, s2].forEach(sideName => {
        // Check if both vertices of this side are in this triangle
        const from = sideName[0], to = sideName[1];
        if (V[from] && V[to]) {
          tickCountMap[sideName] = count;
          tickCountMap[to + from] = count; // reverse
        }
      });
    }
    // Draw ticks on sides
    for (const key of keys) {
      for (const key2 of keys) {
        if (key >= key2) continue;
        const sideName = key + key2;
        const count = tickCountMap[sideName] ?? tickCountMap[key2 + key];
        if (count !== undefined) {
          out += tickMark(V[key].x, V[key].y, V[key2].x, V[key2].y, count);
        }
      }
    }

    // Congruent angle arcs — find matching angles for this triangle's vertices
    for (let gi = 0; gi < (allCongruentAngles ?? []).length; gi++) {
      const [ang1Key, ang2Key] = allCongruentAngles[gi];
      const matchKey = keys.find(k => k === ang1Key || k === ang2Key);
      if (!matchKey) continue;
      const vx = V[matchKey].x, vy = V[matchKey].y;
      const adjKeys = keys.filter(k => k !== matchKey);
      if (adjKeys.length < 2) continue;
      const adj1 = V[adjKeys[0]], adj2 = V[adjKeys[1]];
      // Draw gi+1 arcs (stacked) to indicate the congruency group
      const arcCount = gi + 1;
      for (let ai = 0; ai < arcCount; ai++) {
        const arcR = 14 + ai * 6;
        const d1x = adj1.x - vx, d1y = adj1.y - vy;
        const l1 = Math.sqrt(d1x*d1x + d1y*d1y) || 1;
        const u1x = d1x/l1, u1y = d1y/l1;
        const d2x = adj2.x - vx, d2y = adj2.y - vy;
        const l2 = Math.sqrt(d2x*d2x + d2y*d2y) || 1;
        const u2x = d2x/l2, u2y = d2y/l2;
        const startA = Math.atan2(u1y, u1x);
        let endA = Math.atan2(u2y, u2x);
        let diff = endA - startA;
        while (diff > Math.PI) diff -= 2 * Math.PI;
        while (diff < -Math.PI) diff += 2 * Math.PI;
        endA = startA + diff;
        const arcX1 = (vx + arcR * Math.cos(startA)).toFixed(2);
        const arcY1 = (vy + arcR * Math.sin(startA)).toFixed(2);
        const arcX2 = (vx + arcR * Math.cos(endA)).toFixed(2);
        const arcY2 = (vy + arcR * Math.sin(endA)).toFixed(2);
        const sweep = diff > 0 ? 1 : 0;
        s += `<path d="M${arcX1},${arcY1} A${arcR},${arcR} 0 0,${sweep} ${arcX2},${arcY2}" fill="none" stroke="#334155" stroke-width="1.2"/>`;
      }
    }

    // Vertex labels
    for (const key of keys) {
      const vx = V[key].x, vy = V[key].y;
      const dx = vx - cx, dy = vy - cy;
      const len = Math.sqrt(dx * dx + dy * dy) || 1;
      const lpos = clampLabel(vx + (dx / len) * 16, vy + (dy / len) * 16, w, h);
      s += svgText(lpos.x, lpos.y, V[key].label ?? key, { bold: true, fontSize: 13 });
    }

    // Triangle label (e.g. "△ABC")
    if (triCfg.label) {
      s += svgText(cx, cy - 8, triCfg.label, { fontSize: 10, fill: '#64748b' });
    }

    return s;
  }

  out += drawSingleTri(cfg.triangle1 ?? {}, cfg.congruentSides, cfg.congruentAngles, cfg.similarity);
  out += drawSingleTri(cfg.triangle2 ?? {}, cfg.congruentSides, cfg.congruentAngles, cfg.similarity);

  // Similarity indicator between triangles
  if (cfg.similarity) {
    const V1 = cfg.triangle1?.vertices ?? {}, V2 = cfg.triangle2?.vertices ?? {};
    const k1 = Object.keys(V1), k2 = Object.keys(V2);
    if (k1.length >= 3 && k2.length >= 3) {
      const cx1 = k1.reduce((s, k) => s + V1[k].x, 0) / k1.length;
      const cy1 = k1.reduce((s, k) => s + V1[k].y, 0) / k1.length;
      const cx2 = k2.reduce((s, k) => s + V2[k].x, 0) / k2.length;
      const cy2 = k2.reduce((s, k) => s + V2[k].y, 0) / k2.length;
      const mx = (cx1 + cx2) / 2, my = (cy1 + cy2) / 2;
      // "~" symbol centred between the two triangles
      out += svgText(mx, my, '∼', { fontSize: 17, bold: true, fill: '#2563eb' });
      // Scale factor or similarity type below the symbol
      if (typeof cfg.similarity === 'string' && cfg.similarity.length > 1) {
        out += svgText(mx, my + 16, cfg.similarity, { fontSize: 10, fill: '#64748b' });
      }
    }
  }

  // Scale-factor tick marks on corresponding sides
  if (cfg.scaleFactor && cfg.scaleFactor !== 1) {
    const sfLabel = typeof cfg.scaleFactor === 'string' ? cfg.scaleFactor : `×${cfg.scaleFactor}`;
    // Place label between the two triangle centroids, slightly above the ~ symbol
    const V1 = cfg.triangle1?.vertices ?? {}, V2 = cfg.triangle2?.vertices ?? {};
    const k1 = Object.keys(V1), k2 = Object.keys(V2);
    if (k1.length >= 3 && k2.length >= 3) {
      const cx1 = k1.reduce((s, k) => s + V1[k].x, 0) / k1.length;
      const cy1 = k1.reduce((s, k) => s + V1[k].y, 0) / k1.length;
      const cx2 = k2.reduce((s, k) => s + V2[k].x, 0) / k2.length;
      const cy2 = k2.reduce((s, k) => s + V2[k].y, 0) / k2.length;
      const mx = (cx1 + cx2) / 2, my = (cy1 + cy2) / 2;
      out += svgText(mx, my - 16, sfLabel, { fontSize: 11, fill: '#16a34a', bold: true });
    }
  }

  // Collect all vertices from both triangles for centering
  const allPts = [];
  for (const tri of [cfg.triangle1, cfg.triangle2].filter(Boolean)) {
    const V = tri.vertices ?? {};
    Object.values(V).forEach(v => allPts.push({ x: v.x, y: v.y }));
  }
  const ct = autoCenterTransform(allPts, w, h);
  return svgWrap(w, h, ct.open + out + ct.close);
}

// ── Shape: normal_curve ──────────────────────────────────────────────
/**
 * Normal distribution bell curve for SAT statistics questions.
 * cfg.mean        default 0
 * cfg.stdDev      default 1
 * cfg.xMin/xMax   default mean ± 4σ
 * cfg.shadedRegions  [{from, to, fillColor, label}]  — vertical slice shading
 * cfg.markers        [{x, label, color}]             — vertical tick + label
 * cfg.title?
 */
function drawNormalCurve(cfg) {
  const W = cfg.width ?? 300, H = cfg.height ?? 200;
  const mu  = cfg.mean   ?? 0;
  const sig = cfg.stdDev ?? 1;
  const xMin = cfg.xMin ?? mu - 4 * sig;
  const xMax = cfg.xMax ?? mu + 4 * sig;
  const padL = 28, padR = 16, padT = cfg.title ? 28 : 18, padB = 36;
  const plotW = W - padL - padR, plotH = H - padT - padB;

  // Normal PDF
  const pdf = x => Math.exp(-0.5 * ((x - mu) / sig) ** 2) / (sig * Math.sqrt(2 * Math.PI));
  const yPeak = pdf(mu);

  const toSVGX = x  => padL + ((x - xMin) / (xMax - xMin)) * plotW;
  const toSVGY = y  => padT + plotH - (y / yPeak) * plotH * 0.85;

  let out = '';

  // Title
  if (cfg.title) {
    out += svgText(W / 2, 14, cfg.title, { fontSize: 11, bold: true, fill: '#1e293b' });
  }

  const steps = 300;
  const dx = (xMax - xMin) / steps;

  // Shaded regions (draw before the curve)
  for (const region of (cfg.shadedRegions ?? [])) {
    const rFrom = region.from ?? xMin, rTo = region.to ?? xMax;
    const pts = [];
    // Baseline start
    pts.push(`${toSVGX(rFrom).toFixed(2)},${(padT + plotH).toFixed(2)}`);
    // Trace curve
    for (let i = 0; i <= steps; i++) {
      const x = xMin + i * dx;
      if (x < rFrom || x > rTo) continue;
      pts.push(`${toSVGX(x).toFixed(2)},${toSVGY(pdf(x)).toFixed(2)}`);
    }
    // Baseline end
    pts.push(`${toSVGX(rTo).toFixed(2)},${(padT + plotH).toFixed(2)}`);
    out += `<polygon points="${pts.join(' ')}" fill="${region.fillColor ?? '#dbeafe'}" fill-opacity="0.7" stroke="none"/>`;
    // Region label (centred, above baseline)
    if (region.label) {
      const midX = (rFrom + rTo) / 2;
      const midY = pdf(midX);
      out += svgText(toSVGX(midX), toSVGY(midY / 2), region.label,
        { fontSize: 10, bold: true, fill: '#1e40af' });
    }
  }

  // Bell curve polyline
  const curvePts = [];
  for (let i = 0; i <= steps; i++) {
    const x = xMin + i * dx;
    curvePts.push(`${toSVGX(x).toFixed(2)},${toSVGY(pdf(x)).toFixed(2)}`);
  }
  out += `<polyline points="${curvePts.join(' ')}" fill="none" stroke="#334155" stroke-width="2"/>`;

  // Baseline (x-axis)
  out += `<line x1="${padL}" y1="${(padT + plotH).toFixed(2)}" x2="${(W - padR).toFixed(2)}" y2="${(padT + plotH).toFixed(2)}" stroke="#334155" stroke-width="1.2"/>`;

  // Vertical markers (mean, ±σ, etc.)
  for (const mk of (cfg.markers ?? [])) {
    const sx = toSVGX(mk.x);
    const topY = toSVGY(pdf(mk.x));
    const botY = padT + plotH;
    const mc = mk.color ?? '#334155';
    const dash = mk.dashed ? 'stroke-dasharray="4,3"' : '';
    out += `<line x1="${sx.toFixed(2)}" y1="${topY.toFixed(2)}" x2="${sx.toFixed(2)}" y2="${botY}" stroke="${mc}" stroke-width="1.2" ${dash}/>`;
    if (mk.label) {
      out += svgText(sx, botY + 13, mk.label, { fontSize: 10, fill: mc, italic: true });
    }
  }

  return svgWrap(W, H, out);
}

// ── Shape: regular_polygon ───────────────────────────────────────────
/**
 * Regular n-sided polygon for SAT geometry questions.
 * cfg.sides         number of sides (3–12)
 * cfg.sideLabel?    label on every side (e.g. "s")
 * cfg.vertexLabels? array of vertex label strings
 * cfg.showDiagonals? draw all diagonals (default false)
 * cfg.shading?      fill color (default light blue)
 * cfg.label?        name shown in center (e.g. "Hexagon")
 * cfg.rotationDeg?  rotation of first vertex from top (default 90 = vertex at top)
 */
function drawRegularPolygon(cfg) {
  const W = cfg.width ?? 260, H = cfg.height ?? 260;
  const n     = Math.max(3, Math.min(12, cfg.sides ?? 6));
  const cx    = W / 2, cy = H / 2;
  const r     = Math.min(W, H) / 2 - 30;
  const rotRad = ((cfg.rotationDeg ?? 90) - 90) * Math.PI / 180;

  const verts = Array.from({length: n}, (_, i) => {
    const a = rotRad + (2 * Math.PI * i) / n;
    return { x: cx + r * Math.cos(a), y: cy + r * Math.sin(a), a };
  });

  const pts = verts.map(v => `${v.x.toFixed(2)},${v.y.toFixed(2)}`).join(' ');
  let out = '';

  // Fill
  const fill = cfg.shading ?? '#dbeafe';
  out += `<polygon points="${pts}" fill="${fill}" fill-opacity="0.5" stroke="#334155" stroke-width="2"/>`;

  // Diagonals
  if (cfg.showDiagonals) {
    for (let i = 0; i < n; i++) {
      for (let j = i + 2; j < n; j++) {
        if (i === 0 && j === n - 1) continue; // skip side
        out += `<line x1="${verts[i].x.toFixed(2)}" y1="${verts[i].y.toFixed(2)}" x2="${verts[j].x.toFixed(2)}" y2="${verts[j].y.toFixed(2)}" stroke="#94a3b8" stroke-width="0.8" stroke-dasharray="3,2"/>`;
      }
    }
  }

  // Side labels
  if (cfg.sideLabel) {
    verts.forEach((v, i) => {
      const next = verts[(i + 1) % n];
      const mx = (v.x + next.x) / 2, my = (v.y + next.y) / 2;
      const dx = cx - mx, dy = cy - my;
      const dl = Math.sqrt(dx*dx + dy*dy) || 1;
      const lpos = clampLabel(mx + (dx/dl)*13, my + (dy/dl)*13, W, H);
      out += svgText(lpos.x, lpos.y, cfg.sideLabel, { italic: true, fontSize: 12, fill: '#334155' });
    });
  }

  // Vertex labels
  const vlabels = cfg.vertexLabels ?? [];
  verts.forEach((v, i) => {
    const lbl = vlabels[i];
    if (!lbl) return;
    const lpos = clampLabel(cx + (r + 16) * Math.cos(v.a), cy + (r + 16) * Math.sin(v.a), W, H);
    out += svgText(lpos.x, lpos.y, lbl, { bold: true, fontSize: 13 });
  });

  // Center label
  if (cfg.label) {
    out += svgText(cx, cy, cfg.label, { fontSize: 11, fill: '#475569', bold: true });
  }

  return svgWrap(W, H, out);
}

// ── Shape: venn_diagram ──────────────────────────────────────────────
/**
 * Two-circle Venn diagram for SAT probability / set-theory questions.
 * cfg.sets       = [{label, color?, value?}, {label, color?, value?}]
 * cfg.intersection = {label?, value?}
 * cfg.title?     — shown at top
 * cfg.universal? — {label, value?} rectangle enclosing everything
 */
function drawVennDiagram(cfg) {
  const W = cfg.width ?? 300, H = cfg.height ?? 220;
  const sets = cfg.sets ?? [{}, {}];
  const S1 = sets[0] ?? {}, S2 = sets[1] ?? {};
  const inter = cfg.intersection ?? {};

  // Circle geometry — 40% overlap
  const cy  = H / 2 + (cfg.title ? 12 : 0);
  const r   = Math.min(W * 0.30, H * 0.38);
  const sep = r * 1.18;   // distance between centres (gives ~40% overlap)
  const cx1 = W / 2 - sep / 2;
  const cx2 = W / 2 + sep / 2;

  let out = '';

  // Optional universal set rectangle
  if (cfg.universal) {
    const pad = 8;
    out += `<rect x="${pad}" y="${(cfg.title ? 22 : pad)}" width="${W - pad*2}" height="${H - (cfg.title ? 28 : pad*2)}" fill="none" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="5,3" rx="4"/>`;
    if (cfg.universal.label) {
      out += svgText(W - pad - 4, cfg.title ? 32 : pad + 12, cfg.universal.label, { fontSize: 10, fill: '#64748b', textAnchor: 'end' });
    }
  }

  // Title
  if (cfg.title) {
    out += svgText(W / 2, 14, cfg.title, { fontSize: 11, bold: true, fill: '#1e293b' });
  }

  // Clip paths so fill stays inside each circle
  const uid = Math.floor(Math.random() * 99999);
  out += `<defs>
    <clipPath id="cp1-${uid}"><circle cx="${cx1.toFixed(2)}" cy="${cy.toFixed(2)}" r="${r.toFixed(2)}"/></clipPath>
    <clipPath id="cp2-${uid}"><circle cx="${cx2.toFixed(2)}" cy="${cy.toFixed(2)}" r="${r.toFixed(2)}"/></clipPath>
  </defs>`;

  // Left circle fill (A only region)
  const c1 = S1.color ?? '#bfdbfe';
  out += `<circle cx="${cx1.toFixed(2)}" cy="${cy.toFixed(2)}" r="${r.toFixed(2)}" fill="${c1}" fill-opacity="0.55" stroke="#2563eb" stroke-width="1.8"/>`;

  // Right circle fill (B only region)
  const c2 = S2.color ?? '#bbf7d0';
  out += `<circle cx="${cx2.toFixed(2)}" cy="${cy.toFixed(2)}" r="${r.toFixed(2)}" fill="${c2}" fill-opacity="0.55" stroke="#16a34a" stroke-width="1.8"/>`;

  // Intersection overlay — brighter tint where both overlap
  const interColor = inter.color ?? '#a5f3fc';
  // Draw right-circle clipped to left-circle to fill overlap region
  out += `<circle cx="${cx2.toFixed(2)}" cy="${cy.toFixed(2)}" r="${r.toFixed(2)}" fill="${interColor}" fill-opacity="0.55" stroke="none" clip-path="url(#cp1-${uid})"/>`;

  // Labels for each region
  const leftX  = cx1 - r * 0.42;   // A-only
  const rightX = cx2 + r * 0.42;   // B-only
  const midX   = W / 2;            // intersection

  // Set A label (above circle, left)
  if (S1.label) {
    out += svgText(cx1, cy - r - 8, S1.label, { fontSize: 12, bold: true, fill: '#1e3a8a' });
  }
  // Set B label (above circle, right)
  if (S2.label) {
    out += svgText(cx2, cy - r - 8, S2.label, { fontSize: 12, bold: true, fill: '#14532d' });
  }

  // Region values
  if (S1.value != null) {
    out += svgText(leftX, cy + 4, String(S1.value), { fontSize: 13, bold: true, fill: '#1e3a8a' });
  }
  if (inter.value != null) {
    out += svgText(midX, cy + 4, String(inter.value), { fontSize: 13, bold: true, fill: '#0f766e' });
  }
  if (S2.value != null) {
    out += svgText(rightX, cy + 4, String(S2.value), { fontSize: 13, bold: true, fill: '#14532d' });
  }

  // Region text labels (e.g. "A only", "A∩B")
  if (S1.regionLabel) {
    out += svgText(leftX, cy + (S1.value != null ? 16 : 4), S1.regionLabel, { fontSize: 10, fill: '#475569' });
  }
  if (inter.label) {
    out += svgText(midX, cy + (inter.value != null ? 16 : 4), inter.label, { fontSize: 10, fill: '#475569' });
  }
  if (S2.regionLabel) {
    out += svgText(rightX, cy + (S2.value != null ? 16 : 4), S2.regionLabel, { fontSize: 10, fill: '#475569' });
  }

  // Universal set total (bottom right)
  if (cfg.universal?.value != null) {
    out += svgText(W - 14, H - 8, `Total: ${cfg.universal.value}`, { fontSize: 10, fill: '#64748b', textAnchor: 'end' });
  }

  return svgWrap(W, H, out);
}

// ── Shape: 3d_shape ──────────────────────────────────────────────────
function drawShape3D(cfg) {
  const w = cfg.width ?? 280, h = cfg.height ?? 220;
  const type = cfg.type ?? 'rectangular_prism';
  const labels = cfg.labels ?? {};
  let out = '';

  if (type === 'rectangular_prism' || type === 'cube') {
    // Isometric-style box
    // Front face bottom-left corner
    const flx = 50, fly = 150;
    const fw = 140, fh = 90;
    // Depth offset (upper-right direction)
    const ddx = 40, ddy = -30;

    // 8 corners:
    // Front face: fl(flx,fly), fr(flx+fw,fly), ftr(flx+fw,fly-fh), ftl(flx,fly-fh)
    const fl  = [flx,       fly     ];
    const fr  = [flx+fw,    fly     ];
    const ftr = [flx+fw,    fly-fh  ];
    const ftl = [flx,       fly-fh  ];
    // Back face (depth offset)
    const bl  = [flx+ddx,   fly+ddy     ];
    const br  = [flx+fw+ddx,fly+ddy     ];
    const btr = [flx+fw+ddx,fly-fh+ddy  ];
    const btl = [flx+ddx,   fly-fh+ddy  ];

    function pt(p) { return `${p[0].toFixed(1)},${p[1].toFixed(1)}`; }
    function line(p1, p2, dash) {
      const d = dash ? 'stroke-dasharray="4,3"' : '';
      return `<line x1="${p1[0].toFixed(1)}" y1="${p1[1].toFixed(1)}" x2="${p2[0].toFixed(1)}" y2="${p2[1].toFixed(1)}" stroke="#334155" stroke-width="1.5" ${d}/>`;
    }

    // Faces (filled)
    // Front face
    out += `<polygon points="${pt(fl)} ${pt(fr)} ${pt(ftr)} ${pt(ftl)}" fill="#f1f5f9" stroke="none"/>`;
    // Right face
    out += `<polygon points="${pt(fr)} ${pt(br)} ${pt(btr)} ${pt(ftr)}" fill="#e2e8f0" stroke="none"/>`;
    // Top face
    out += `<polygon points="${pt(ftl)} ${pt(ftr)} ${pt(btr)} ${pt(btl)}" fill="#f8fafc" stroke="none"/>`;

    // Solid visible edges
    // Front face edges
    out += line(fl, fr);
    out += line(fr, ftr);
    out += line(ftr, ftl);
    out += line(ftl, fl);
    // Right face edges (fr-br, btr-ftr already drawn)
    out += line(fr, br);
    out += line(br, btr);
    out += line(btr, ftr);
    // Top face edges (ftl-ftr drawn, ftr-btr drawn)
    out += line(ftl, btl);
    out += line(btl, btr);

    // Dashed hidden edges
    out += line(fl,  bl,  true);
    out += line(bl,  br,  true);
    out += line(bl,  btl, true);

    // Dimension labels
    const lw = labels.length ?? 'l';
    const lwd = labels.width ?? 'w';
    const lh = labels.height ?? 'h';

    // Length label (along bottom front edge)
    const lmx = (fl[0] + fr[0]) / 2, lmy = fl[1] + 16;
    out += svgText(lmx, lmy, lw, { italic: true, fontSize: 13 });

    // Height label (along left front edge)
    const hmx = fl[0] - 14, hmy = (fl[1] + ftl[1]) / 2;
    out += svgText(hmx, hmy, lh, { italic: true, fontSize: 13 });

    // Width label (along right-going depth edge)
    const wmx = (fr[0] + br[0]) / 2 + 10, wmy = (fr[1] + br[1]) / 2 + 10;
    out += svgText(wmx, wmy, lwd, { italic: true, fontSize: 13 });

  } else if (type === 'cylinder') {
    const bcx = w / 2, bcy = h - 40, cr = 70, ch = 120;
    const ry = 18; // ellipse y-radius for top/bottom
    // Cylinder body sides
    out += `<line x1="${bcx - cr}" y1="${bcy}" x2="${bcx - cr}" y2="${bcy - ch}" stroke="#334155" stroke-width="1.5"/>`;
    out += `<line x1="${bcx + cr}" y1="${bcy}" x2="${bcx + cr}" y2="${bcy - ch}" stroke="#334155" stroke-width="1.5"/>`;
    // Bottom ellipse (dashed bottom half, solid front)
    out += `<ellipse cx="${bcx}" cy="${bcy}" rx="${cr}" ry="${ry}" fill="#f1f5f9" stroke="#334155" stroke-width="1.5" stroke-dasharray="5,4"/>`;
    // Top ellipse (solid)
    out += `<ellipse cx="${bcx}" cy="${bcy - ch}" rx="${cr}" ry="${ry}" fill="#f8fafc" stroke="#334155" stroke-width="1.5"/>`;
    // Labels
    const lh = labels.height ?? 'h';
    const lr = labels.radius ?? labels.width ?? 'r';
    out += svgText(bcx + cr + 14, bcy - ch / 2, lh, { italic: true, fontSize: 13 });
    out += svgText(bcx + cr / 2, bcy - ch - ry - 8, lr, { italic: true, fontSize: 13 });

  } else if (type === 'cone') {
    const bcx = w / 2, bcy = h - 40, cr = 70, apex = 30, ry = 18;
    const apexX = bcx, apexY = apex;
    out += `<ellipse cx="${bcx}" cy="${bcy}" rx="${cr}" ry="${ry}" fill="#f1f5f9" stroke="#334155" stroke-width="1.5" stroke-dasharray="5,4"/>`;
    out += `<line x1="${bcx - cr}" y1="${bcy}" x2="${apexX}" y2="${apexY}" stroke="#334155" stroke-width="1.5"/>`;
    out += `<line x1="${bcx + cr}" y1="${bcy}" x2="${apexX}" y2="${apexY}" stroke="#334155" stroke-width="1.5"/>`;
    const lh = labels.height ?? 'h';
    const lr = labels.radius ?? labels.width ?? 'r';
    out += svgText(apexX - 16, (apexY + bcy) / 2, lh, { italic: true, fontSize: 13 });
    out += svgText((bcx + bcx + cr) / 2, bcy + ry + 14, lr, { italic: true, fontSize: 13 });

  } else if (type === 'pyramid') {
    // Square base pyramid — isometric view
    const bx1 = 50, by1 = h - 40;
    const bw2 = 100; // half base width
    // Base corners (parallelogram projection)
    const b1 = [bx1,           by1        ];
    const b2 = [bx1 + bw2*2,   by1        ];
    const b3 = [bx1 + bw2*2 + 30, by1 - 22];
    const b4 = [bx1 + 30,      by1 - 22   ];
    const apex = [bx1 + bw2 + 15, by1 - 130];
    function pt(p) { return `${p[0].toFixed(1)},${p[1].toFixed(1)}`; }
    function pline(p1, p2, dash) {
      const d = dash ? 'stroke-dasharray="4,3"' : '';
      return `<line x1="${p1[0].toFixed(1)}" y1="${p1[1].toFixed(1)}" x2="${p2[0].toFixed(1)}" y2="${p2[1].toFixed(1)}" stroke="#334155" stroke-width="1.5" ${d}/>`;
    }
    out += `<polygon points="${pt(b1)} ${pt(b2)} ${pt(b3)} ${pt(b4)}" fill="#f1f5f9" stroke="#334155" stroke-width="1.5"/>`;
    out += pline(b1, apex);
    out += pline(b2, apex);
    out += pline(b3, apex);
    out += pline(b4, apex);
    // Dashed diagonals of base
    out += pline(b1, b3, true);
    out += pline(b2, b4, true);
    // Labels
    const lb = labels.base ?? labels.length ?? 'b';
    const lh = labels.height ?? 'h';
    out += svgText((b1[0] + b2[0]) / 2, b1[1] + 16, lb, { italic: true, fontSize: 13 });
    out += svgText(apex[0] - 14, (apex[1] + b1[1]) / 2, lh, { italic: true, fontSize: 13 });

  } else if (type === 'sphere') {
    const scx = w / 2, scy = h / 2, sr = Math.min(w, h) / 2 - 24;
    // Outer circle
    out += `<circle cx="${scx}" cy="${scy}" r="${sr}" fill="#f1f5f9" stroke="#334155" stroke-width="1.5"/>`;
    // Equator ellipse
    out += `<ellipse cx="${scx}" cy="${scy}" rx="${sr}" ry="${Math.round(sr*0.22)}" fill="none" stroke="#334155" stroke-width="1" stroke-dasharray="5,4"/>`;
    // Vertical meridian ellipse (visible half solid, back half dashed)
    const mry = sr, mrx = Math.round(sr * 0.22);
    out += `<ellipse cx="${scx}" cy="${scy}" rx="${mrx}" ry="${mry}" fill="none" stroke="#334155" stroke-width="1" stroke-dasharray="5,4"/>`;
    // Radius line + label
    const lbl_r = labels.radius ?? 'r';
    out += `<line x1="${scx}" y1="${scy}" x2="${(scx + sr).toFixed(1)}" y2="${scy}" stroke="#334155" stroke-width="1.3"/>`;
    out += `<circle cx="${scx}" cy="${scy}" r="2.5" fill="#334155"/>`;
    out += svgText(scx + sr / 2, scy - 10, lbl_r, { italic: true, fontSize: 13 });

  } else if (type === 'triangular_prism') {
    // Two equilateral-ish triangular faces + three rectangular side faces (isometric)
    const bx = 70, by = h - 40, bw = 140, bh = 100, ddx = 44, ddy = -28;
    // Front triangle vertices
    const ft = [bx + bw / 2, by - bh];  // top
    const fl2 = [bx,          by      ]; // bottom-left
    const fr2 = [bx + bw,     by      ]; // bottom-right
    // Back triangle (offset by depth)
    const bt2 = [ft[0]+ddx,  ft[1]+ddy];
    const bl2 = [fl2[0]+ddx, fl2[1]+ddy];
    const br2 = [fr2[0]+ddx, fr2[1]+ddy];
    function p2(p) { return `${p[0].toFixed(1)},${p[1].toFixed(1)}`; }
    function ln2(a, b, dash) {
      const d = dash ? 'stroke-dasharray="4,3"' : '';
      return `<line x1="${a[0].toFixed(1)}" y1="${a[1].toFixed(1)}" x2="${b[0].toFixed(1)}" y2="${b[1].toFixed(1)}" stroke="#334155" stroke-width="1.5" ${d}/>`;
    }
    // Faces
    out += `<polygon points="${p2(fl2)} ${p2(fr2)} ${p2(ft)}" fill="#f1f5f9" stroke="none"/>`;
    out += `<polygon points="${p2(fr2)} ${p2(br2)} ${p2(bt2)} ${p2(ft)}" fill="#e2e8f0" stroke="none"/>`;
    out += `<polygon points="${p2(ft)} ${p2(bt2)} ${p2(bl2)} ${p2(fl2)}" fill="#f8fafc" stroke="none"/>`;
    // Visible edges
    out += ln2(fl2, fr2); out += ln2(fr2, ft); out += ln2(ft, fl2);
    out += ln2(fr2, br2); out += ln2(br2, bt2); out += ln2(bt2, ft);
    out += ln2(ft, bt2); // top ridge
    // Dashed hidden edges
    out += ln2(fl2, bl2, true); out += ln2(bl2, br2, true); out += ln2(bl2, bt2, true);
    // Labels
    const llbl = labels.length ?? labels.depth ?? 'l';
    const blbl = labels.base  ?? 'b';
    const hlbl = labels.height ?? 'h';
    out += svgText((fl2[0]+fr2[0])/2, fl2[1]+16, blbl, { italic:true, fontSize:13 });
    out += svgText(ft[0]-14, (ft[1]+fl2[1])/2, hlbl, { italic:true, fontSize:13 });
    out += svgText((fr2[0]+br2[0])/2+10, (fr2[1]+br2[1])/2+10, llbl, { italic:true, fontSize:13 });

  } else if (type === 'frustum') {
    // Truncated cone: top ellipse smaller than bottom
    const fcx = w / 2, fbcy = h - 40, fry = 16, fcr = 72, fch = 110, ftcr = 38, ftcy = fbcy - fch;
    // Bottom ellipse
    out += `<ellipse cx="${fcx}" cy="${fbcy}" rx="${fcr}" ry="${fry}" fill="#f1f5f9" stroke="#334155" stroke-width="1.5" stroke-dasharray="5,4"/>`;
    // Top ellipse
    out += `<ellipse cx="${fcx}" cy="${ftcy}" rx="${ftcr}" ry="${Math.round(fry*ftcr/fcr)}" fill="#f8fafc" stroke="#334155" stroke-width="1.5"/>`;
    // Side lines
    out += `<line x1="${(fcx-fcr).toFixed(1)}" y1="${fbcy}" x2="${(fcx-ftcr).toFixed(1)}" y2="${ftcy}" stroke="#334155" stroke-width="1.5"/>`;
    out += `<line x1="${(fcx+fcr).toFixed(1)}" y1="${fbcy}" x2="${(fcx+ftcr).toFixed(1)}" y2="${ftcy}" stroke="#334155" stroke-width="1.5"/>`;
    // Labels
    const fr_lbl = labels.radius ?? labels.bottomRadius ?? 'R';
    const fr2_lbl = labels.topRadius ?? 'r';
    const fh_lbl  = labels.height ?? 'h';
    out += svgText(fcx+fcr/2+6, fbcy+fry+14, fr_lbl, { italic:true, fontSize:13 });
    out += svgText(fcx+ftcr/2+4, ftcy-Math.round(fry*ftcr/fcr)-8, fr2_lbl, { italic:true, fontSize:13 });
    out += svgText(fcx+fcr+14, (fbcy+ftcy)/2, fh_lbl, { italic:true, fontSize:13 });
  }

  return svgWrap(w, h, out);
}

// ── Shape: angle_figure ──────────────────────────────────────────────
/**
 * Draws one or more angle figures: two rays meeting at a vertex, with arc
 * markers, angle labels, and optional right-angle squares.
 * Each entry in cfg.angles: { vx, vy, ray1Angle, ray2Angle, rayLength, label,
 *   point1Label, point2Label, vertexLabel, rightAngle, arcCount }
 * Also supports adjacent supplementary/vertical angles via cfg.extraRays.
 */
function drawAngleFigure(cfg) {
  const w = cfg.width ?? 220, h = cfg.height ?? 180;
  let out = '';

  for (const ang of (cfg.angles ?? [])) {
    const vx  = ang.vx  ?? w / 2;
    const vy  = ang.vy  ?? h * 0.65;
    const r1a = (ang.ray1Angle ?? 180) * Math.PI / 180;
    const r2a = (ang.ray2Angle ?? 0)   * Math.PI / 180;
    const len = ang.rayLength ?? 75;
    const r1x = vx + len * Math.cos(r1a), r1y = vy + len * Math.sin(r1a);
    const r2x = vx + len * Math.cos(r2a), r2y = vy + len * Math.sin(r2a);

    out += `<line x1="${vx.toFixed(2)}" y1="${vy.toFixed(2)}" x2="${r1x.toFixed(2)}" y2="${r1y.toFixed(2)}" stroke="#334155" stroke-width="1.8"/>`;
    out += `<line x1="${vx.toFixed(2)}" y1="${vy.toFixed(2)}" x2="${r2x.toFixed(2)}" y2="${r2y.toFixed(2)}" stroke="#334155" stroke-width="1.8"/>`;

    if (ang.rightAngle) {
      out += rightAngleSquare(vx, vy, r1x, r1y, r2x, r2y);
    } else if (ang.label) {
      const arcCount = ang.arcCount ?? 1;
      const adj1 = { x: r1x, y: r1y }, adj2 = { x: r2x, y: r2y };
      const d1x = adj1.x - vx, d1y = adj1.y - vy, l1 = Math.sqrt(d1x*d1x+d1y*d1y)||1;
      const d2x = adj2.x - vx, d2y = adj2.y - vy, l2 = Math.sqrt(d2x*d2x+d2y*d2y)||1;
      const u1x = d1x/l1, u1y = d1y/l1, u2x = d2x/l2, u2y = d2y/l2;
      const saDeg = Math.atan2(u1y, u1x) * 180 / Math.PI;
      let eaDeg   = Math.atan2(u2y, u2x) * 180 / Math.PI;
      let diff = eaDeg - saDeg;
      while (diff >  180) diff -= 360;
      while (diff < -180) diff += 360;
      eaDeg = saDeg + diff;
      for (let ai = 0; ai < arcCount; ai++) {
        out += Prim.arc(vx, vy, 18 + ai * 6, saDeg, eaDeg);
      }
      // Label along bisector
      let bx = u1x + u2x, by = u1y + u2y;
      const bl = Math.sqrt(bx*bx+by*by)||1; bx /= bl; by /= bl;
      const loff = (arcCount > 1 ? 24 + (arcCount-1)*6 : 18) + 12;
      const isGreek = /[θαβγδεφ°]/.test(ang.label);
      const lpos = clampLabel(vx + bx*loff, vy + by*loff, w, h);
      out += svgText(lpos.x, lpos.y, ang.label, { italic: isGreek, fontSize: 13 });
    }

    // End-point labels
    if (ang.point1Label) {
      const lpos = clampLabel(r1x + (r1x > vx ? 10 : -10), r1y + (r1y < vy ? -8 : 8), w, h);
      out += svgText(lpos.x, lpos.y, ang.point1Label, { bold: true, fontSize: 13 });
    }
    if (ang.point2Label) {
      const lpos = clampLabel(r2x + (r2x > vx ? 10 : -10), r2y + (r2y < vy ? -8 : 8), w, h);
      out += svgText(lpos.x, lpos.y, ang.point2Label, { bold: true, fontSize: 13 });
    }
    if (ang.vertexLabel) {
      out += svgText(vx, vy + 14, ang.vertexLabel, { bold: true, fontSize: 13 });
    }
  }

  // Extra rays (for supplementary / vertical angle figures)
  for (const ray of (cfg.extraRays ?? [])) {
    const vx  = ray.vx  ?? w / 2, vy = ray.vy ?? h * 0.65;
    const ra  = ray.angle * Math.PI / 180;
    const len = ray.length ?? 75;
    const ex  = vx + len * Math.cos(ra), ey = vy + len * Math.sin(ra);
    out += `<line x1="${vx.toFixed(2)}" y1="${vy.toFixed(2)}" x2="${ex.toFixed(2)}" y2="${ey.toFixed(2)}" stroke="#334155" stroke-width="1.8"/>`;
    if (ray.label) {
      const lpos = clampLabel(ex + (ex > vx ? 10 : -10), ey + (ey < vy ? -8 : 8), w, h);
      out += svgText(lpos.x, lpos.y, ray.label, { bold: true, fontSize: 13 });
    }
  }

  return svgWrap(w, h, out);
}

// ── Shape: composite ─────────────────────────────────────────────────
/**
 * Renders multiple sub-shapes on a single canvas.
 * cfg.shapes: array of sub-shape configs, each with optional offsetX/offsetY.
 * cfg.dimensions: [{x, y, label}] — shared labels drawn on top of everything.
 *
 * Example:
 *   { shape:"composite", width:360, height:240, shapes:[
 *       { shape:"rectangle", offsetX:0, ... },
 *       { shape:"triangle",  offsetX:0, ... }
 *     ], dimensions:[{x:180, y:230, label:"Total figure"}] }
 */
function drawComposite(cfg) {
  const w = cfg.width ?? 360, h = cfg.height ?? 260;
  let out = '';

  for (const sub of (cfg.shapes ?? [])) {
    const dx   = sub.offsetX ?? 0, dy = sub.offsetY ?? 0;
    const subW = sub.width   ?? w,  subH = sub.height ?? h;
    const subCfg = Object.assign({}, sub, { width: subW, height: subH });
    delete subCfg.offsetX; delete subCfg.offsetY;
    try {
      const subSvg = buildSVG(subCfg);
      // Extract the SVG inner content (strip outer <svg> wrapper)
      const inner  = subSvg.replace(/^<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
      if (dx !== 0 || dy !== 0) {
        out += `<g transform="translate(${dx.toFixed(1)},${dy.toFixed(1)})">${inner}</g>`;
      } else {
        out += inner;
      }
    } catch (e) {
      out += `<text x="${dx+10}" y="${dy+20}" font-size="10" fill="#dc2626">sub-shape error: ${e.message}</text>`;
    }
  }

  // Composite-level dimension annotations
  for (const dim of (cfg.dimensions ?? [])) {
    out += svgText(dim.x, dim.y, dim.label, { italic: true, fontSize: dim.fontSize ?? 13 });
  }
  // Composite-level arrows (for total measurements spanning multiple sub-shapes)
  for (const arr of (cfg.arrows ?? [])) {
    const sx = arr.x1, sy = arr.y1, ex = arr.x2, ey = arr.y2;
    const sc = arr.color ?? '#64748b';
    out += `<line x1="${sx}" y1="${sy}" x2="${ex}" y2="${ey}" stroke="${sc}" stroke-width="1.2" stroke-dasharray="4,3"/>`;
    out += arrowHead(sx, sy, ex, ey, sc);
    if (arr.label) {
      const lpos = clampLabel((sx+ex)/2 + (arr.labelOffsetX ?? 0), (sy+ey)/2 + (arr.labelOffsetY ?? -10), w, h);
      out += svgText(lpos.x, lpos.y, arr.label, { italic: true, fontSize: 12, fill: sc });
    }
  }

  return svgWrap(w, h, out);
}

// ── buildSVG dispatcher ─────────────────────────────────────────────
/**
 * buildSVG(config) — main SVG entry point.
 * Dispatches on config.shape.
 */
function buildSVG(config) {
  if (!config) return `<p style="color:#dc2626;font-size:12px;padding:8px">No SVG config provided</p>`;
  const cfg = normalizeConfig(config);
  try {
    switch (cfg.shape) {
      case 'triangle':
      case 'right_triangle':          return drawTriangle(cfg);
      case 'circle':                  return drawCircle(cfg);
      case 'number_line':             return drawNumberLine(cfg);
      case 'rectangle':               return drawRectangle(cfg);
      case 'parallel_transversal':    return drawParallelTransversal(cfg);
      case 'triangle_with_altitude':  return drawTriangleWithAltitude(cfg);
      case 'coordinate_plane':        return drawCoordinatePlane(cfg);
      case 'parallelogram':           return drawParallelogram(cfg);
      case 'trapezoid':               return drawParallelogram(cfg);
      case 'two_triangles':           return drawTwoTriangles(cfg);
      case 'normal_curve':            return drawNormalCurve(cfg);
      case 'regular_polygon':         return drawRegularPolygon(cfg);
      case 'venn_diagram':            return drawVennDiagram(cfg);
      case '3d_shape':                return drawShape3D(cfg);
      case 'angle_figure':            return drawAngleFigure(cfg);
      case 'composite':               return drawComposite(cfg);
      // Legacy physics shapes (kept for backward compatibility)
      case 'atwood_machine':          return drawAtwoodMachine(cfg);
      case 'spring_mass':             return drawSpringMass(cfg);
      case 'ray_diagram':             return drawRayDiagram(cfg);
      // Elements array fallback
      default:
        if (cfg.elements)  return renderSVGElements(cfg);
        if (cfg.sections)  return renderSVGPieChart(cfg);
        return `<p style="color:#dc2626;font-size:12px;padding:8px">Unknown shape: ${cfg.shape}</p>`;
    }
  } catch (e) {
    return `<p style="color:#dc2626;font-size:12px;padding:8px">SVG error: ${e.message}</p>`;
  }
}

// ── Legacy physics shapes (preserved for backward compat) ───────────
function drawAtwoodMachine(cfg) {
  const w = cfg.width ?? 240, h = cfg.height ?? 290;
  const cx = w / 2, ceilY = 16, pR = 22, pY = ceilY + 38;
  const blockW = 52, blockH = 38, strBot = pY + 125;
  const lx = cx - pR, rx = cx + pR;
  let s = '';
  s += `<line x1="0" y1="${ceilY}" x2="${w}" y2="${ceilY}" stroke="#64748b" stroke-width="3"/>`;
  for (let bx = 16; bx < w; bx += 14)
    s += `<line x1="${bx}" y1="${ceilY - 9}" x2="${bx - 9}" y2="${ceilY}" stroke="#94a3b8" stroke-width="1"/>`;
  s += `<line x1="${cx}" y1="${ceilY}" x2="${cx}" y2="${pY - pR}" stroke="#64748b" stroke-width="2"/>`;
  s += `<circle cx="${cx}" cy="${pY}" r="${pR}" fill="#f1f5f9" stroke="#334155" stroke-width="2.5"/>`;
  s += `<circle cx="${cx}" cy="${pY}" r="5" fill="#334155"/>`;
  s += `<line x1="${lx}" y1="${pY}" x2="${lx}" y2="${strBot}" stroke="#1e293b" stroke-width="1.8"/>`;
  s += `<line x1="${rx}" y1="${pY}" x2="${rx}" y2="${strBot}" stroke="#1e293b" stroke-width="1.8"/>`;
  const m1x = lx - blockW / 2;
  s += `<rect x="${m1x}" y="${strBot}" width="${blockW}" height="${blockH}" fill="#bfdbfe" stroke="#2563eb" stroke-width="2" rx="3"/>`;
  s += svgText(lx, strBot + blockH / 2 + 5, cfg.m1Label ?? 'm₁', { fontSize: 12, fill: '#1e40af', bold: true });
  const m2x = rx - blockW / 2;
  s += `<rect x="${m2x}" y="${strBot}" width="${blockW}" height="${blockH}" fill="#fee2e2" stroke="#dc2626" stroke-width="2" rx="3"/>`;
  s += svgText(rx, strBot + blockH / 2 + 5, cfg.m2Label ?? 'm₂', { fontSize: 12, fill: '#991b1b', bold: true });
  if (cfg.showAcceleration !== false) {
    const al = 26;
    s += `<line x1="${lx}" y1="${strBot - 4}" x2="${lx}" y2="${strBot - 4 - al}" stroke="#16a34a" stroke-width="1.8"/>`;
    s += arrowHead(lx, strBot - 4, lx, strBot - 4 - al, '#16a34a');
    s += svgText(lx - 15, strBot - 4 - al / 2, 'a', { fontSize: 11, fill: '#16a34a', italic: true });
    const m2bot = strBot + blockH;
    s += `<line x1="${rx}" y1="${m2bot + 4}" x2="${rx}" y2="${m2bot + 4 + al}" stroke="#dc2626" stroke-width="1.8"/>`;
    s += arrowHead(rx, m2bot + 4, rx, m2bot + 4 + al, '#dc2626');
    s += svgText(rx + 14, m2bot + 4 + al / 2, 'a', { fontSize: 11, fill: '#dc2626', italic: true });
  }
  return svgWrap(w, h, s);
}

function drawSpringMass(cfg) {
  const w = cfg.width ?? 330, h = cfg.height ?? 165;
  const wallW = 18, wallX = 22;
  const groundY = h - 25, wallH = 105, wallY = groundY - wallH;
  const blockW = 54, blockH = 48;
  const blockX = w - blockW - 20, blockY = groundY - blockH;
  const springY = blockY + blockH / 2;
  const sx1 = wallX + wallW, sx2 = blockX;
  let s = '';
  s += `<line x1="${wallX}" y1="${groundY}" x2="${blockX + blockW + 12}" y2="${groundY}" stroke="#64748b" stroke-width="1.5"/>`;
  for (let bx = wallX; bx < blockX + blockW + 12; bx += 12)
    s += `<line x1="${bx}" y1="${groundY}" x2="${bx + 8}" y2="${groundY + 8}" stroke="#94a3b8" stroke-width="1"/>`;
  s += `<rect x="${wallX - wallW}" y="${wallY}" width="${wallW}" height="${wallH}" fill="#e2e8f0" stroke="#64748b" stroke-width="1.5"/>`;
  const coils = 8, len = sx2 - sx1, seg = len / (coils * 2 + 2), amp = 15;
  let pts = `${sx1},${springY} ${sx1 + seg},${springY}`;
  for (let i = 0; i < coils; i++) {
    const xb = sx1 + seg + i * 2 * seg;
    pts += ` ${xb + seg},${springY - amp} ${xb + 2 * seg},${springY + amp}`;
  }
  pts += ` ${sx2 - seg},${springY} ${sx2},${springY}`;
  s += `<polyline points="${pts}" fill="none" stroke="#334155" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>`;
  s += svgText((sx1 + sx2) / 2, springY - amp - 10, cfg.kLabel ?? 'k', { fontSize: 12, fill: '#475569' });
  s += `<rect x="${blockX}" y="${blockY}" width="${blockW}" height="${blockH}" fill="#bfdbfe" stroke="#2563eb" stroke-width="2" rx="3"/>`;
  s += svgText(blockX + blockW / 2, blockY + blockH / 2 + 5, cfg.blockLabel ?? 'm', { fontSize: 13, fill: '#1e40af', bold: true });
  return svgWrap(w, h, s);
}

function drawRayDiagram(cfg) {
  const w = cfg.width ?? 340, h = cfg.height ?? 230;
  const lensX = cfg.lensX ?? 110, axisY = Math.round(h / 2);
  const fPx = cfg.fPx ?? 40, uPx = cfg.uPx ?? 60, vPx = cfg.vPx ?? 120;
  const objH = cfg.objH ?? 35, imgH = Math.round(objH * vPx / uPx);
  const lensHH = cfg.lensHH ?? 65, bulge = 14;
  const objX = lensX - uPx, imgX = lensX + vPx;
  const fLX  = lensX - fPx, fRX  = lensX + fPx;
  let s = '';
  s += `<line x1="8" y1="${axisY}" x2="${w - 8}" y2="${axisY}" stroke="#94a3b8" stroke-width="1" stroke-dasharray="5,3"/>`;
  s += `<path d="M ${lensX} ${axisY - lensHH} Q ${lensX + bulge} ${axisY} ${lensX} ${axisY + lensHH} Q ${lensX - bulge} ${axisY} ${lensX} ${axisY - lensHH} Z" fill="#bfdbfe" fill-opacity="0.45" stroke="#2563eb" stroke-width="1.8"/>`;
  s += svgText(lensX, axisY - lensHH - 7, 'Convex Lens', { fontSize: 9, fill: '#2563eb' });
  s += `<circle cx="${fLX}" cy="${axisY}" r="3.5" fill="#dc2626"/>`;
  s += svgText(fLX, axisY + 13, 'F', { fontSize: 10, fill: '#dc2626' });
  s += `<circle cx="${fRX}" cy="${axisY}" r="3.5" fill="#dc2626"/>`;
  s += svgText(fRX, axisY + 13, "F'", { fontSize: 10, fill: '#dc2626' });
  s += `<line x1="${objX}" y1="${axisY}" x2="${objX}" y2="${axisY - objH}" stroke="#334155" stroke-width="2.2"/>`;
  s += arrowHead(objX, axisY, objX, axisY - objH, '#334155');
  s += `<line x1="${imgX}" y1="${axisY}" x2="${imgX}" y2="${axisY + imgH}" stroke="#dc2626" stroke-width="2" stroke-dasharray="5,3"/>`;
  s += arrowHead(imgX, axisY, imgX, axisY + imgH, '#dc2626');
  s += `<line x1="${objX}" y1="${axisY - objH}" x2="${lensX}" y2="${axisY - objH}" stroke="#16a34a" stroke-width="1.3"/>`;
  s += `<line x1="${lensX}" y1="${axisY - objH}" x2="${imgX}" y2="${axisY + imgH}" stroke="#16a34a" stroke-width="1.3"/>`;
  s += `<line x1="${objX}" y1="${axisY - objH}" x2="${imgX}" y2="${axisY + imgH}" stroke="#7c3aed" stroke-width="1.3"/>`;
  return svgWrap(w, h, s);
}

// ───────────────────────────────────────────────────────────────────
// SECTION 3 — CHART.JS RENDERERS
// ───────────────────────────────────────────────────────────────────

const TICK_COLOR = '#475569';
const GRID_COLOR = '#e2e8f0';
const FONT = { size: 11, family: 'system-ui, sans-serif' };

function gridColor(zeroLine) {
  return zeroLine
    ? (ctx) => ctx.tick.value === 0 ? '#94a3b8' : GRID_COLOR
    : GRID_COLOR;
}
function gridWidth(zeroLine) {
  return zeroLine ? (ctx) => ctx.tick.value === 0 ? 1.5 : 0.5 : 0.5;
}

function linearScale(ax, zeroLine = false) {
  return {
    type: 'linear',
    min:  ax?.min,
    max:  ax?.max,
    title: ax?.label ? { display: true, text: ax.label, color: TICK_COLOR, font: FONT } : { display: false },
    ticks: { stepSize: ax?.stepSize, color: TICK_COLOR, font: FONT },
    grid:  { color: gridColor(zeroLine), lineWidth: gridWidth(zeroLine), drawBorder: false },
    border: { color: '#cbd5e1' }
  };
}

function categoryScale(ax) {
  return {
    title: ax?.label ? { display: true, text: ax.label, color: TICK_COLOR, font: FONT } : { display: false },
    ticks: { color: TICK_COLOR, font: FONT },
    grid:  { color: GRID_COLOR, lineWidth: 0.5, drawBorder: false },
    border: { color: '#cbd5e1' }
  };
}

function basePlugins(config, multiDataset) {
  return {
    animation: false,
    responsive: false,
    plugins: {
      legend: {
        display: multiDataset,
        labels: { color: TICK_COLOR, font: FONT, boxWidth: 18, padding: 10 }
      },
      title: {
        display: !!config.title,
        text: config.title ?? '',
        color: '#1e293b',
        font: { size: 13, weight: '600' },
        padding: { bottom: 6 }
      }
    }
  };
}

/** Normalize a dataset from AI-generator shorthand to Chart.js format. */
function normalizeDataset(ds) {
  const out = Object.assign({}, ds);

  // points[] → data[]
  if (ds.points && !ds.data) {
    out.data = ds.points;
    delete out.points;
  }
  // values[] → data[]
  if (ds.values && !ds.data) {
    out.data = ds.values;
    delete out.values;
  }
  // color → borderColor / backgroundColor / pointBackgroundColor
  if (ds.color && !ds.borderColor) {
    out.borderColor          = ds.color;
    out.pointBackgroundColor = ds.color;
    out.backgroundColor      = ds.color + '26'; // ~15% opacity
    delete out.color;
  }
  // showPoints flag
  if (ds.showPoints === false) out.pointRadius = 0;
  else if (ds.showPoints === true && out.pointRadius == null) out.pointRadius = 5;

  return out;
}

// ── bar chart ───────────────────────────────────────────────────────
function renderBarChart(canvasId, config) {
  const categories = config.categories ?? config.datasets?.[0]?.categories ?? [];
  const datasets   = (config.datasets ?? []).map(ds => ({
    label:           ds.label ?? '',
    data:            ds.values ?? ds.data ?? [],
    backgroundColor: ds.colors ?? hexAlpha(ds.color ?? '#3b82f6', 0.7),
    borderColor:     ds.borderColors ?? ds.color ?? '#2563eb',
    borderWidth:     1.5,
    borderRadius:    3
  }));

  // Value labels plugin — only for single-dataset bar charts
  const pluginsArr = [];
  if (datasets.length === 1) {
    pluginsArr.push({
      id: 'barValueLabels',
      afterDatasetsDraw(chart) {
        const ctx = chart.ctx;
        chart.data.datasets.forEach((dataset, di) => {
          const meta = chart.getDatasetMeta(di);
          meta.data.forEach((bar, i) => {
            const value = dataset.data[i];
            if (value == null) return;
            ctx.save();
            ctx.fillStyle = '#334155';
            ctx.font = '10px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillText(value, bar.x, bar.y - 2);
            ctx.restore();
          });
        });
      }
    });
  }

  new Chart(document.getElementById(canvasId), {
    type: 'bar',
    plugins: pluginsArr,
    data: { labels: categories, datasets },
    options: {
      ...basePlugins(config, datasets.length > 1),
      scales: {
        x: { ...categoryScale(config.xAxis), stacked: config.stacked ?? false },
        y: {
          ...categoryScale(config.yAxis),
          type: 'linear',
          stacked: config.stacked ?? false,
          min: config.yAxis?.min,
          max: config.yAxis?.max,
          ticks: { stepSize: config.yAxis?.stepSize, color: TICK_COLOR, font: FONT }
        }
      }
    }
  });
}

// ── histogram ───────────────────────────────────────────────────────
function renderHistogram(canvasId, config) {
  const categories = config.categories ?? [];
  const values     = config.values ?? config.datasets?.[0]?.values ?? [];
  const color      = config.color ?? config.datasets?.[0]?.color ?? '#0d9488';

  new Chart(document.getElementById(canvasId), {
    type: 'bar',
    data: {
      labels: categories,
      datasets: [{
        label: config.label ?? '',
        data:  values,
        backgroundColor: hexAlpha(color, 0.75),
        borderColor:     color,
        borderWidth: 1.5,
        borderRadius: 0,
        categoryPercentage: 1.0,
        barPercentage:      1.0
      }]
    },
    options: {
      ...basePlugins(config, false),
      scales: {
        x: categoryScale(config.xAxis),
        y: {
          ...categoryScale(config.yAxis),
          type: 'linear',
          min: config.yAxis?.min ?? 0,
          max: config.yAxis?.max,
          ticks: { stepSize: config.yAxis?.stepSize, color: TICK_COLOR, font: FONT },
          grid: { color: GRID_COLOR, lineWidth: 0.5 }
        }
      }
    }
  });
}

// ── line chart (category x-axis) ────────────────────────────────────
function renderLineChart(canvasId, config) {
  const labels = config.categories ?? config.datasets?.[0]?.categories ?? [];
  const datasets = (config.datasets ?? []).map(ds => ({
    label:                ds.label ?? '',
    data:                 ds.values ?? ds.data ?? [],
    borderColor:          ds.color ?? '#2563eb',
    backgroundColor:      hexAlpha(ds.color ?? '#2563eb', 0.12),
    borderWidth:          2,
    pointRadius:          ds.showPoints === false ? 0 : (ds.pointRadius ?? 4),
    pointBackgroundColor: ds.color ?? '#2563eb',
    tension: 0,
    fill: false
  }));

  new Chart(document.getElementById(canvasId), {
    type: 'line',
    data: { labels, datasets },
    options: {
      ...basePlugins(config, datasets.length > 1),
      scales: {
        x: categoryScale(config.xAxis),
        y: {
          ...categoryScale(config.yAxis),
          type: 'linear',
          min: config.yAxis?.min,
          max: config.yAxis?.max,
          ticks: { stepSize: config.yAxis?.stepSize, color: TICK_COLOR, font: FONT },
          grid: { color: GRID_COLOR, lineWidth: 0.5 }
        }
      }
    }
  });
}

// ── scatter chart ───────────────────────────────────────────────────
function renderScatterChart(canvasId, config) {
  const datasets = (config.datasets ?? []).map(ds => ({
    type:            'scatter',
    label:           ds.label ?? '',
    data:            ds.points ?? ds.data ?? [],
    parsing:         { xAxisKey: 'x', yAxisKey: 'y' },
    borderColor:     ds.color ?? '#2563eb',
    backgroundColor: hexAlpha(ds.color ?? '#2563eb', 0.75),
    borderWidth:     1.5,
    pointRadius:     ds.showPoints === false ? 0 : (ds.pointRadius ?? 5),
    showLine:        ds.showLine ?? (ds.showPoints === false ? true : false),
    tension:         0
  }));

  // Best fit line
  if (config.bestFitLine?.show) {
    const allPoints = (config.datasets ?? []).flatMap(ds => ds.points ?? ds.data ?? []);
    if (allPoints.length >= 2) {
      const { slope, intercept } = leastSquares(allPoints);
      const xMin = config.xAxis?.min ?? Math.min(...allPoints.map(p => p.x));
      const xMax = config.xAxis?.max ?? Math.max(...allPoints.map(p => p.x));
      datasets.push({
        type:            'line',
        label:           config.bestFitLine.label ?? 'Best Fit',
        data:            [{ x: xMin, y: slope * xMin + intercept }, { x: xMax, y: slope * xMax + intercept }],
        parsing:         { xAxisKey: 'x', yAxisKey: 'y' },
        borderColor:     config.bestFitLine.color ?? '#dc2626',
        backgroundColor: 'transparent',
        borderWidth:     2,
        borderDash:      [6, 4],
        pointRadius:     0,
        showLine:        true,
        tension:         0
      });
    }
  }

  new Chart(document.getElementById(canvasId), {
    type: 'scatter',
    data: { datasets },
    options: {
      ...basePlugins(config, datasets.length > 1),
      scales: {
        x: { ...linearScale(config.xAxis) },
        y: linearScale(config.yAxis)
      }
    }
  });
}

// ── pie chart ───────────────────────────────────────────────────────
function renderPieChart(canvasId, config) {
  const segments = config.segments ?? [];
  const showLegend = config.showLegend !== false;

  new Chart(document.getElementById(canvasId), {
    type: 'pie',
    data: {
      labels:   segments.map(s => s.label ?? ''),
      datasets: [{
        data:            segments.map(s => s.value),
        backgroundColor: segments.map(s => s.color ?? '#94a3b8'),
        borderColor:     '#fff',
        borderWidth:     2
      }]
    },
    options: {
      ...basePlugins(config, false),
      plugins: {
        legend: {
          display: showLegend,
          position: 'bottom',
          labels: { color: TICK_COLOR, font: FONT, boxWidth: 14, padding: 10 }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const pct   = ((ctx.raw / total) * 100).toFixed(1);
              return ` ${ctx.label}: ${pct}%`;
            }
          }
        }
      }
    }
  });
}

// ── boxplot (simulated with floating bars + afterDraw) ──────────────
function renderBoxPlot(canvasId, config) {
  const labels         = (config.groups ?? []).map(g => g.label);
  const whiskerBotData = (config.groups ?? []).map(g => [g.min, g.q1]);
  const boxData        = (config.groups ?? []).map(g => [g.q1, g.q3]);
  const whiskerTopData = (config.groups ?? []).map(g => [g.q3, g.max]);

  const boxPlugin = {
    id: 'boxplotOverlay',
    afterDraw(chart) {
      const ctx  = chart.ctx;
      const ys   = chart.scales.y;
      const meta = chart.getDatasetMeta(1);

      (config.groups ?? []).forEach((g, i) => {
        const bar = meta.data[i];
        if (!bar) return;
        const bx = bar.x, bw = bar.width;
        const capW = Math.max(bw * 0.38, 12);

        // Median line (bold, white, over box)
        const medY = ys.getPixelForValue(g.median);
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(bx - bw / 2, medY); ctx.lineTo(bx + bw / 2, medY);
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.stroke();
        ctx.restore();

        // Whisker lines
        const minY = ys.getPixelForValue(g.min);
        const q1Y  = ys.getPixelForValue(g.q1);
        const q3Y  = ys.getPixelForValue(g.q3);
        const maxY = ys.getPixelForValue(g.max);
        ctx.save();
        ctx.strokeStyle = g.color ?? '#334155'; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.moveTo(bx, minY); ctx.lineTo(bx, q1Y); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(bx, q3Y);  ctx.lineTo(bx, maxY); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(bx - capW / 2, minY); ctx.lineTo(bx + capW / 2, minY); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(bx - capW / 2, maxY); ctx.lineTo(bx + capW / 2, maxY); ctx.stroke();
        ctx.restore();

        // Median value label
        ctx.save();
        ctx.fillStyle = '#1e293b'; ctx.font = 'bold 10px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(g.median, bx, medY - 6);
        ctx.restore();

        // Min and Max value labels at whisker ends
        ctx.save();
        ctx.fillStyle = '#475569'; ctx.font = '9px system-ui';
        ctx.textAlign = 'center';
        ctx.fillText(g.min, bx, minY + 12);
        ctx.fillText(g.max, bx, maxY - 4);
        ctx.restore();
      });
    }
  };

  new Chart(document.getElementById(canvasId), {
    type: 'bar',
    plugins: [boxPlugin],
    data: {
      labels,
      datasets: [
        { data: whiskerBotData, backgroundColor: 'transparent', borderColor: 'transparent', borderWidth: 0, borderSkipped: false, barPercentage: 0.45 },
        { data: boxData, backgroundColor: (config.groups ?? []).map(g => hexAlpha(g.color ?? '#3b82f6', 0.45)), borderColor: (config.groups ?? []).map(g => g.color ?? '#3b82f6'), borderWidth: 1.5, borderSkipped: false, barPercentage: 0.45 },
        { data: whiskerTopData, backgroundColor: 'transparent', borderColor: 'transparent', borderWidth: 0, borderSkipped: false, barPercentage: 0.45 }
      ]
    },
    options: {
      ...basePlugins(config, false),
      scales: {
        x: categoryScale(config.xAxis),
        y: {
          ...categoryScale(config.yAxis),
          type: 'linear',
          min: config.yAxis?.min,
          max: config.yAxis?.max,
          ticks: { stepSize: config.yAxis?.stepSize, color: TICK_COLOR, font: FONT },
          grid: { color: GRID_COLOR, lineWidth: 0.5 }
        }
      }
    }
  });
}

// ── dotplot (afterDraw stacked circles) ─────────────────────────────
function renderDotPlot(canvasId, config) {
  const values  = config.values ?? [];
  const dotR    = config.dotRadius ?? 7;
  const dotGap  = 2;
  const color   = config.color ?? '#3b82f6';
  const freq = {};
  for (const v of values) freq[v] = (freq[v] ?? 0) + 1;
  const maxFreq = Math.max(...Object.values(freq), 1);

  const dotPlugin = {
    id: 'dotplotDots',
    afterDraw(chart) {
      const ctx  = chart.ctx;
      const xs   = chart.scales.x;
      const yBot = chart.scales.y.bottom;
      ctx.save();
      for (const [val, cnt] of Object.entries(freq)) {
        const cx = xs.getPixelForValue(Number(val));
        for (let i = 0; i < cnt; i++) {
          const cy = yBot - dotR - i * (dotR * 2 + dotGap) - dotGap;
          ctx.beginPath();
          ctx.arc(cx, cy, dotR, 0, Math.PI * 2);
          ctx.fillStyle   = hexAlpha(color, 0.8);
          ctx.fill();
          ctx.strokeStyle = color;
          ctx.lineWidth   = 1;
          ctx.stroke();
        }
      }
      ctx.restore();
    }
  };

  const xAx = config.xAxis ?? {};
  new Chart(document.getElementById(canvasId), {
    type: 'scatter',
    plugins: [dotPlugin],
    data: { datasets: [{ data: [] }] },
    options: {
      ...basePlugins(config, false),
      scales: {
        x: {
          type: 'linear',
          min: (xAx.min ?? Math.min(...values, 0)) - 0.5,
          max: (xAx.max ?? Math.max(...values, 5)) + 0.5,
          ticks: { stepSize: 1, callback: v => Number.isInteger(v) ? v : '', color: TICK_COLOR, font: FONT },
          title: xAx.label ? { display: true, text: xAx.label, color: TICK_COLOR, font: FONT } : { display: false },
          grid:   { color: GRID_COLOR, lineWidth: 0.5 },
          border: { color: '#cbd5e1' }
        },
        y: { min: 0, max: maxFreq + 2, display: false }
      }
    }
  });
}

/**
 * renderChart(canvasId, config) — main Chart.js dispatcher.
 * Dispatches on config.chartType.
 * Always destroys any existing chart on the canvas first.
 */
function renderChart(canvasId, config) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  // Destroy any existing chart on this canvas
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  try {
    switch (config.chartType) {
      case 'bar':       renderBarChart(canvasId, config);     break;
      case 'histogram': renderHistogram(canvasId, config);    break;
      case 'line':      renderLineChart(canvasId, config);    break;
      case 'scatter':   renderScatterChart(canvasId, config); break;
      case 'pie':       renderPieChart(canvasId, config);     break;
      case 'boxplot':   renderBoxPlot(canvasId, config);      break;
      case 'dotplot':   renderDotPlot(canvasId, config);      break;
      default:
        console.warn('[renderer] Unknown chartType:', config.chartType);
    }
  } catch (e) {
    console.error('[renderer] Chart error:', e);
  }
}

// ───────────────────────────────────────────────────────────────────
// SECTION 4 — MASTER DISPATCHER (used by app.js)
// ───────────────────────────────────────────────────────────────────

/**
 * renderDiagram(diagramConfig, hostEl)
 * Called by app.js when a question has a diagram.
 */
function renderDiagram(diagramConfig, hostEl) {
  if (!diagramConfig || !hostEl) return;

  // Normalise: some questions store "type" instead of "diagramType"
  const dtype = diagramConfig.diagramType ?? diagramConfig.type ?? '';

  if (dtype === 'svg' || dtype === 'svg_programmatic') {
    const cfg = diagramConfig.svgConfig;
    try {
      if (!cfg) {
        hostEl.innerHTML = `<p class="text-red-500 text-xs p-2">Missing svgConfig</p>`;
        return;
      }
      // Normalise: "shapes" is accepted as an alias for "elements"
      // Also merge "labels" arrays (text annotations) into elements
      const normCfg = cfg.elements ? cfg : (cfg.shapes ? {
        ...cfg,
        elements: [
          ...cfg.shapes,
          ...(cfg.labels ?? []).map(l => ({ type: 'text', ...l }))
        ]
      } : cfg);
      if (normCfg.elements)  {
        hostEl.innerHTML = renderSVGElements(normCfg);
      } else if (normCfg.sections) {
        hostEl.innerHTML = renderSVGPieChart(normCfg);
      } else {
        hostEl.innerHTML = buildSVG(normCfg);
      }
    } catch (e) {
      hostEl.innerHTML = `<p class="text-red-500 text-xs p-2">SVG error: ${e.message}</p>`;
    }

  } else if (dtype === 'chartjs') {
    const cfg = diagramConfig.chartConfig;
    if (!cfg) {
      hostEl.innerHTML = `<p class="text-red-500 text-xs p-2">Missing chartConfig</p>`;
      return;
    }
    // Normalize field names — Claude sometimes uses Chart.js native names instead of renderer names.
    // "labels" at top level → "categories"  (bar x-axis category labels)
    // dataset "backgroundColor" (string or array) → "color" / "colors"
    const normalCfg = Object.assign({}, cfg);
    if (!normalCfg.categories && normalCfg.labels && Array.isArray(normalCfg.labels)) {
      normalCfg.categories = normalCfg.labels;
    }
    if (normalCfg.datasets) {
      normalCfg.datasets = normalCfg.datasets.map(ds => {
        const out = Object.assign({}, ds);
        if (out.backgroundColor !== undefined && out.color === undefined && out.colors === undefined) {
          if (Array.isArray(out.backgroundColor)) out.colors = out.backgroundColor;
          else                                     out.color  = out.backgroundColor;
        }
        return out;
      });
      normalCfg.datasets = normalCfg.datasets.map(normalizeDataset);
    }

    const id = 'chart-' + Math.random().toString(36).slice(2);
    const canvas = document.createElement('canvas');
    canvas.id     = id;
    canvas.width  = cfg.width  ?? 300;
    canvas.height = cfg.height ?? 220;
    hostEl.innerHTML = '';
    hostEl.appendChild(canvas);
    try {
      renderChart(id, normalCfg);
    } catch (e) {
      hostEl.innerHTML = `<p class="text-red-500 text-xs p-2">Chart error: ${e.message}</p>`;
    }
  }
}

// ───────────────────────────────────────────────────────────────────
// SECTION 5 — KATEX HELPER
// ───────────────────────────────────────────────────────────────────

/**
 * renderKaTeXIn(el)
 * Re-renders any KaTeX math inside the given element.
 * Called by app.js after injecting question HTML.
 */
function renderKaTeXIn(el) {
  if (typeof renderMathInElement !== 'function') {
    setTimeout(() => renderKaTeXIn(el), 100);
    return;
  }
  renderMathInElement(el, {
    delimiters: [
      { left: '\\(',  right: '\\)',  display: false },
      { left: '\\[',  right: '\\]',  display: true  },
      { left: '$$',   right: '$$',   display: true  },
      { left: '$',    right: '$',    display: false }
    ],
    throwOnError: false
  });
}

// ══════════════════════════════════════════════════════════════
// ANIMATION PLAYER  (step-by-step SVG geometry animation)
// ══════════════════════════════════════════════════════════════

(function injectAnimCSS() {
  if (document.getElementById('anim-player-css')) return;
  const style = document.createElement('style');
  style.id = 'anim-player-css';
  style.textContent = `
    .anim-player {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 0.75rem;
      padding: 0.75rem;
      margin-bottom: 1rem;
    }
    .anim-player.anim-player-synced {
      padding-bottom: 0.4rem;
      margin-bottom: 0.75rem;
    }
    .anim-player-synced .anim-caption {
      font-size: 0.72rem;
      background: #f1f5f9;
      border-top: 1px solid #e2e8f0;
      border-radius: 0 0 0.5rem 0.5rem;
      padding: 0.3rem 0.75rem;
      margin: 0.2rem 0 0.4rem;
      color: #475569;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      min-height: 1.5em;
    }
    .anim-cap-step {
      font-weight: 700;
      color: #2563eb;
      white-space: nowrap;
      flex-shrink: 0;
    }
    .anim-dots-synced {
      display: flex;
      justify-content: center;
      gap: 5px;
      margin: 0 0 0.35rem;
    }
    .anim-svg-wrap {
      position: relative;
      display: block;
      width: 100%;
    }
    .anim-svg-wrap svg { display: block; overflow: visible; width: 100%; height: 100%; }
    .anim-overlays {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .anim-caption {
      font-size: 0.78rem;
      font-weight: 600;
      color: #475569;
      text-align: center;
      min-height: 1.3em;
      margin: 0.5rem 0 0.35rem;
      letter-spacing: 0.01em;
    }
    .anim-controls {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
    }
    .anim-btn {
      display: inline-flex; align-items: center; justify-content: center;
      width: 1.8rem; height: 1.8rem;
      border-radius: 50%;
      border: 1.5px solid #cbd5e1;
      background: #fff;
      color: #334155;
      font-size: 0.85rem;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }
    .anim-btn:hover:not(:disabled) { background: #f1f5f9; border-color: #94a3b8; }
    .anim-btn:disabled { opacity: 0.35; cursor: default; }
    .anim-dots { display: flex; gap: 5px; align-items: center; }
    .anim-dot {
      width: 7px; height: 7px;
      border-radius: 50%;
      background: #cbd5e1;
      transition: background 0.2s, transform 0.2s;
      cursor: pointer;
    }
    .anim-dot.active { background: #3b82f6; transform: scale(1.3); }
    @keyframes anim-draw-path {
      from { stroke-dashoffset: 3000; }
      to   { stroke-dashoffset: 0; }
    }
    @keyframes anim-fade-in {
      from { opacity: 0; transform: translateY(3px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .anim-draw {
      stroke-dasharray: 3000;
      stroke-dashoffset: 3000;
      animation: anim-draw-path 0.5s cubic-bezier(0.22,0.61,0.36,1) forwards;
    }
    .anim-fade {
      opacity: 0;
      animation: anim-fade-in 0.35s cubic-bezier(0.22,0.61,0.36,1) forwards;
    }
    .anim-overlay-label {
      position: absolute;
      transform: translate(-50%, -50%);
      font-family: 'Inter', sans-serif;
      pointer-events: none;
    }
    .anim-overlay-label.anim-fade {
      opacity: 0;
      animation: anim-fade-in 0.35s cubic-bezier(0.22,0.61,0.36,1) forwards;
    }
  `;
  document.head.appendChild(style);
})();

/** Global registry of active animation players. */
window._animPlayers = window._animPlayers || {};

/**
 * Render an animation player into `container`.
 * @param {object}  cfg          — parsed animation JSON (must have .frames array)
 * @param {Element} container    — DOM element to render into
 * @param {object}  [opts]       — options
 * @param {boolean} [opts.synced] — true = no controls, skip katex overlays (steps shown below)
 * @returns {string|null} uid — player ID for external control (animGoTo)
 */
// ── Compute tight bounding box across all animation frames ──────────────
function _animBBox(frames) {
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const exp = (x, y) => { x0=Math.min(x0,x); y0=Math.min(y0,y); x1=Math.max(x1,x); y1=Math.max(y1,y); };

  for (const frame of frames) {
    for (const el of (frame.elements || [])) {
      switch (el.type) {
        case 'polygon':
          (el.points||[]).forEach(([px,py]) => exp(px, py));
          break;
        case 'line':
          exp(el.x1, el.y1); exp(el.x2, el.y2);
          break;
        case 'circle': case 'sector':
          exp(el.cx-(el.r||0), el.cy-(el.r||0));
          exp(el.cx+(el.r||0), el.cy+(el.r||0));
          break;
        case 'arc': {
          const ar = el.r || 20;
          exp(el.cx - ar, el.cy - ar); exp(el.cx + ar, el.cy + ar);
          // Account for auto-positioned label
          if (el.label) {
            const mid = ((el.startDeg||0) + (el.endDeg||90)) / 2 * Math.PI / 180;
            const lr = ar * 1.75;
            const llen = String(el.label).length * (el.labelSize || 12) * 0.55;
            exp(el.cx + lr*Math.cos(mid) - llen, el.cy + lr*Math.sin(mid) - 14);
            exp(el.cx + lr*Math.cos(mid) + llen, el.cy + lr*Math.sin(mid) + 6);
          }
          break;
        }
        case 'rect':
          exp(el.x, el.y); exp(el.x+(el.width||0), el.y+(el.height||0));
          break;
        case 'dot':
          exp(el.x-(el.r||4), el.y-(el.r||4)); exp(el.x+(el.r||4), el.y+(el.r||4));
          break;
        case 'right_angle':
          if (el.vertex) exp(el.vertex[0], el.vertex[1]);
          if (el.leg1)   exp(el.leg1[0],   el.leg1[1]);
          if (el.leg2)   exp(el.leg2[0],   el.leg2[1]);
          break;
        case 'side_label': {
          const [slx1,sly1] = el.p1||[0,0], [slx2,sly2] = el.p2||[0,0];
          const smx=(slx1+slx2)/2, smy=(sly1+sly2)/2;
          const [sax,say] = el.awayFrom||[smx,smy];
          let sdx=smx-sax, sdy=smy-say;
          const sdl=Math.hypot(sdx,sdy)||1; sdx/=sdl; sdy/=sdl;
          const so=el.offset??18, slx=smx+sdx*so, sly2b=smy+sdy*so;
          const fs=el.fontSize||13, tw=(el.text||'').length*fs*0.58;
          exp(slx-tw/2-4, sly2b-fs); exp(slx+tw/2+4, sly2b+4);
          break;
        }
        case 'text': {
          const fs  = el.fontSize || 13;
          const len = String(el.text||'').length;
          const ta  = el.textAnchor || 'start';
          const tw  = len * fs * 0.58;
          const tx  = ta === 'middle' ? el.x - tw/2 : ta === 'end' ? el.x - tw : el.x;
          exp(tx - 4, el.y - fs); exp(tx + tw + 4, el.y + 4);
          break;
        }
      }
    }
  }
  if (!isFinite(x0)) return null;
  const PAD = 16;
  return { x: x0-PAD, y: y0-PAD, w: x1-x0+PAD*2, h: y1-y0+PAD*2 };
}

function renderAnimation(cfg, container, opts) {
  opts = opts || {};
  const synced = !!opts.synced;
  if (!container) return null;
  if (!cfg || !Array.isArray(cfg.frames) || cfg.frames.length === 0) {
    container.innerHTML = '';
    return null;
  }

  const w   = cfg.width  || 280;
  const h   = cfg.height || 260;
  const uid = 'ap_' + Math.random().toString(36).slice(2, 9);

  // Compute tight viewBox from actual element positions — figure always fills canvas
  const bb  = _animBBox(cfg.frames);
  const vb  = bb ? `${bb.x.toFixed(1)} ${bb.y.toFixed(1)} ${bb.w.toFixed(1)} ${bb.h.toFixed(1)}` : `0 0 ${w} ${h}`;

  const controlsHtml = synced
      ? `<div class="anim-dots anim-dots-synced" id="${uid}_dots"></div>`
      : `<div class="anim-controls">
        <button class="anim-btn" id="${uid}_prev" onclick="animStep('${uid}',-1)">&#8592;</button>
        <div class="anim-dots" id="${uid}_dots"></div>
        <button class="anim-btn" id="${uid}_next" onclick="animStep('${uid}',1)">&#8594;</button>
      </div>`;

  // Use tight bbox aspect-ratio for standalone mode; split-layout CSS overrides with flex height
  const arStyle = bb ? `aspect-ratio:${(bb.w/bb.h).toFixed(4)};` : `aspect-ratio:${w}/${h};`;

  container.innerHTML = `
    <div class="anim-player${synced ? ' anim-player-synced' : ''}">
      <div class="anim-svg-wrap" style="${arStyle}">
        <svg id="${uid}_svg" viewBox="${vb}" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;display:block;"></svg>
        <div id="${uid}_ov" class="anim-overlays"></div>
      </div>
      <div class="anim-caption" id="${uid}_cap"></div>
      ${controlsHtml}
    </div>`;

  window._animPlayers[uid] = { cfg, currentIdx: 0, synced, viewBox: vb };
  _animRenderFrame(uid, 0, false);
  return uid;
}

/** Called by Prev/Next buttons. */
function animStep(uid, dir) {
  const state = window._animPlayers[uid];
  if (!state) return;
  const next = state.currentIdx + dir;
  if (next < 0 || next >= state.cfg.frames.length) return;
  _animRenderFrame(uid, next, true);
}

function _animRenderFrame(uid, idx, animate) {
  const state = window._animPlayers[uid];
  if (!state) return;
  const { cfg } = state;
  const frames = cfg.frames;
  state.currentIdx = idx;

  const svgEl   = document.getElementById(uid + '_svg');
  const ovEl    = document.getElementById(uid + '_ov');
  const capEl   = document.getElementById(uid + '_cap');
  const dotsEl  = document.getElementById(uid + '_dots');
  const prevBtn = document.getElementById(uid + '_prev');
  const nextBtn = document.getElementById(uid + '_next');
  if (!svgEl || !ovEl) return;

  const { synced } = state;

  // Clear
  svgEl.innerHTML = '';
  ovEl.innerHTML  = '';

  // Each frame is a self-contained snapshot (includes all previous elements + new ones).
  // Detect "new" elements by comparing count with the previous frame.
  const currentElements = frames[idx].elements || [];
  const prevCount = idx > 0 ? (frames[idx - 1].elements || []).length : 0;

  const svgW = cfg.width  || 280;
  const svgH = cfg.height || 260;
  let newElIdx = 0;
  for (let ei = 0; ei < currentElements.length; ei++) {
    const isNew = animate && ei >= prevCount;
    const el = currentElements[ei];
    // In synced mode: skip katex overlays (formulas shown in step text below)
    if (synced && el.type === 'katex') continue;
    // Stagger new elements: each new element starts 75ms after the previous new one
    const animDelay = isNew ? newElIdx * 75 : 0;
    if (isNew) newElIdx++;
    _animRenderElement(svgEl, ovEl, el, isNew, animDelay, svgW, svgH);
  }

  // Caption: in synced mode show "Figure N of M: <caption>" as a contextual label below canvas
  if (capEl) {
    if (synced) {
      const frameLabel = `Figure ${idx + 1} of ${frames.length}`;
      capEl.innerHTML = `<span class="anim-cap-step">${frameLabel}:</span> ${frames[idx].caption || ''}`;
    } else {
      capEl.textContent = frames[idx].caption || '';
    }
  }

  // Dots: always clickable — in synced mode dots advance animation only (independent of steps)
  if (dotsEl) {
    dotsEl.innerHTML = frames.map((_, i) =>
      `<span class="anim-dot${i === idx ? ' active' : ''}" onclick="animGoTo('${uid}',${i})" title="Figure ${i+1}"></span>`
    ).join('');
  }
  // Prev/Next buttons only in standalone mode
  if (!synced) {
    if (prevBtn) prevBtn.disabled = idx === 0;
    if (nextBtn) nextBtn.disabled = idx === frames.length - 1;
  }

  // KaTeX in overlays — renderKaTeXIn is always available (defined in renderer.js)
  // scheduleKaTeX is a page-level helper and may not exist
  if (typeof renderKaTeXIn === 'function') renderKaTeXIn(ovEl);
  else if (typeof scheduleKaTeX === 'function') scheduleKaTeX([ovEl]);
}

function animGoTo(uid, idx) {
  const state = window._animPlayers[uid];
  if (!state) return;
  const clamped = Math.max(0, Math.min(idx, state.cfg.frames.length - 1));
  _animRenderFrame(uid, clamped, clamped > state.currentIdx);
}

const _SVG_NS = 'http://www.w3.org/2000/svg';

function _animRenderElement(svgEl, ovEl, el, isNew, animDelay, svgW, svgH) {
  svgW = svgW || 280; svgH = svgH || 260;
  const _applyAnim = (node, animClass) => {
    node.classList.add(animClass);
    if (animDelay) node.style.animationDelay = `${animDelay}ms`;
  };
  switch (el.type) {
    case 'polygon': {
      const pts = (el.points || []).map(p => `${p[0]},${p[1]}`).join(' ');
      const node = document.createElementNS(_SVG_NS, 'polygon');
      node.setAttribute('points', pts);
      node.setAttribute('stroke', el.stroke || '#334155');
      node.setAttribute('stroke-width', el.strokeWidth || 2);
      node.setAttribute('fill', el.fill || 'none');
      node.setAttribute('stroke-linejoin', 'round');
      if (isNew) _applyAnim(node, 'anim-draw');
      svgEl.appendChild(node);
      break;
    }
    case 'line': {
      const node = document.createElementNS(_SVG_NS, 'line');
      node.setAttribute('x1', el.x1); node.setAttribute('y1', el.y1);
      node.setAttribute('x2', el.x2); node.setAttribute('y2', el.y2);
      node.setAttribute('stroke', el.stroke || '#334155');
      node.setAttribute('stroke-width', el.strokeWidth || 2);
      node.setAttribute('stroke-linecap', 'round');
      if (el.dashed) node.setAttribute('stroke-dasharray', isNew ? '5,4 3000' : '5,4');
      if (isNew && !el.dashed) _applyAnim(node, 'anim-draw');
      if (isNew && el.dashed)  _applyAnim(node, 'anim-fade');
      svgEl.appendChild(node);
      break;
    }
    case 'right_angle': {
      const [vx, vy] = el.vertex;
      const [l1x, l1y] = el.leg1;
      const [l2x, l2y] = el.leg2;
      const size = el.size || 12;
      const d1x = l1x - vx, d1y = l1y - vy, len1 = Math.hypot(d1x, d1y) || 1;
      const d2x = l2x - vx, d2y = l2y - vy, len2 = Math.hypot(d2x, d2y) || 1;
      const u1x = d1x/len1, u1y = d1y/len1;
      const u2x = d2x/len2, u2y = d2y/len2;
      const p1x = vx + u1x*size, p1y = vy + u1y*size;
      const p2x = p1x + u2x*size, p2y = p1y + u2y*size;
      const p3x = vx + u2x*size, p3y = vy + u2y*size;
      const node = document.createElementNS(_SVG_NS, 'polyline');
      node.setAttribute('points', `${p1x},${p1y} ${p2x},${p2y} ${p3x},${p3y}`);
      node.setAttribute('stroke', el.stroke || '#334155');
      node.setAttribute('stroke-width', el.strokeWidth || 1.5);
      node.setAttribute('fill', 'none');
      if (isNew) _applyAnim(node, 'anim-fade');
      svgEl.appendChild(node);
      break;
    }
    case 'arc': {
      const { cx, cy, r = 20, startDeg = 0, endDeg = 90 } = el;
      const sRad = startDeg * Math.PI / 180;
      const eRad = endDeg   * Math.PI / 180;
      const x1 = cx + r * Math.cos(sRad), y1 = cy + r * Math.sin(sRad);
      const x2 = cx + r * Math.cos(eRad), y2 = cy + r * Math.sin(eRad);
      const large = Math.abs(endDeg - startDeg) > 180 ? 1 : 0;
      const node = document.createElementNS(_SVG_NS, 'path');
      node.setAttribute('d', `M${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2}`);
      node.setAttribute('stroke', el.stroke || '#64748b');
      node.setAttribute('stroke-width', el.strokeWidth || 1.5);
      node.setAttribute('fill', 'none');
      if (isNew) _applyAnim(node, 'anim-draw');
      svgEl.appendChild(node);
      // Auto-position label along the bisector at 1.75× arc radius — never overlaps the arc
      if (el.label) {
        const midRad = (sRad + eRad) / 2;
        const labelR = r * 1.75;
        const lx = cx + labelR * Math.cos(midRad);
        const ly = cy + labelR * Math.sin(midRad);
        const lNode = document.createElementNS(_SVG_NS, 'text');
        lNode.setAttribute('x', lx.toFixed(1));
        lNode.setAttribute('y', ly.toFixed(1));
        lNode.setAttribute('text-anchor', 'middle');
        lNode.setAttribute('dominant-baseline', 'central');
        lNode.setAttribute('font-size', el.labelSize || 12);
        lNode.setAttribute('font-family', "Georgia, serif");
        lNode.setAttribute('fill', el.labelColor || el.stroke || '#64748b');
        lNode.textContent = el.label;
        if (isNew) { _applyAnim(lNode, 'anim-fade'); if (animDelay) lNode.style.animationDelay = `${animDelay + 80}ms`; }
        svgEl.appendChild(lNode);
      }
      break;
    }
    case 'dot': {
      const node = document.createElementNS(_SVG_NS, 'circle');
      node.setAttribute('cx', el.x); node.setAttribute('cy', el.y);
      node.setAttribute('r',  el.r || 4);
      node.setAttribute('fill', el.fill || '#1e293b');
      if (isNew) _applyAnim(node, 'anim-fade');
      svgEl.appendChild(node);
      break;
    }
    case 'circle': {
      const node = document.createElementNS(_SVG_NS, 'circle');
      node.setAttribute('cx', el.cx); node.setAttribute('cy', el.cy);
      node.setAttribute('r',  el.r || 50);
      node.setAttribute('stroke', el.stroke || '#334155');
      node.setAttribute('stroke-width', el.strokeWidth || 2);
      node.setAttribute('fill', el.fill || '#f0f9ff');
      if (isNew) _applyAnim(node, 'anim-draw');
      svgEl.appendChild(node);
      break;
    }
    case 'rect': {
      const node = document.createElementNS(_SVG_NS, 'rect');
      node.setAttribute('x', el.x); node.setAttribute('y', el.y);
      node.setAttribute('width',  el.width  || 100);
      node.setAttribute('height', el.height || 80);
      node.setAttribute('stroke', el.stroke || '#334155');
      node.setAttribute('stroke-width', el.strokeWidth || 2);
      node.setAttribute('fill', el.fill || '#f0f9ff');
      if (el.rx) node.setAttribute('rx', el.rx);
      if (isNew) _applyAnim(node, 'anim-draw');
      svgEl.appendChild(node);
      break;
    }
    case 'sector': {
      // Filled sector: M cx,cy L x1,y1 A r,r 0 large,1 x2,y2 Z
      const { cx, cy, r = 60, startDeg = 0, endDeg = 90 } = el;
      const s = startDeg * Math.PI / 180;
      const e = endDeg   * Math.PI / 180;
      const x1 = cx + r * Math.cos(s), y1 = cy + r * Math.sin(s);
      const x2 = cx + r * Math.cos(e), y2 = cy + r * Math.sin(e);
      const large = Math.abs(endDeg - startDeg) > 180 ? 1 : 0;
      const node = document.createElementNS(_SVG_NS, 'path');
      node.setAttribute('d', `M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large},1 ${x2.toFixed(2)},${y2.toFixed(2)} Z`);
      node.setAttribute('stroke', el.stroke || '#334155');
      node.setAttribute('stroke-width', el.strokeWidth || 2);
      node.setAttribute('fill', el.fill || '#dbeafe');
      if (isNew) _applyAnim(node, 'anim-fade');
      svgEl.appendChild(node);
      break;
    }
    case 'side_label': {
      // Label auto-positioned perpendicular to a segment, pushed away from an interior reference point.
      // el.p1, el.p2: segment endpoints  el.awayFrom: any interior point (e.g. centroid)
      // el.offset (default 18): px distance from segment midpoint
      const [slx1, sly1] = el.p1 || [0, 0];
      const [slx2, sly2] = el.p2 || [0, 0];
      const smx = (slx1 + slx2) / 2, smy = (sly1 + sly2) / 2;
      const [ax, ay] = el.awayFrom || [smx, smy];
      let sdx = smx - ax, sdy = smy - ay;
      const sdlen = Math.hypot(sdx, sdy) || 1;
      sdx /= sdlen; sdy /= sdlen;
      // Auto-compute minimum offset so text doesn't overlap the segment.
      // Cap each axis contribution to avoid exploding offsets on diagonal push directions.
      // e.g. a diagonal push on a horizontal segment shouldn't require 60px just because
      // the horizontal component of the push direction is small.
      const _fs  = el.fontSize || 13;
      const _htw = (el.text || '').length * _fs * 0.55 / 2; // half text width
      const _hth = _fs * 0.5;                                // half text height
      const _minX = Math.abs(sdx) > 0.15 ? Math.min((_htw + 5) / Math.abs(sdx), _htw + 8) : 0;
      const _minY = Math.abs(sdy) > 0.15 ? Math.min((_hth + 4) / Math.abs(sdy), _hth + 6) : 0;
      const soff = Math.max(el.offset ?? 18, _minX, _minY);
      const slx = smx + sdx * soff, sly = smy + sdy * soff;
      const sNode = document.createElementNS(_SVG_NS, 'text');
      sNode.setAttribute('x', slx.toFixed(1));
      sNode.setAttribute('y', sly.toFixed(1));
      sNode.setAttribute('font-size', el.fontSize || 13);
      sNode.setAttribute('fill', el.color || '#1e293b');
      sNode.setAttribute('font-family', "Inter, 'Helvetica Neue', sans-serif");
      sNode.setAttribute('text-anchor', 'middle');
      sNode.setAttribute('dominant-baseline', 'central');
      if (el.bold) sNode.setAttribute('font-weight', '700');
      sNode.textContent = el.text || '';
      if (isNew) _applyAnim(sNode, 'anim-fade');
      svgEl.appendChild(sNode);
      break;
    }
    case 'text': {
      const rawText = el.text || '';
      // Auto-promote to katex overlay if text contains LaTeX markers
      const looksLikeLatex = /\\\(|\\\[|\\[a-zA-Z]{2,}|\^[{0-9]|_[{a-zA-Z0-9]/.test(rawText);
      if (looksLikeLatex) {
        // Strip outer \(...\) or \[...\] wrappers if present, then wrap correctly
        let formula = rawText.trim();
        if (formula.startsWith('\\(') && formula.endsWith('\\)'))
          formula = formula.slice(2, -2);
        else if (formula.startsWith('\\[') && formula.endsWith('\\]'))
          formula = formula.slice(2, -2);
        const div = document.createElement('div');
        div.className = 'anim-overlay-label' + (isNew ? ' anim-fade' : '');
        if (isNew && animDelay) div.style.animationDelay = `${animDelay}ms`;
        div.style.left     = (el.x / svgW * 100) + '%';
        div.style.top      = (el.y / svgH * 100) + '%';
        div.style.fontSize = (el.fontSize || 13) + 'px';
        div.style.color    = el.color || '#1e293b';
        if (window.katex) {
          try {
            div.innerHTML = window.katex.renderToString(formula,
              { throwOnError: false, displayMode: false });
          } catch(e) { div.textContent = formula; }
        } else {
          div.innerHTML = `\\(${formula}\\)`;
        }
        ovEl.appendChild(div);
      } else {
        const node = document.createElementNS(_SVG_NS, 'text');
        node.setAttribute('x', el.x); node.setAttribute('y', el.y);
        node.setAttribute('font-size', el.fontSize || 13);
        node.setAttribute('fill', el.color || '#1e293b');
        node.setAttribute('font-family', "Inter, 'Helvetica Neue', sans-serif");
        node.setAttribute('text-anchor', el.anchor || 'middle');
        node.setAttribute('dominant-baseline', 'central');
        if (el.bold) node.setAttribute('font-weight', '700');
        node.textContent = rawText;
        if (isNew) _applyAnim(node, 'anim-fade');
        svgEl.appendChild(node);
      }
      break;
    }
    case 'katex': {
      const div = document.createElement('div');
      div.className = 'anim-overlay-label' + (isNew ? ' anim-fade' : '');
      if (isNew && animDelay) div.style.animationDelay = `${animDelay}ms`;
      div.style.left     = (el.x / svgW * 100) + '%';
      div.style.top      = (el.y / svgH * 100) + '%';
      div.style.fontSize = (el.fontSize || 13) + 'px';
      div.style.color    = el.color || '#1e293b';
      // Render synchronously with katex.renderToString if available,
      // else fall back to delimiter syntax for later renderMathInElement pass
      if (window.katex) {
        try {
          div.innerHTML = window.katex.renderToString(el.formula,
            { throwOnError: false, displayMode: false });
        } catch(e) {
          div.textContent = el.formula;
        }
      } else {
        div.innerHTML = `\\(${el.formula}\\)`;
      }
      ovEl.appendChild(div);
      break;
    }
  }
}
