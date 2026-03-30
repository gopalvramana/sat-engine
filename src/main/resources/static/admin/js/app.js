// ═══════════════════════════════════════════════════════════════════
// app.js — SAT Question Validation Site
// Handles both index.html (question browser) and
// question.html (single question view)
// ═══════════════════════════════════════════════════════════════════

// ── Domain / Section label maps ───────────────────────────────────
const SECTION_LABELS = {
  math:            'Math',
  reading_writing: 'R&W'
};

const DOMAIN_LABELS = {
  algebra:              'Algebra',
  advanced_math:        'Advanced Math',
  geometry_trigonometry:'Geometry',
  problem_solving_data: 'Problem Solving',
  expression_ideas:     'Expression',
  standard_english:     'Standard English',
  craft_structure:      'Craft',
  information_ideas:    'Information'
};

function sectionLabel(s)  { return SECTION_LABELS[s] || s; }
function domainLabel(d)   { return DOMAIN_LABELS[d]  || d; }

// ── Difficulty helpers ────────────────────────────────────────────
function diffClass(d) {
  if (d <= 2) return 'easy';
  if (d <= 5) return 'medium';
  return 'hard';
}

function diffDots(difficulty) {
  const cls = diffClass(difficulty);
  let html = '<span class="flex gap-0.5 items-center">';
  for (let i = 1; i <= 7; i++) {
    const filled = i <= difficulty;
    const dotCls = filled ? `filled-${cls}` : 'empty';
    html += `<span class="diff-dot ${dotCls}"></span>`;
  }
  html += '</span>';
  return html;
}

// ── Text processing (fix double-escaped \n and Markdown tables) ──
function markdownTableToHTML(lines) {
  const parseRow = line => line.split('|').slice(1, -1).map(c => c.trim());
  const headers  = parseRow(lines[0]);
  // lines[1] is the separator row (|---|---|...) — skip it
  const dataRows = lines.slice(2).filter(l => /^\|/.test(l.trim())).map(parseRow);
  const thead = `<thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead>`;
  const tbody = `<tbody>${dataRows.map(row =>
    `<tr>${row.map(c => `<td>${c}</td>`).join('')}</tr>`
  ).join('')}</tbody>`;
  return `<table class="md-table">${thead}${tbody}</table>`;
}

function processQuestionText(raw) {
  if (!raw) return '';
  // Fix literal \n (backslash + n) stored by AI generator → real newline.
  // Use negative lookahead (?![a-zA-Z]) so LaTeX commands like \neq, \nabla,
  // \notin are NOT touched — only standalone \n line-break markers are replaced.
  let text = raw.replace(/\\n(?![a-zA-Z])/g, '\n');
  // Split on blank lines into paragraph blocks
  const blocks = text.split(/\n{2,}/);
  const parts = blocks.map(block => {
    const lines = block.split('\n').filter(l => l.trim() !== '');
    if (!lines.length) return '';
    // Detect Markdown table: first line has pipes, second is separator
    if (
      lines.length >= 2 &&
      /^\|/.test(lines[0].trim()) &&
      /^\|[\s\-:|]+\|/.test(lines[1].trim())
    ) {
      return markdownTableToHTML(lines);
    }
    return lines.join('<br>');
  });
  return parts.filter(p => p).join('<br><br>');
}

// ── Load all approved questions across all batches ────────────────
async function loadQuestions() {
  const v = Date.now();
  const idx = await fetch(`data/batches/index.json?v=${v}`).then(r => {
    if (!r.ok) throw new Error(`Failed to load index: ${r.status}`);
    return r.json();
  });

  const batches = await Promise.all(
    idx.map(b => fetch(`${b.path}?v=${v}`).then(r => r.ok ? r.json() : []))
  );

  // Flatten all batches, deduplicate by externalId (latest batch wins)
  const seen = new Set();
  const all = [];
  for (const batch of batches) {
    const qs = Array.isArray(batch) ? batch : (batch.questions || []);
    for (const q of qs) {
      if (!seen.has(q.externalId)) {
        seen.add(q.externalId);
        all.push(q);
      }
    }
  }
  return all;
}

// ═══════════════════════════════════════════════════════════════════
// INDEX PAGE
// ═══════════════════════════════════════════════════════════════════

