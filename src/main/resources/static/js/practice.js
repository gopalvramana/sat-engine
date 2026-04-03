/* ═══════════════════════════════════════════════════════════════
   practice.js — Student-facing practice session logic
   Stack: plain JS, renderer.js, KaTeX, Chart.js
   API:   GET /api/admin/questions  (prototype: uses admin endpoint)
═══════════════════════════════════════════════════════════════ */

'use strict';

/* ── State ───────────────────────────────────────────────────── */
const state = {
  allQuestions : [],   // all approved/enriched questions from API
  session      : [],   // sampled subset for this session
  idx          : 0,    // current question index (0-based)
  answers      : [],   // [{q, answer, correct}]
  phase        : 'question',  // 'question' | 'feedback'
  selected     : null, // currently selected MCQ letter
  section      : 'math',
  reviewIdx    : 0,    // current card index in review overlay
};

/* ── Initialisation ─────────────────────────────────────────── */
window.addEventListener('DOMContentLoaded', () => { init(); });

async function init() {
  try {
    const res = await fetch('/api/admin/questions?status=all');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    // Keep only questions that are ready for students
    state.allQuestions = data.filter(q =>
      q.status === 'approved' || q.status === 'enriched'
    );
    populateFilters();
    updatePoolInfo();
    el('btn-start').disabled = false;
  } catch (e) {
    el('pool-info').textContent = 'Could not load questions. Is the server running?';
    console.error(e);
  }
}

/* ── Filter population ──────────────────────────────────────── */
function populateFilters() {
  populateDomains();
}

function populateDomains() {
  const section = state.section;
  const domains = [...new Set(
    state.allQuestions
      .filter(q => q.section === section)
      .map(q => q.domain)
  )].sort();

  const sel = el('sel-domain');
  sel.innerHTML = '<option value="all">All domains</option>';
  domains.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = domainLabel(d);
    sel.appendChild(opt);
  });
}

function onDomainChange() {
  updatePoolInfo();
}

/* ── Section toggle ─────────────────────────────────────────── */
function setSection(section) {
  state.section = section;
  el('btn-math').classList.toggle('active', section === 'math');
  el('btn-rw').classList.toggle('active',   section === 'reading_writing');
  populateDomains();
  el('sel-domain').value = 'all';
  updatePoolInfo();
}

/* ── Pool info (how many questions match current filters) ─── */
function updatePoolInfo() {
  const pool = filteredPool();
  const count = parseInt(el('sel-count').value, 10) || 10;
  const available = pool.length;
  el('pool-info').textContent =
    available === 0
      ? 'No questions match these filters.'
      : `${available} question${available === 1 ? '' : 's'} available`;
  el('btn-start').disabled = available === 0;
}

function filteredPool() {
  const section    = state.section;
  const domain     = el('sel-domain').value;
  const difficulty = el('sel-difficulty').value;

  return state.allQuestions.filter(q => {
    if (q.section !== section) return false;
    if (domain !== 'all' && q.domain !== domain) return false;
    if (difficulty !== 'all' && String(q.difficulty) !== difficulty) return false;
    return true;
  });
}

/* ── Start session ──────────────────────────────────────────── */
function startSession() {
  const pool  = filteredPool();
  const count = Math.min(parseInt(el('sel-count').value, 10) || 10, pool.length);

  if (pool.length === 0) return;

  // Fisher-Yates shuffle then take count
  const shuffled = [...pool];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  state.session = shuffled.slice(0, count);
  state.idx     = 0;
  state.answers = [];

  showScreen('question');
  renderQuestion();
}

/* ── Render question ────────────────────────────────────────── */
function renderQuestion() {
  const q = state.session[state.idx];
  state.phase    = 'question';
  state.selected = null;

  // Header progress
  const num   = state.idx + 1;
  const total = state.session.length;
  el('progress-area').classList.remove('hidden');
  el('progress-label').textContent = `Question ${num} of ${total}`;
  el('progress-meta').textContent  = `${domainLabel(q.domain)} · Difficulty ${q.difficulty}`;
  el('progress-bar').style.width   = `${(num / total) * 100}%`;

  // Choose layout
  const isRW      = q.section === 'reading_writing' && q.passageText;
  const isMath    = !isRW;

  el('layout-math').classList.toggle('hidden', !isMath);
  el('layout-rw').classList.toggle('hidden',   !isRW);

  if (isMath) {
    el('math-stem').innerHTML   = processText(q.questionStem);
    el('math-diagram').innerHTML = '';
    if (q.diagram) renderDiagramSafe(q.diagram, el('math-diagram'));
  } else {
    el('rw-passage').innerHTML = processText(q.passageText);
    el('rw-stem').innerHTML    = processText(q.questionStem);
  }

  // Answer area
  const isMCQ = (q.questionType || '').toLowerCase() === 'mcq';
  el('mcq-choices').classList.toggle('hidden', !isMCQ);
  el('spr-input').classList.toggle('hidden',    isMCQ);
  el('spr-feedback').classList.add('hidden');

  if (isMCQ) {
    ['A','B','C','D'].forEach(letter => {
      const text = q[`option${letter}`] || '';
      el(`choice-text-${letter}`).innerHTML = processText(text);
      const item = el(`choice-${letter}`);
      item.className = 'choice-item';
      item.onclick   = () => selectChoice(letter);
      el(`choice-icon-${letter}`).classList.add('hidden');
    });
    el('btn-submit').disabled = true;
  } else {
    el('spr-field').value    = '';
    el('spr-field').disabled = false;
    el('btn-submit').disabled = true;
  }

  // Show submit bar, hide feedback
  el('submit-bar').classList.remove('hidden');
  el('feedback-panel').classList.add('hidden');

  // Re-render KaTeX on newly set content
  scheduleKaTeX([
    el('layout-math'), el('layout-rw'),
    el('mcq-choices'), el('spr-input')
  ]);
}

/* ── Choice selection ───────────────────────────────────────── */
function selectChoice(letter) {
  if (state.phase !== 'question') return;
  state.selected = letter;
  ['A','B','C','D'].forEach(l => {
    el(`choice-${l}`).classList.toggle('selected', l === letter);
  });
  el('btn-submit').disabled = false;
}

/* ── SPR input validation ───────────────────────────────────── */
function onSprInput() {
  const raw = el('spr-field').value.trim();
  el('btn-submit').disabled = parseSPR(raw) === null;
}

function parseSPR(raw) {
  if (!raw) return null;
  if (/^-?\d+(\.\d+)?$/.test(raw)) return parseFloat(raw);
  const fractionMatch = raw.match(/^(-?\d+)\s*\/\s*(-?\d+)$/);
  if (fractionMatch) {
    const num = parseInt(fractionMatch[1], 10);
    const den = parseInt(fractionMatch[2], 10);
    if (den === 0) return null;
    return num / den;
  }
  return null;
}