function initIndexPage() {
  let allQuestions = [];

  // Filter state
  const filters = {
    section:    'all',
    domain:     'all',
    difficulty: 'all',
    type:       'all',
    diagram:    'all',
    reviewed:   'passed',  // default: show only approved questions
    pool:       'all'
  };

  // ── Wire filter buttons ─────────────────────────────────────────
  function bindFilterGroup(groupAttr, stateKey) {
    document.querySelectorAll(`[data-filter="${groupAttr}"]`).forEach(btn => {
      btn.addEventListener('click', () => {
        filters[stateKey] = btn.dataset.value;
        document.querySelectorAll(`[data-filter="${groupAttr}"]`)
          .forEach(b => b.classList.toggle('active', b === btn));
        applyFilters();
      });
    });
  }

  bindFilterGroup('section',    'section');
  bindFilterGroup('domain',     'domain');
  bindFilterGroup('difficulty', 'difficulty');
  bindFilterGroup('type',       'type');
  bindFilterGroup('diagram',    'diagram');
  bindFilterGroup('reviewed',   'reviewed');
  bindFilterGroup('pool',       'pool');

  // ── Apply filters ───────────────────────────────────────────────
  function applyFilters() {
    const filtered = allQuestions.filter(q => {
      if (filters.section    !== 'all' && q.section       !== filters.section)    return false;
      if (filters.domain     !== 'all' && q.domain        !== filters.domain)     return false;
      if (filters.difficulty !== 'all' && String(q.difficulty) !== filters.difficulty) return false;
      if (filters.type       !== 'all' && q.questionType  !== filters.type)       return false;
      if (filters.diagram === 'has'  && !q.diagram)  return false;
      if (filters.diagram === 'none' &&  q.diagram)  return false;
      if (filters.reviewed === 'passed'  && !q.reviewed) return false;
      if (filters.reviewed === 'pending' &&  q.reviewed) return false;
      if (filters.pool !== 'all' && q.pool !== filters.pool) return false;
      return true;
    });

    renderCards(filtered);
    updateStats(filtered, allQuestions);
  }

  // ── Stats bar ───────────────────────────────────────────────────
  function updateStats(filtered, all) {
    const math   = filtered.filter(q => q.section === 'math').length;
    const rw     = filtered.filter(q => q.section === 'reading_writing').length;
    const easy   = filtered.filter(q => q.difficulty <= 2).length;
    const medium = filtered.filter(q => q.difficulty >= 3 && q.difficulty <= 5).length;
    const hard   = filtered.filter(q => q.difficulty >= 6).length;
    const diags  = filtered.filter(q => q.diagram).length;

    const el = document.getElementById('stats-bar');
    if (!el) return;
    el.innerHTML = `
      <span class="font-semibold text-slate-700">Showing: ${filtered.length}</span>
      <span class="text-slate-400">·</span>
      <span>Math: <strong>${math}</strong></span>
      <span>R&W: <strong>${rw}</strong></span>
      <span class="text-slate-400">·</span>
      <span class="text-green-600">Easy: <strong>${easy}</strong></span>
      <span class="text-amber-600">Medium: <strong>${medium}</strong></span>
      <span class="text-red-600">Hard: <strong>${hard}</strong></span>
      <span class="text-slate-400">·</span>
      <span>Diagrams: <strong>${diags}</strong></span>
    `;
  }

  // ── Render question cards ───────────────────────────────────────
  function renderCards(questions) {
    const list = document.getElementById('question-list');
    if (!list) return;

    if (questions.length === 0) {
      list.innerHTML = `
        <div class="empty-state col-span-full">
          <div class="empty-icon">🔍</div>
          <div class="empty-text">No questions match the selected filters.</div>
        </div>`;
      return;
    }

    list.innerHTML = questions.map(q => {
      const secLbl  = sectionLabel(q.section);
      const domLbl  = domainLabel(q.domain);
      const cls     = diffClass(q.difficulty);
      const stem    = (q.questionStem || '').slice(0, 130);
      const hasDiag = q.diagram ? 'Has diagram' : 'No diagram';
      const typeStr = q.questionType?.toUpperCase() || 'MCQ';
      const revBadge = q.reviewed
        ? '<span class="badge-reviewed">✓ Reviewed</span>'
        : '<span class="badge-pending">Pending</span>';

      return `
        <div class="question-card-item">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
              ${q.externalId}
            </span>
            <span class="text-xs text-slate-500">${secLbl} · ${domLbl}</span>
            ${revBadge}
          </div>

          <div class="flex items-center gap-2 flex-wrap text-xs text-slate-500">
            <span class="diff-${cls} px-2 py-0.5 rounded-full text-xs font-semibold">
              Difficulty ${q.difficulty}
            </span>
            ${diffDots(q.difficulty)}
            <span>${typeStr}</span>
            <span class="text-slate-400">·</span>
            <span>${hasDiag}</span>
          </div>

          <div class="question-stem text-sm text-slate-600 mt-1 stem-preview">
            ${stem}${q.questionStem?.length > 130 ? '…' : ''}
          </div>

          <div class="flex justify-end mt-2">
            <a href="question.html?id=${encodeURIComponent(q.externalId)}"
               class="nav-btn is-primary text-sm">
              View Question →
            </a>
          </div>
        </div>`;
    }).join('');

    // Render KaTeX in stem previews
    list.querySelectorAll('.stem-preview').forEach(el => renderKaTeXIn(el));
  }

  // ── Boot ────────────────────────────────────────────────────────
  // Activate the default 'passed' filter button visually
  document.querySelectorAll('[data-filter="reviewed"]').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.value === 'passed');
  });

  loadQuestions()
    .then(qs => {
      allQuestions = qs;

      const approved = qs.filter(q => q.reviewed).length;
      const subtitle = document.getElementById('question-count');
      if (subtitle) subtitle.textContent = `${approved} approved · ${qs.length} total`;

      applyFilters();
    })
    .catch(err => {
      const list = document.getElementById('question-list');
      if (list) list.innerHTML = `
        <div class="empty-state col-span-full">
          <div class="empty-icon">⚠️</div>
          <div class="empty-text">Could not load questions: ${err.message}</div>
        </div>`;
    });
}