/* ── Submit answer ──────────────────────────────────────────── */
function submitAnswer() {
  const q = state.session[state.idx];
  state.phase = 'feedback';

  const isMCQ = (q.questionType || '').toLowerCase() === 'mcq';
  let correct, studentAnswer;

  if (isMCQ) {
    studentAnswer = state.selected;
    correct = studentAnswer === (q.correctAnswer || '').toUpperCase();
  } else {
    const raw = el('spr-field').value.trim();
    const val = parseSPR(raw);
    studentAnswer = raw;
    if (val === null) {
      correct = false;
    } else {
      const mn = q.sprMin != null ? parseFloat(q.sprMin) : null;
      const mx = q.sprMax != null ? parseFloat(q.sprMax) : null;
      const correctVal = parseFloat(q.correctAnswer);
      // Use range only if it's a genuine range (sprMin < sprMax)
      // sprMin=0, sprMax=0 means the pipeline didn't set them → fall back to correctAnswer
      if (mn !== null && mx !== null && mn < mx) {
        correct = val >= mn && val <= mx;
      } else if (!isNaN(correctVal)) {
        correct = val === correctVal;
      } else if (mn !== null && !isNaN(mn) && mn !== 0) {
        correct = val === mn;  // tight range: sprMin === sprMax
      } else {
        correct = false;
      }
    }
  }

  state.answers.push({ q, answer: studentAnswer, correct });

  // Lock choices and show results
  if (isMCQ) {
    highlightChoices(q, studentAnswer);
  } else {
    showSPRFeedback(q, studentAnswer, correct);
  }

  // Show feedback panel
  el('submit-bar').classList.add('hidden');
  el('feedback-panel').classList.remove('hidden');
  el('feedback-panel').innerHTML = buildFeedbackPanel(q, correct);
}

/* ── MCQ choice highlighting ────────────────────────────────── */
function highlightChoices(q, chosen) {
  const correct = (q.correctAnswer || '').toUpperCase();
  ['A','B','C','D'].forEach(l => {
    const item = el(`choice-${l}`);
    item.onclick = null; // disable clicks
    if (l === correct) {
      item.className = 'choice-item correct';
      el(`choice-icon-${l}`).textContent = '✓';
      el(`choice-icon-${l}`).classList.remove('hidden');
    } else if (l === chosen && l !== correct) {
      item.className = 'choice-item wrong';
      el(`choice-icon-${l}`).textContent = '✗';
      el(`choice-icon-${l}`).classList.remove('hidden');
    } else {
      item.className = 'choice-item neutral';
    }
  });
}

/* ── SPR feedback ───────────────────────────────────────────── */
function showSPRFeedback(q, raw, correct) {
  const box = el('spr-feedback');
  box.classList.remove('hidden');
  // Prefer numeric correctAnswer; fall back to sprMin if it's non-zero
  const mn = q.sprMin != null ? parseFloat(q.sprMin) : null;
  const mx = q.sprMax != null ? parseFloat(q.sprMax) : null;
  let correctDisplay;
  if (q.correctAnswer && !isNaN(parseFloat(q.correctAnswer))) {
    correctDisplay = (mn !== null && mx !== null && mn < mx)
      ? `${mn}–${mx}`   // genuine range (e.g. 75–82)
      : q.correctAnswer; // exact answer
  } else if (mn !== null && !isNaN(mn)) {
    correctDisplay = String(mn);
  } else {
    correctDisplay = '?';
  }
  if (correct) {
    box.className = 'spr-feedback-box correct';
    box.textContent = `✓  Your answer: ${raw} — Correct!`;
  } else {
    box.className = 'spr-feedback-box wrong';
    box.textContent = `✗  Your answer: ${raw} — Correct answer: ${correctDisplay}`;
  }
  el('spr-field').disabled = true;
}

/* ── Feedback panel HTML ────────────────────────────────────── */
function buildFeedbackPanel(q, correct) {
  const bannerClass = correct ? 'correct' : 'incorrect';
  const bannerText  = correct ? '✓  Correct!' : '✗  Incorrect — you\'ll see the explanation in the review';
  const isLast = state.idx + 1 >= state.session.length;

  return `
    <div class="feedback-banner ${bannerClass} mb-4">${bannerText}</div>
    <div class="flex justify-end">
      <button onclick="nextQuestion()"
              class="px-6 py-2.5 rounded-xl font-semibold text-sm bg-slate-800 text-white hover:bg-slate-900 transition-all">
        ${isLast ? 'See Results →' : 'Next Question →'}
      </button>
    </div>
  `;
}