// ═══════════════════════════════════════════════════════════════════
// QUESTION PAGE
// ═══════════════════════════════════════════════════════════════════

function initQuestionPage() {
  const params  = new URLSearchParams(window.location.search);
  const targetId = params.get('id');

  let allQuestions  = [];
  let currentIndex  = 0;
  let activeChartId = null;

  // ── Navigate to question by index ──────────────────────────────
  function navigateTo(index) {
    if (index < 0 || index >= allQuestions.length) return;
    currentIndex = index;
    const q = allQuestions[index];

    // Update URL without reload
    const newUrl = `question.html?id=${encodeURIComponent(q.externalId)}`;
    history.replaceState(null, '', newUrl);

    renderQuestion(q);
    updateNavButtons();
  }

  function updateNavButtons() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    if (prevBtn) prevBtn.disabled = currentIndex === 0;
    if (nextBtn) nextBtn.disabled = currentIndex === allQuestions.length - 1;

    const counter = document.getElementById('q-counter');
    if (counter) counter.textContent = `${currentIndex + 1} / ${allQuestions.length}`;
  }

  // ── Destroy any active Chart.js instance ───────────────────────
  function destroyActiveChart() {
    if (!activeChartId) return;
    const existing = typeof Chart !== 'undefined' && Chart.getChart(activeChartId);
    if (existing) existing.destroy();
    activeChartId = null;
  }

  // ── Render a single question ────────────────────────────────────
  function renderQuestion(q) {
    destroyActiveChart();

    const container = document.getElementById('question-container');
    if (!container) return;

    const secLbl  = sectionLabel(q.section);
    const domLbl  = domainLabel(q.domain);
    const cls     = diffClass(q.difficulty);
    const isMCQ   = q.questionType !== 'spr';

    // Build choices HTML
    let choicesHtml = '';
    if (isMCQ) {
      const opts = [
        { letter: 'A', text: q.optionA },
        { letter: 'B', text: q.optionB },
        { letter: 'C', text: q.optionC },
        { letter: 'D', text: q.optionD }
      ].filter(o => o.text);

      choicesHtml = `<div class="flex flex-col gap-2 mt-4" id="choices">
        ${opts.map(o => `
          <label class="choice-label" data-letter="${o.letter}">
            <span class="choice-letter">${o.letter}</span>
            <span class="choice-text flex-1">${o.text}</span>
          </label>`).join('')}
      </div>`;
    } else {
      const hint = (q.sprMin != null && q.sprMax != null)
        ? `<span class="text-xs text-slate-400 ml-2">Range: ${q.sprMin} – ${q.sprMax}</span>`
        : '';
      choicesHtml = `<div class="mt-4 flex items-center gap-2">
        <input type="number" id="spr-answer" class="spr-input" placeholder="Enter answer" />
        ${hint}
      </div>`;
    }

    // Passage box
    const passageHtml = q.passageText
      ? `<div class="passage-box mb-4">${q.passageText}</div>`
      : '';

    // Diagram host
    const diagramHtml = q.diagram
      ? `<div class="diagram-host my-4" id="diagram-host"></div>`
      : '';

    // Validation panel
    const revBadge = q.reviewed
      ? '<span class="badge-reviewed">✓ Reviewed</span>'
      : '<span class="badge-pending">⏳ Pending Review</span>';

    const reviewNotesHtml = q.reviewNotes
      ? `<div class="validation-row">
           <span class="vkey">Notes:</span>
           <span class="vval italic">${q.reviewNotes}</span>
         </div>`
      : '';

    const genDate = q.generatedAt
      ? new Date(q.generatedAt).toLocaleString()
      : 'Unknown';

    container.innerHTML = `
      <!-- Meta header -->
      <div class="flex items-center gap-2 flex-wrap mb-4">
        <span class="diff-${cls} px-2.5 py-1 rounded-full text-xs font-bold">
          ${secLbl} · ${domLbl} · Difficulty ${q.difficulty}
        </span>
        <span class="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
          ${q.externalId}
        </span>
        <span class="text-xs text-slate-400">${q.questionType?.toUpperCase()}</span>
        ${q.diagram ? '<span class="text-xs text-blue-500 bg-blue-50 px-2 py-0.5 rounded">Has Diagram</span>' : ''}
      </div>

      <!-- Passage -->
      ${passageHtml}

      <!-- Diagram -->
      ${diagramHtml}

      <!-- Question stem -->
      <div class="question-stem mb-2" id="q-stem">${processQuestionText(q.questionStem)}</div>

      <!-- Choices / SPR -->
      ${choicesHtml}

      <!-- Check Answer button -->
      <div class="mt-4 flex items-center gap-3">
        <button class="check-btn" id="check-btn" ${isMCQ ? 'disabled' : ''}>
          Check Answer
        </button>
        <span id="answer-feedback" class="text-sm"></span>
      </div>

      <!-- Explanation (hidden until checked) -->
      <div id="explanation-panel" class="mt-4 hidden"></div>

      <!-- Divider -->
      <hr class="my-6 border-slate-200">

      <!-- Validation Panel -->
      <div class="validation-panel">
        <div class="panel-title">Validation Panel</div>
        <div class="flex items-center gap-2 mb-3">
          ${revBadge}
        </div>
        ${reviewNotesHtml}
        <div class="validation-row">
          <span class="vkey">External ID:</span>
          <span class="vval font-mono">${q.externalId}</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Section:</span>
          <span class="vval">${secLbl}</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Domain:</span>
          <span class="vval">${domLbl}</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Skill:</span>
          <span class="vval">${q.skill || '—'}</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Difficulty:</span>
          <span class="vval">${q.difficulty} / 7</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Type:</span>
          <span class="vval">${q.questionType?.toUpperCase()}</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Calculator OK:</span>
          <span class="vval">${q.calculatorOk ? 'Yes' : 'No'}</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Generated:</span>
          <span class="vval">${genDate}</span>
        </div>
        <div class="validation-row">
          <span class="vkey">Source:</span>
          <span class="vval">${q.source || 'ai_generated'}</span>
        </div>
      </div>

      <!-- Prev / Next -->
      <div class="flex items-center justify-between mt-6">
        <button id="prev-btn" class="nav-btn" ${currentIndex === 0 ? 'disabled' : ''}>
          ← Previous
        </button>
        <span id="q-counter" class="text-sm text-slate-500 font-mono">
          ${currentIndex + 1} / ${allQuestions.length}
        </span>
        <button id="next-btn" class="nav-btn is-primary" ${currentIndex === allQuestions.length - 1 ? 'disabled' : ''}>
          Next →
        </button>
      </div>
    `;

    // ── Render diagram ────────────────────────────────────────────
    if (q.diagram) {
      const host = document.getElementById('diagram-host');
      if (host) {
        renderDiagram(q.diagram, host);
        // Track canvas id for cleanup
        const canvas = host.querySelector('canvas');
        if (canvas) activeChartId = canvas.id;
      }
    }

    // ── KaTeX render ──────────────────────────────────────────────
    renderKaTeXIn(container);

    // ── Wire MCQ choice clicks ────────────────────────────────────
    if (isMCQ) {
      const checkBtn = document.getElementById('check-btn');
      document.querySelectorAll('.choice-label').forEach(label => {
        label.addEventListener('click', () => {
          if (label.classList.contains('is-locked')) return;
          document.querySelectorAll('.choice-label').forEach(l => {
            l.classList.remove('is-selected');
          });
          label.classList.add('is-selected');
          if (checkBtn) checkBtn.disabled = false;
        });
      });

      if (checkBtn) {
        checkBtn.addEventListener('click', () => {
          const selected = document.querySelector('.choice-label.is-selected');
          if (!selected) return;
          checkMCQ(q, selected);
        });
      }
    }

    // ── Wire SPR answer input ─────────────────────────────────────
    if (!isMCQ) {
      const input   = document.getElementById('spr-answer');
      const checkBtn = document.getElementById('check-btn');

      if (input) {
        input.addEventListener('input', () => {
          if (checkBtn) checkBtn.disabled = input.value.trim() === '';
        });
      }
      if (checkBtn) {
        checkBtn.addEventListener('click', () => checkSPR(q));
      }
    }

    // ── Wire Prev/Next ────────────────────────────────────────────
    document.getElementById('prev-btn')?.addEventListener('click', () => navigateTo(currentIndex - 1));
    document.getElementById('next-btn')?.addEventListener('click', () => navigateTo(currentIndex + 1));
  }

  // ── Check MCQ answer ───────────────────────────────────────────
  function checkMCQ(q, selectedLabel) {
    const selected = selectedLabel.dataset.letter;
    const correct  = q.correctAnswer?.toUpperCase();
    const isRight  = selected === correct;

    // Lock all labels
    document.querySelectorAll('.choice-label').forEach(l => {
      l.classList.add('is-locked');
      if (l.dataset.letter === correct) l.classList.add('is-correct');
    });
    if (!isRight) selectedLabel.classList.add('is-incorrect');

    // Disable check button
    const checkBtn = document.getElementById('check-btn');
    if (checkBtn) { checkBtn.disabled = true; checkBtn.textContent = isRight ? '✓ Correct!' : '✗ Incorrect'; }

    showExplanation(q, isRight);
  }

  // ── Check SPR answer ───────────────────────────────────────────
  function checkSPR(q) {
    const input = document.getElementById('spr-answer');
    if (!input) return;
    const val     = parseFloat(input.value);
    const correct = parseFloat(q.correctAnswer);
    const isRight = !isNaN(val) && !isNaN(correct) && Math.abs(val - correct) < 0.001;

    input.classList.add(isRight ? 'is-correct' : 'is-incorrect');
    input.disabled = true;

    const checkBtn = document.getElementById('check-btn');
    if (checkBtn) { checkBtn.disabled = true; checkBtn.textContent = isRight ? '✓ Correct!' : '✗ Incorrect'; }

    showExplanation(q, isRight);
  }

  // ── Show explanation panel ─────────────────────────────────────
  function showExplanation(q, isRight) {
    const panel = document.getElementById('explanation-panel');
    if (!panel) return;

    const statusIcon = isRight ? '✓ Correct' : '✗ Incorrect';
    const panelClass = isRight ? 'fb-correct' : 'fb-incorrect';

    panel.innerHTML = `
      <div class="feedback-panel ${panelClass}">
        <div class="feedback-status">${statusIcon}</div>
        <div class="explanation-body">${processQuestionText(q.explanation) || 'No explanation provided.'}</div>
      </div>`;
    panel.classList.remove('hidden');

    // KaTeX in explanation
    renderKaTeXIn(panel);
  }

  // ── Keyboard navigation ───────────────────────────────────────
  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') navigateTo(currentIndex + 1);
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   navigateTo(currentIndex - 1);
  });

  // ── Boot ────────────────────────────────────────────────────────
  loadQuestions()
    .then(qs => {
      allQuestions = qs;

      // Find target question index
      const idx = qs.findIndex(q => q.externalId === targetId);
      currentIndex = idx >= 0 ? idx : 0;

      if (qs.length === 0) {
        const container = document.getElementById('question-container');
        if (container) container.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">📭</div>
            <div class="empty-text">No questions loaded. Run merge_questions.py first.</div>
          </div>`;
        return;
      }

      if (idx < 0 && targetId) {
        const container = document.getElementById('question-container');
        if (container) container.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">Question "${targetId}" not found.</div>
          </div>`;
        return;
      }

      renderQuestion(allQuestions[currentIndex]);
      updateNavButtons();
    })
    .catch(err => {
      const container = document.getElementById('question-container');
      if (container) container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">⚠️</div>
          <div class="empty-text">Could not load questions: ${err.message}</div>
        </div>`;
    });
}


// ═══════════════════════════════════════════════════════════════════
// BOOT — detect which page we're on
// ═══════════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  const page = document.body.dataset.page;
  if (page === 'index')    initIndexPage();
  if (page === 'question') initQuestionPage();
});