/* ── Step navigator builder ─────────────────────────────────── */
function buildStepNavigator(navId, steps, renderFn) {
  if (!steps || steps.length === 0) {
    return '<p class="accordion-empty">No steps available.</p>';
  }

  const stepsHtml = steps.map((s, i) => `
    <div class="step-card ${i > 0 ? 'hidden' : ''}" data-step="${i}">
      ${steps.length > 1 ? `<div class="step-number">Step ${i + 1} of ${steps.length}</div>` : ''}
      ${renderFn(s, i)}
    </div>
  `).join('');

  const dotsHtml = steps.map((_, i) =>
    `<span class="step-dot ${i === 0 ? 'active' : ''}"></span>`
  ).join('');

  const footer = steps.length > 1 ? `
    <div class="step-nav-footer">
      <button class="step-nav-btn" onclick="stepNav('${navId}', -1)" disabled>← Prev</button>
      <div class="step-nav-center">
        <div class="step-dots">${dotsHtml}</div>
        <span class="step-counter">1 of ${steps.length}</span>
      </div>
      <button class="step-nav-btn" onclick="stepNav('${navId}', 1)">Next →</button>
    </div>
  ` : '';

  return `
    <div class="step-navigator" data-nav-id="${navId}" data-current="0" data-total="${steps.length}">
      ${stepsHtml}
      ${footer}
    </div>
  `;
}

function stepNav(navId, dir) {
  const nav = document.querySelector(`[data-nav-id="${navId}"]`);
  if (!nav) return;

  const total   = parseInt(nav.dataset.total);
  const current = parseInt(nav.dataset.current);
  const next    = current + dir;
  if (next < 0 || next >= total) return;

  nav.querySelector(`[data-step="${current}"]`).classList.add('hidden');
  nav.querySelector(`[data-step="${next}"]`).classList.remove('hidden');

  nav.querySelectorAll('.step-dot').forEach((d, i) => d.classList.toggle('active', i === next));

  const counter = nav.querySelector('.step-counter');
  if (counter) counter.textContent = `${next + 1} of ${total}`;

  const btns = nav.querySelectorAll('.step-nav-btn');
  btns[0].disabled = next === 0;
  btns[1].disabled = next === total - 1;

  nav.dataset.current = next;
  scheduleKaTeX([nav.querySelector(`[data-step="${next}"]`)]);
}

/* ── Accordion builder ──────────────────────────────────────── */
function buildAccordion(q) {
  const items = [];

  // ── Tab 1: Prerequisites ─────────────────────────────────────
  let prereqs = [];
  try {
    if (q.prerequisites) {
      prereqs = Array.isArray(q.prerequisites)
        ? q.prerequisites
        : JSON.parse(q.prerequisites);
    }
  } catch (e) { prereqs = []; }

  if (prereqs.length > 0) {
    const navHtml = buildStepNavigator('snav-prereq', prereqs, (p) => `
      <div class="prereq-topic">${escHtml(p.topic || String(p))}</div>
      ${p.why ? `<p class="step-content">${processText(p.why)}</p>` : ''}
    `);
    items.push(`
      <details class="accordion-item">
        <summary class="accordion-summary">
          <span class="accordion-icon">🔑</span>
          <span class="accordion-label">Prerequisites</span>
          <span class="accordion-badge">${prereqs.length} topic${prereqs.length !== 1 ? 's' : ''}</span>
          <span class="accordion-chevron">▶</span>
        </summary>
        <div class="accordion-body">${navHtml}</div>
      </details>`);
  }

  // ── Tab 2: Solution ──────────────────────────────────────────
  let steps = [];
  try {
    if (q.explanationSteps) {
      steps = Array.isArray(q.explanationSteps)
        ? q.explanationSteps
        : JSON.parse(q.explanationSteps);
    }
  } catch (e) { steps = []; }

  let solutionBody;
  if (steps.length > 0) {
    solutionBody = buildStepNavigator('snav-sol', steps, (s) => `
      ${s.title   ? `<h3 class="step-title">${processText(s.title)}</h3>` : ''}
      ${s.content ? `<p class="step-content">${processText(s.content)}</p>` : ''}
      ${s.math    ? `<div class="step-math">\\[${s.math}\\]</div>` : ''}
    `);
  } else {
    solutionBody = `<div class="accordion-empty">${
      q.explanationShort ? processText(q.explanationShort) : 'Solution not available.'
    }</div>`;
  }

  items.push(`
    <details class="accordion-item" open>
      <summary class="accordion-summary">
        <span class="accordion-icon">📋</span>
        <span class="accordion-label">Solution</span>
        ${steps.length ? `<span class="accordion-badge">${steps.length} step${steps.length !== 1 ? 's' : ''}</span>` : ''}
        <span class="accordion-chevron">▶</span>
      </summary>
      <div class="accordion-body">${solutionBody}</div>
    </details>`);

  // ── Tab 3: Core Concept ──────────────────────────────────────
  let cc = null;
  try {
    if (q.coreConcept) {
      cc = typeof q.coreConcept === 'object' ? q.coreConcept : JSON.parse(q.coreConcept);
    }
  } catch (e) { cc = null; }

  if (cc) {
    items.push(`
      <details class="accordion-item">
        <summary class="accordion-summary">
          <span class="accordion-icon">💡</span>
          <span class="accordion-label">Core Concept</span>
          <span class="accordion-badge accordion-badge-concept">${escHtml(cc.title || '')}</span>
          <span class="accordion-chevron">▶</span>
        </summary>
        <div class="accordion-body">
          <div class="step-card-single">
            ${cc.title   ? `<div class="concept-title-text">${escHtml(cc.title)}</div>` : ''}
            ${cc.summary ? `<p class="step-content">${processText(cc.summary)}</p>` : ''}
            ${cc.keyFormula ? `<div class="step-math">\\(${cc.keyFormula}\\)</div>` : ''}
          </div>
        </div>
      </details>`);
  }

  // ── Tab 4: Alternative Approach (Math only) ──────────────────
  if (q.section === 'math') {
    let alt = null;
    try {
      if (q.alternativeApproach) {
        alt = typeof q.alternativeApproach === 'object'
          ? q.alternativeApproach
          : JSON.parse(q.alternativeApproach);
      }
    } catch (e) { alt = null; }

    if (alt) {
      let altSteps = [];
      try { altSteps = Array.isArray(alt.steps) ? alt.steps : []; } catch (e) { altSteps = []; }

      const altBody = altSteps.length > 0
        ? buildStepNavigator('snav-alt', altSteps, (s) => `
            ${s.title   ? `<h3 class="step-title" style="color:#0369a1">${processText(s.title)}</h3>` : ''}
            ${s.content ? `<p class="step-content">${processText(s.content)}</p>` : ''}
          `)
        : '<p class="accordion-empty">No steps available.</p>';

      items.push(`
        <details class="accordion-item">
          <summary class="accordion-summary">
            <span class="accordion-icon">&#8644;</span>
            <span class="accordion-label">Alternative Approach</span>
            <span class="accordion-badge accordion-badge-alt">${processText(alt.title || '')}</span>
            <span class="accordion-chevron">▶</span>
          </summary>
          <div class="accordion-body">${altBody}</div>
        </details>`);
    }
  }

  return items.join('');
}

/* ── Accordion mutual-exclusion wiring ──────────────────────── */
function initAccordion() {
  const group = document.getElementById('feedback-accordion');
  if (!group) return;
  const items = Array.from(group.querySelectorAll('details.accordion-item'));
  items.forEach(item => {
    item.addEventListener('toggle', () => {
      if (item.open) {
        items.forEach(other => { if (other !== item) other.open = false; });
      }
    });
  });
}

/* ── Next question / end session ────────────────────────────── */
function nextQuestion() {
  state.idx++;
  if (state.idx < state.session.length) {
    renderQuestion();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    showSummary();
  }
}

/* ── Summary ────────────────────────────────────────────────── */
function showSummary() {
  showScreen('summary');
  el('progress-area').classList.add('hidden');

  const total   = state.answers.length;
  const correct = state.answers.filter(a => a.correct).length;
  const pct     = total > 0 ? Math.round((correct / total) * 100) : 0;

  el('summary-subtitle').textContent =
    `${correct} correct out of ${total} questions`;
  el('summary-fraction').textContent = `${correct} / ${total}`;
  el('summary-pct').textContent      = `${pct}%`;

  const bar = el('summary-bar');
  bar.style.width      = '0%';
  bar.style.background = pct >= 80 ? '#22c55e' : pct >= 60 ? '#f59e0b' : '#ef4444';
  setTimeout(() => { bar.style.width = `${pct}%`; }, 50);

  // Domain breakdown
  const byDomain = {};
  state.answers.forEach(({ q, correct }) => {
    const d = q.domain;
    if (!byDomain[d]) byDomain[d] = { correct: 0, total: 0 };
    byDomain[d].total++;
    if (correct) byDomain[d].correct++;
  });

  const domainsEl = el('summary-domains');
  domainsEl.innerHTML = '';
  Object.entries(byDomain).sort().forEach(([domain, stats]) => {
    const p = Math.round((stats.correct / stats.total) * 100);
    const color = p >= 80 ? '#22c55e' : p >= 60 ? '#f59e0b' : '#ef4444';
    const label = p >= 80 ? '✓ Good' : p >= 50 ? 'Needs work' : 'Focus here';

    const row = document.createElement('div');
    row.className = 'domain-row';
    row.innerHTML = `
      <div class="domain-row-header">
        <span class="font-medium text-slate-700">${domainLabel(domain)}</span>
        <span class="text-slate-500 text-xs">${stats.correct}/${stats.total} &nbsp;·&nbsp; ${p}% &nbsp;
          <span style="color:${color}">${label}</span>
        </span>
      </div>
      <div class="domain-row-bar-bg">
        <div class="domain-row-bar" data-w="${p}" style="width:0%; background:${color}"></div>
      </div>`;
    domainsEl.appendChild(row);
  });

  // Animate bars
  setTimeout(() => {
    domainsEl.querySelectorAll('.domain-row-bar').forEach(b => {
      b.style.width = b.dataset.w + '%';
    });
  }, 100);
}

/* ── Practice again ─────────────────────────────────────────── */
function practiceAgain() {
  // Reset state; keep filters
  state.session = [];
  state.answers = [];
  state.idx     = 0;
  showScreen('setup');
  el('progress-area').classList.add('hidden');
  updatePoolInfo();
}

/* ── Review answers overlay ─────────────────────────────────── */
function reviewAnswers() {
  state.reviewIdx = 0;
  el('review-overlay').classList.remove('hidden');
  renderReviewCard(0);
}

function renderReviewCard(idx) {
  const total   = state.answers.length;
  const { q, answer, correct } = state.answers[idx];
  const isMCQ = (q.questionType || '').toLowerCase() === 'mcq';

  // Counter
  el('review-counter').textContent = `Q ${idx + 1} of ${total}`;

  // Dots
  const dotsEl = el('review-dots');
  dotsEl.innerHTML = '';
  for (let i = 0; i < total; i++) {
    const dot = document.createElement('div');
    const ans = state.answers[i];
    const isActive = i === idx;
    dot.className = [
      'w-2 h-2 rounded-full transition-all cursor-pointer',
      ans.correct ? 'bg-green-400' : 'bg-red-400',
      isActive ? 'scale-125 ring-2 ring-white/60' : 'opacity-50',
    ].join(' ');
    dot.onclick = () => { state.reviewIdx = i; renderReviewCard(i); };
    dotsEl.appendChild(dot);
  }

  // Nav buttons
  el('review-prev').disabled = idx === 0;
  el('review-next').disabled = idx === total - 1;

  // Build card HTML
  const mn = q.sprMin != null ? parseFloat(q.sprMin) : null;
  const mx = q.sprMax != null ? parseFloat(q.sprMax) : null;
  const correctDisplay = isMCQ
    ? (q.correctAnswer || '').toUpperCase()
    : (q.correctAnswer && !isNaN(parseFloat(q.correctAnswer))
        ? (mn !== null && mx !== null && mn < mx ? `${mn}–${mx}` : q.correctAnswer)
        : (mn !== null && mn !== 0 ? String(mn) : '?'));

  const accordionHtml = buildAccordion(q);

  const card = document.createElement('div');
  card.className = `review-card ${correct ? 'review-correct' : 'review-wrong'}`;
  card.innerHTML = `
    <div class="flex items-center gap-2 mb-3">
      <span class="text-xs font-semibold px-2 py-0.5 rounded-full ${correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
        ${correct ? '✓ Correct' : '✗ Incorrect'}
      </span>
      <span class="text-xs text-slate-400">Q${idx+1} · ${domainLabel(q.domain)} · Difficulty ${q.difficulty}</span>
    </div>
    <div class="question-stem text-sm mb-3">${processText(q.questionStem)}</div>
    ${isMCQ ? buildReviewChoices(q, answer) : `
      <p class="text-sm mb-3">
        Your answer: <strong>${answer}</strong>
        ${!correct ? `&nbsp;·&nbsp; Correct: <strong>${correctDisplay}</strong>` : ''}
      </p>`}
    ${q.explanationShort ? `<p class="text-sm text-slate-500 mt-3 mb-4 leading-relaxed">${processText(q.explanationShort)}</p>` : ''}
    ${accordionHtml ? `<div class="accordion-group mt-3">${accordionHtml}</div>` : ''}
  `;

  const container = el('review-card-container');
  container.innerHTML = '';
  container.appendChild(card);

  // Wire accordion mutual-exclusion
  card.querySelectorAll('.accordion-group').forEach(group => {
    const items = Array.from(group.querySelectorAll('details.accordion-item'));
    items.forEach(item => {
      item.addEventListener('toggle', () => {
        if (item.open) items.forEach(o => { if (o !== item) o.open = false; });
      });
    });
  });

  scheduleKaTeX([card]);
  // Scroll overlay back to top on card change
  el('review-overlay').scrollTop = 0;
}

function reviewNav(dir) {
  const next = state.reviewIdx + dir;
  if (next < 0 || next >= state.answers.length) return;
  state.reviewIdx = next;
  renderReviewCard(next);
}

function buildReviewChoices(q, chosen) {
  return ['A','B','C','D'].map(l => {
    const text = q[`option${l}`] || '';
    const correct   = l === (q.correctAnswer || '').toUpperCase();
    const wasChosen = l === chosen;
    let cls = '';
    if (correct)             cls = 'text-green-700 font-semibold';
    else if (wasChosen)      cls = 'text-red-600 line-through opacity-70';
    else                     cls = 'text-slate-400';
    const icon = correct ? ' ✓' : (wasChosen && !correct ? ' ✗' : '');
    return `<div class="text-xs ${cls} py-0.5">
      <span class="font-bold">${l}.</span> ${processText(text)}${icon}
    </div>`;
  }).join('');
}

function closeReview() {
  el('review-overlay').classList.add('hidden');
}

/* ── Screen switcher ────────────────────────────────────────── */
function showScreen(name) {
  el('screen-setup').classList.toggle('hidden',    name !== 'setup');
  el('screen-question').classList.toggle('hidden', name !== 'question');
  el('screen-summary').classList.toggle('hidden',  name !== 'summary');
}

/* ── Diagram rendering (safe wrapper) ──────────────────────── */
function renderDiagramSafe(diagram, host) {
  if (!diagram || !host) return;
  try {
    // diagram may already be an object (JsonRawValue) or a JSON string
    const cfg = typeof diagram === 'string' ? JSON.parse(diagram) : diagram;
    if (window.renderDiagram) {
      renderDiagram(cfg, host);
    }
  } catch (e) {
    console.warn('Diagram render error:', e);
  }
}

/* ── KaTeX rendering ────────────────────────────────────────── */
function scheduleKaTeX(elements) {
  const valid = elements.filter(Boolean);
  if (window.renderMathInElement) {
    valid.forEach(el => renderKaTeXIn(el));
  } else {
    // KaTeX not loaded yet — queue
    if (!window._pendingKatex) window._pendingKatex = [];
    window._pendingKatex.push(...valid);
  }
}

function renderKaTeXIn(el) {
  if (!el || !window.renderMathInElement) return;
  renderMathInElement(el, {
    delimiters: [
      // Only \(...\) and \[...\] — never $$ which collides with currency text
      { left: '\\(', right: '\\)', display: false },
      { left: '\\[', right: '\\]', display: true  },
    ],
    throwOnError: false
  });
}

/* ── Text processing (matches validate2.js) ─────────────────── */
function processText(text) {
  if (!text) return '';
  const raw = String(text);
  // Also matches $...$ LaTeX math (when $ is NOT followed by a digit — that's currency).
  // Uses (?:[^$\\]|\\.)* to allow \$ (escaped dollar) inside, e.g. $\$165$.
  const mathRe = /(\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$(?!\d)(?:[^$\\]|\\.)*\$)/g;
  const segments = [];
  let last = 0, m;
  while ((m = mathRe.exec(raw)) !== null) {
    if (m.index > last) segments.push({ math: false, t: raw.slice(last, m.index) });
    segments.push({ math: true, t: m[0] });
    last = m.index + m[0].length;
  }
  if (last < raw.length) segments.push({ math: false, t: raw.slice(last) });

  return segments.map(seg => {
    if (seg.math) {
      // Convert $...$ → \(...\) since KaTeX no longer has $ as a delimiter
      let t = seg.t;
      if (t.charAt(0) === '$') t = '\\(' + t.slice(1, -1) + '\\)';
      return t
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/\\n(?![a-zA-Z]{2,})/g, ' ')
        .replace(/\n/g, ' ');
    }
    return seg.t
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/&lt;(\/?)table&gt;/gi, (_, a) => `<${a}table>`)
      .replace(/&lt;(\/?)thead&gt;/gi, (_, a) => `<${a}thead>`)
      .replace(/&lt;(\/?)tbody&gt;/gi, (_, a) => `<${a}tbody>`)
      .replace(/&lt;(\/?)tr&gt;/gi,    (_, a) => `<${a}tr>`)
      .replace(/&lt;th&gt;/gi, '<th>').replace(/&lt;\/th&gt;/gi, '</th>')
      .replace(/&lt;td&gt;/gi, '<td>').replace(/&lt;\/td&gt;/gi, '</td>')
      .replace(/\\n/g, '<br>')
      .replace(/\n/g, '<br>')
      // Escape bare $ so KaTeX never mistakes currency for a math delimiter
      .replace(/\$/g, '&#36;')
      // Markdown bold/italic (Claude occasionally outputs these despite instructions)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*([^*\n]+)\*/g, '<em>$1</em>');
  }).join('');
}

/* ── Label helpers ──────────────────────────────────────────── */
function domainLabel(d) {
  const M = {
    algebra: 'Algebra', advanced_math: 'Adv Math',
    problem_solving_data: 'Problem Solving', geometry_trigonometry: 'Geometry',
    information_ideas: 'Info & Ideas', craft_structure: 'Craft & Structure',
    expression_ideas: 'Expression', standard_english: 'Standard English'
  };
  return M[d] || d || '?';
}

function skillLabel(s) {
  if (!s) return '?';
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function escHtml(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

/* ── DOM helper ─────────────────────────────────────────────── */
function el(id) { return document.getElementById(id); }
