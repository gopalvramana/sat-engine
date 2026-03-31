/* ═══════════════════════════════════════════════════════════════
   STATE
═══════════════════════════════════════════════════════════════ */
let allQuestions  = [];
let activeFilter  = 'all';
let activeSection = 'all';   // 'all' | 'math' | 'rw'
let activeDomain  = null;    // domain string or null = all
let searchQuery   = '';
let currentIdx    = 0;       // position within visibleQuestions()
let stepIdx       = 0;       // current explanation step
let activeTab     = 'explanation';

/* ═══════════════════════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════════════════════ */
function showToast(msg, isError = false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.background = isError ? '#dc2626' : '#1e293b';
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2400);
}

/* ═══════════════════════════════════════════════════════════════
   API
═══════════════════════════════════════════════════════════════ */
async function apiPatch(path, body) {
  const r = await fetch(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
}

/* ═══════════════════════════════════════════════════════════════
   STATS
═══════════════════════════════════════════════════════════════ */
function updateStats() {
  const total    = allQuestions.length;
  const pending  = allQuestions.filter(q => ['generated','reviewed','enriched'].includes(q.status)).length;
  const approved = allQuestions.filter(q => q.status === 'approved').length;
  const rejected = allQuestions.filter(q => q.status === 'rejected').length;

  document.getElementById('stat-total').textContent    = total;
  document.getElementById('stat-pending').textContent  = pending;
  document.getElementById('stat-approved').textContent = approved;
  document.getElementById('stat-rejected').textContent = rejected;

  const qb = document.getElementById('queue-badge');
  if (pending > 0) { qb.textContent = `${pending} pending`; qb.classList.remove('hidden'); }
  else             { qb.classList.add('hidden'); }

  document.getElementById('header-sub').textContent =
    `${total} questions · ${approved} approved · ${rejected} rejected`;
}

/* ═══════════════════════════════════════════════════════════════
   FILTER + VISIBLE LIST
═══════════════════════════════════════════════════════════════ */
function setFilter(filter, el) {
  activeFilter  = filter;
  activeDomain  = null;
  currentIdx    = 0;
  stepIdx       = 0;
  activeTab     = 'explanation';
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  buildSidebar();
  renderQuestion();
}

function statusFiltered() {
  return allQuestions.filter(q => {
    if (activeFilter === 'pending')  return ['generated','reviewed','enriched'].includes(q.status);
    if (activeFilter === 'approved') return q.status === 'approved';
    if (activeFilter === 'rejected') return q.status === 'rejected';
    return true;
  });
}

function visibleQuestions() {
  const sq = searchQuery.toLowerCase();
  return statusFiltered().filter(q => {
    if (activeSection === 'math') return q.section === 'math';
    if (activeSection === 'rw')   return q.section === 'reading_writing';
    return true;
  }).filter(q => {
    if (activeDomain) return q.domain === activeDomain;
    return true;
  }).filter(q => {
    if (!sq) return true;
    return (q.externalId    || '').toLowerCase().includes(sq)
        || (q.domain        || '').toLowerCase().includes(sq)
        || (q.questionStem  || '').toLowerCase().includes(sq);
  });
}

/* ═══════════════════════════════════════════════════════════════
   QUEUE FILTER HANDLERS
═══════════════════════════════════════════════════════════════ */
function setSection(s) {
  activeSection = s;
  activeDomain  = null;
  currentIdx    = 0;
  ['all','math','rw'].forEach(id => {
    document.getElementById(`sec-${id}`)?.classList.toggle('active', id === s);
  });
  buildSidebar();
  renderQuestion();
}

function setDomain(d) {
  activeDomain = (activeDomain === d) ? null : d;
  currentIdx   = 0;
  buildSidebar();
  renderQuestion();
}

function setSearch(val) {
  searchQuery  = val.trim();
  activeDomain = null;
  currentIdx   = 0;
  buildSidebar();
  renderQuestion();
}

/* ═══════════════════════════════════════════════════════════════
   SIDEBAR + NAVIGATION
═══════════════════════════════════════════════════════════════ */
function buildSidebar() {
  const base = statusFiltered().filter(q => {
    if (activeSection === 'math') return q.section === 'math';
    if (activeSection === 'rw')   return q.section === 'reading_writing';
    return true;
  });
  const counts = {};
  base.forEach(q => { counts[q.domain] = (counts[q.domain] || 0) + 1; });
  const domains = Object.keys(counts).sort();

  const domainEl = document.getElementById('domain-list');
  domainEl.innerHTML = domains.length
    ? domains.map(d => `
        <button class="domain-btn ${activeDomain === d ? 'active' : ''}"
                onclick="setDomain('${d}')">
          <span>${domainLabel(d)}</span>
          <span class="domain-count">${counts[d]}</span>
        </button>`).join('')
    : '';

  const list = visibleQuestions();
  const el   = document.getElementById('q-list');

  el.innerHTML = list.map((q, i) => {
    const dot = q.status === 'approved' ? '#22c55e'
              : q.status === 'rejected' ? '#ef4444' : '#f59e0b';
    const agentFail = q.agentReview && !q.agentReview.pass;
    return `<div class="q-list-item ${i === currentIdx ? 'active' : ''}"
                 onclick="jumpTo(${i})">
      <span class="q-status-dot" style="background:${dot}"></span>
      <span class="font-mono flex-1 truncate" style="font-size:0.72rem;">${q.externalId}</span>
      ${agentFail ? '<span style="color:#ef4444;font-size:0.6rem;flex-shrink:0;">●</span>' : ''}
    </div>`;
  }).join('') || '<div class="px-3 py-2 text-xs text-slate-400 italic">No matches.</div>';

  const counter = document.getElementById('nav-counter');
  counter.textContent = list.length ? `${currentIdx + 1} / ${list.length}` : '0 / 0';
  document.getElementById('btn-prev').disabled = currentIdx === 0;
  document.getElementById('btn-next').disabled = currentIdx >= list.length - 1;
}

function jumpTo(idx) {
  currentIdx = idx;
  stepIdx    = 0;
  activeTab  = 'explanation';
  buildSidebar();
  renderQuestion();
}

function navigate(dir) {
  const list = visibleQuestions();
  currentIdx = Math.max(0, Math.min(list.length - 1, currentIdx + dir));
  stepIdx    = 0;
  activeTab  = 'explanation';
  buildSidebar();
  renderQuestion();
}

/* ═══════════════════════════════════════════════════════════════
   TABS
═══════════════════════════════════════════════════════════════ */
function switchTab(name) {
  activeTab = name;
  document.querySelectorAll('.tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === name));
  document.querySelectorAll('.tab-pane').forEach(p =>
    p.classList.toggle('is-active', p.id === 'tab-' + name));
  renderKaTeXIn(document.getElementById('tab-' + name));
}

/* ═══════════════════════════════════════════════════════════════
   EXPLANATION STEP NAVIGATOR
═══════════════════════════════════════════════════════════════ */
function getSteps() {
  const q = visibleQuestions()[currentIdx];
  if (!q) return [];
  try {
    return typeof q.explanationSteps === 'string'
      ? JSON.parse(q.explanationSteps || '[]')
      : (q.explanationSteps || []);
  } catch (e) { return []; }
}

function setStep(idx) {
  const steps = getSteps();
  stepIdx = Math.max(0, Math.min(steps.length - 1, idx));
  renderExplanationTab(steps);
}

function renderExplanationTab(steps) {
  const el = document.getElementById('tab-explanation');
  if (!el) return;

  if (!steps || !steps.length) {
    const q = visibleQuestions()[currentIdx];
    el.innerHTML = q && q.explanationShort
      ? `<p class="text-sm text-slate-600 leading-relaxed">${processText(q.explanationShort)}</p>`
      : `<p class="text-sm text-slate-400 italic">No explanation available.</p>`;
    renderKaTeXIn(el);
    return;
  }

  const s     = steps[stepIdx];
  const total = steps.length;

  const dotsHtml = steps.map((_, i) => `
    <div onclick="setStep(${i})"
         class="step-dot"
         style="background:${i < stepIdx ? '#86efac' : i === stepIdx ? '#2563eb' : '#e2e8f0'};
                ${i === stepIdx ? 'transform:scale(1.5);box-shadow:0 0 0 3px #bfdbfe;' : ''}">
    </div>`).join('');

  el.innerHTML = `
    <div class="step-card mb-4">
      <div class="step-num">${stepIdx + 1}</div>
      <div class="step-title">${escHtml(s.title || '')}</div>
      <div class="step-desc">${processText(s.content || '')}</div>
      ${s.math ? `<div class="step-math">\\(${s.math}\\)</div>` : ''}
    </div>

    <div class="flex items-center justify-between">
      <button class="ctrl-btn flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold
                     bg-white text-slate-500 hover:bg-slate-50"
              style="border:1.5px solid #e2e8f0;"
              onclick="setStep(${stepIdx - 1})" ${stepIdx === 0 ? 'disabled' : ''}>
        ← Prev
      </button>

      <div class="flex flex-col items-center gap-1.5">
        <div class="flex items-center gap-1.5">${dotsHtml}</div>
        <p class="text-xs text-slate-400">Step ${stepIdx + 1} of ${total}</p>
      </div>

      <button class="ctrl-btn flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold
                     bg-blue-600 text-white hover:bg-blue-700"
              onclick="setStep(${stepIdx + 1})" ${stepIdx === total - 1 ? 'disabled' : ''}>
        Next →
      </button>
    </div>`;

  renderKaTeXIn(el);
}

/* ═══════════════════════════════════════════════════════════════
   MAIN RENDER
═══════════════════════════════════════════════════════════════ */
function renderQuestion() {
  const list = visibleQuestions();

  if (!list.length) {
    document.getElementById('question-area').innerHTML =
      `<div class="empty-panel"><div style="font-size:2.5rem">🎉</div>
       <p class="mt-3">Nothing here for this filter.</p></div>`;
    return;
  }

  const q = list[currentIdx];
  document.getElementById('question-area').innerHTML =
    `<div class="qv-body">${buildView(q)}</div>`;

  if (q.diagram) {
    const host = document.getElementById('diagram-host');
    if (host) renderDiagram(q.diagram, host);
  }

  renderExplanationTab(getSteps());
  renderKaTeXIn(document.getElementById('question-area'));
  wireEvents(q);
}

/* ═══════════════════════════════════════════════════════════════
   VIEW BUILDER
═══════════════════════════════════════════════════════════════ */
function buildView(q) {
  const diff   = q.difficulty || 1;
  const status = q.status;
  const isMCQ  = (q.questionType || 'mcq').toLowerCase() !== 'spr';
  const correct = (q.correctAnswer || '').toUpperCase();

  const dots = Array.from({ length: 7 }, (_, i) =>
    `<span class="diff-dot ${i < diff ? 'filled' : 'empty'}"></span>`
  ).join('');

  const topicLabel = `${sectionLabel(q.section)} · ${domainLabel(q.domain)}`;

  /* ── Answer choices ── */
  let choicesHtml = '';
  if (isMCQ) {
    const opts = [
      { l: 'A', t: q.optionA }, { l: 'B', t: q.optionB },
      { l: 'C', t: q.optionC }, { l: 'D', t: q.optionD }
    ].filter(o => o.t);
    choicesHtml = `<div class="flex flex-col gap-2 mt-4">${
      opts.map(o => `
        <div class="choice-label ${o.l === correct ? 'is-correct' : ''}">
          <span class="choice-letter">${o.l}</span>
          <span class="choice-text">${processText(o.t)}</span>
          ${o.l === correct
            ? `<svg class="ml-auto flex-shrink-0" width="17" height="17" viewBox="0 0 17 17" fill="none">
                 <circle cx="8.5" cy="8.5" r="8" fill="#22c55e"/>
                 <path d="M5 8.5l3 3 4.5-5.5" stroke="white" stroke-width="1.8"
                       stroke-linecap="round" stroke-linejoin="round"/>
               </svg>` : ''}
        </div>`).join('')
    }</div>`;
  } else {
    choicesHtml = `<div class="mt-4 flex items-center gap-3">
      <span class="text-sm text-slate-500 font-semibold">Answer:</span>
      <span class="font-mono text-green-700 font-bold text-base bg-green-50
                   border border-green-200 px-3 py-1 rounded-lg">${correct || '?'}</span>
      ${q.sprMin != null
        ? `<span class="text-xs text-slate-400">Range: ${q.sprMin} – ${q.sprMax}</span>` : ''}
    </div>`;
  }

  /* ── Agent verdict ── */
  let ar = q.agentReview;
  let verdictHtml = '';
  if (ar) {
    let issues = [];
    try { issues = typeof ar.issues === 'string' ? JSON.parse(ar.issues || '[]') : (ar.issues || []); }
    catch (e) { issues = []; }
    const crits    = issues.filter(i => i.severity === 'critical');
    const warns    = issues.filter(i => i.severity === 'warning');
    const solved   = (ar.solvedAnswer || '').toUpperCase();
    const mismatch = solved && /^[A-D]$/.test(solved) && solved !== correct;
    const conf     = ar.confidence != null ? Math.round(ar.confidence * 100) : null;

    if (ar.pass) {
      verdictHtml = `
        <div class="verdict-pass mb-3">
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                 style="background:#22c55e;">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                <path d="M2.5 6.5l3 3 5-6" stroke="white" stroke-width="2"
                      stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </div>
            <div>
              <p class="text-sm font-bold text-green-700">Agent passed</p>
              <p class="text-xs text-green-600">
                ${conf != null ? `Confidence: ${conf}%` : ''}
                ${solved ? ` · Solved: ${solved}` : ''}
                ${warns.length ? ` · ${warns.length} warning(s)` : ''}
              </p>
            </div>
          </div>
          ${warns.length ? `<div class="mt-2 space-y-0.5 pt-2 border-t border-green-200">
            ${warns.map(i => `<div class="issue-item">
              <span class="issue-chip warning">WARN</span>
              <span class="text-slate-600">[${i.check}] ${escHtml(i.detail || '')}</span>
            </div>`).join('')}
          </div>` : ''}
        </div>`;
    } else {
      const fixBtn = mismatch
        ? `<button class="btn-fix" id="btn-fix" data-answer="${solved}">Fix answer → ${solved}</button>` : '';
      verdictHtml = `
        <div class="verdict-fail mb-3">
          <div class="flex items-center gap-2.5 mb-2">
            <div class="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                 style="background:#ef4444;">
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                <path d="M2 2l7 7M9 2L2 9" stroke="white" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-sm font-bold text-red-700">Agent failed</p>
              <p class="text-xs text-red-500">
                ${conf != null ? `Confidence: ${conf}%` : ''}
                ${solved ? ` · Solved: ${solved}` : ''}
                ${crits.length ? ` · ${crits.length} critical` : ''}
              </p>
            </div>
            ${fixBtn}
          </div>
          ${issues.length ? `<div class="space-y-0.5 pt-2 border-t border-red-200">
            ${issues.map(i => `<div class="issue-item">
              <span class="issue-chip ${i.severity}">${i.severity}</span>
              <span class="text-slate-600 text-xs">[${i.check}] ${escHtml(i.detail || '')}</span>
            </div>`).join('')}
          </div>` : ''}
        </div>`;
    }
  }

  /* ── Section flag — R&W gets simplified right panel ── */
  const isMath = q.section === 'math';

  /* ── Trap panel (Math only) ── */
  let trapHtml = '';
  if (isMath && q.trapCategory) {
    const catLabel = q.trapCategory.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    trapHtml = `
      <div class="trap-panel mt-3 mb-3">
        <div class="flex items-start gap-2">
          <span style="font-size:1.15rem; flex-shrink:0;">⚠️</span>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <p class="text-sm font-bold text-amber-800">Trap Analysis</p>
              <span class="text-xs bg-amber-200 text-amber-800 font-semibold px-2 py-0.5 rounded-full">
                ${catLabel}
              </span>
            </div>
            <p class="text-sm text-amber-700 leading-relaxed">${processText(q.trapExplanation || '')}</p>
          </div>
        </div>
      </div>`;
  }

  /* ── Core Concept tab (Math only) ── */
  let conceptHtml = '';
  if (isMath) {
    let cc = {};
    try { cc = typeof q.coreConcept === 'string'
      ? (JSON.parse(q.coreConcept || 'null') || {}) : (q.coreConcept || {}); } catch (e) {}
    conceptHtml = cc.title ? `
      <div class="rounded-xl p-4 mb-4" style="background:#eff6ff; border:1.5px solid #bfdbfe;">
        <p class="text-sm font-bold text-blue-800 mb-2">${escHtml(cc.title)}</p>
        <p class="text-sm text-blue-700 leading-relaxed mb-3">${processText(cc.summary || '')}</p>
        ${cc.keyFormula
          ? `<div class="bg-white border border-blue-100 rounded-lg p-3 font-mono text-sm text-blue-900">
               \\(${cc.keyFormula}\\)
             </div>` : ''}
      </div>` : `<p class="text-sm text-slate-400 italic">No core concept data. Run enrich job.</p>`;
  }

  /* ── Prerequisites tab (Math only) ── */
  let prereqsHtml = '';
  if (isMath) {
    let prereqs = [];
    try { prereqs = typeof q.prerequisites === 'string'
      ? (JSON.parse(q.prerequisites || '[]') || []) : (q.prerequisites || []); } catch (e) {}
    prereqsHtml = prereqs.length
      ? prereqs.map(p => `
          <div class="prereq-card mb-3">
            <div style="width:9px;height:9px;border-radius:50%;background:#3b82f6;flex-shrink:0;margin-top:3px;"></div>
            <div>
              <p class="text-sm font-semibold text-slate-800">${escHtml(p.topic || '')}</p>
              <p class="text-xs text-slate-500 mt-0.5 leading-relaxed">${escHtml(p.why || '')}</p>
            </div>
          </div>`).join('')
      : `<p class="text-sm text-slate-400 italic">No prerequisites data. Run enrich job.</p>`;
  }

  /* ── Status badges ── */
  const statusBadge = status === 'approved'
    ? `<span class="text-xs font-bold px-2 py-0.5 rounded-full bg-green-100 text-green-700">✓ Approved</span>`
    : status === 'rejected'
      ? `<span class="text-xs font-bold px-2 py-0.5 rounded-full bg-red-100 text-red-600">✗ Rejected</span>`
      : `<span class="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Pending</span>`;

  const enrichBadge = isMath && !q.coreConcept && status === 'approved'
    ? `<span class="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded"
            title="Run: --job=enrich --include-approved">⚠ Needs enrich</span>` : '';

  const diagBadge = q.diagram
    ? `<span class="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
         ${(q.diagram.diagramType || q.diagram.type || '').includes('chart') ? 'Chart.js' : 'SVG'}
       </span>` : '';

  /* ── Pool buttons ── */
  const pool = q.pool || 'both';
  const poolBtns = ['test','practice','both'].map(p => `
    <button class="pool-btn ${pool === p ? 'active-' + p : ''}"
            data-pool="${p}" id="pool-${p}">
      ${p.charAt(0).toUpperCase() + p.slice(1)}
    </button>`).join('');

  /* ── Final HTML ── */
  return `
    <div class="qv-left">
      <div class="bg-white border border-slate-200 rounded-2xl p-5"
           style="box-shadow:0 2px 10px rgba(0,0,0,0.05);">

        <div class="flex items-center justify-between mb-3 flex-wrap gap-2">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold"
                  style="background:#eff6ff; border:1.5px solid #bfdbfe; color:#1d4ed8;">
              ${topicLabel}
            </span>
            <div class="flex items-center gap-0.5">${dots}</div>
            ${diagBadge}
          </div>
          <span class="text-xs bg-slate-100 text-slate-500 rounded-full px-2.5 py-0.5 font-medium">
            ${(q.questionType || 'MCQ').toUpperCase()}
          </span>
        </div>

        ${q.passageText ? `<div class="passage-box">${processText(q.passageText)}</div>` : ''}
        <p class="question-stem mb-1">${processText(q.questionStem)}</p>

        ${q.diagram
          ? `<div id="diagram-host" class="rounded-xl my-4 p-2"
                  style="background:#f8fbff; border:1px solid #e2e8f0; min-height:80px;"></div>` : ''}

        ${choicesHtml}

        <div class="flex items-center gap-2 mt-4 pt-3 border-t border-slate-100 flex-wrap">
          <span class="font-mono text-xs text-slate-400">${q.externalId}</span>
          ${statusBadge}
          ${enrichBadge}
        </div>
      </div>
    </div>

    <div class="qv-right">
      ${verdictHtml}

      <div class="bg-white border border-slate-200 rounded-2xl overflow-hidden mb-3"
           style="box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        ${isMath ? `
        <div class="border-b border-slate-200 px-1">
          <div class="flex overflow-x-auto">
            <button class="tab-btn ${activeTab === 'explanation' ? 'active' : ''}"
                    data-tab="explanation" onclick="switchTab('explanation')">Explanation</button>
            <button class="tab-btn ${activeTab === 'concept' ? 'active' : ''}"
                    data-tab="concept" onclick="switchTab('concept')">Core Concept</button>
            <button class="tab-btn ${activeTab === 'prereqs' ? 'active' : ''}"
                    data-tab="prereqs" onclick="switchTab('prereqs')">Prerequisites</button>
          </div>
        </div>` : ''}
        <div class="p-5">
          <div id="tab-explanation"
               class="tab-pane ${isMath ? (activeTab === 'explanation' ? 'is-active' : '') : 'is-active'}">
          </div>
          ${isMath ? `
          <div id="tab-concept"
               class="tab-pane ${activeTab === 'concept' ? 'is-active' : ''}">
            ${conceptHtml}
          </div>
          <div id="tab-prereqs"
               class="tab-pane ${activeTab === 'prereqs' ? 'is-active' : ''}">
            ${prereqsHtml}
          </div>` : ''}
        </div>
      </div>

      ${trapHtml}

      <div class="admin-bar">
        <span class="text-xs font-semibold text-slate-400">Pool:</span>
        ${poolBtns}
        <span class="flex-1"></span>
        <button class="btn-approve ${status === 'approved' ? 'active' : ''}" id="btn-approve">
          ${status === 'approved' ? '✓ Approved' : '✓ Approve'}
        </button>
        <button class="btn-reject  ${status === 'rejected' ? 'active' : ''}" id="btn-reject">
          ${status === 'rejected' ? '✗ Rejected' : '✗ Reject'}
        </button>
      </div>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   EVENT WIRING (admin buttons)
═══════════════════════════════════════════════════════════════ */
function wireEvents(q) {

  document.getElementById('btn-approve')?.addEventListener('click', async () => {
    const wasApproved = q.status === 'approved';
    q.status = wasApproved ? 'enriched' : 'approved';
    try {
      await apiPatch(`/api/admin/questions/${q.id}/${wasApproved ? 'pending' : 'approve'}`);
      showToast(wasApproved ? `${q.externalId} reverted to pending` : `✅ ${q.externalId} approved`);
    } catch (e) {
      q.status = wasApproved ? 'approved' : 'enriched';
      showToast(`Error: ${e.message}`, true);
    }
    updateStats(); buildSidebar(); renderQuestion();
  });

  document.getElementById('btn-reject')?.addEventListener('click', async () => {
    const prev = q.status;
    q.status = prev === 'rejected' ? 'enriched' : 'rejected';
    try {
      await apiPatch(`/api/admin/questions/${q.id}/${prev === 'rejected' ? 'pending' : 'reject'}`);
      showToast(prev === 'rejected' ? `${q.externalId} reverted to pending` : `❌ ${q.externalId} rejected`);
    } catch (e) {
      q.status = prev;
      showToast(`Error: ${e.message}`, true);
    }
    updateStats(); buildSidebar(); renderQuestion();
  });

  document.getElementById('btn-fix')?.addEventListener('click', async () => {
    const answer = document.getElementById('btn-fix').dataset.answer;
    const prev   = q.correctAnswer;
    const prevSt = q.status;
    q.correctAnswer = answer;
    q.status = 'approved';
    try {
      await apiPatch(`/api/admin/questions/${q.id}/answer`, { correctAnswer: answer });
      showToast(`🔧 ${q.externalId} fixed → ${answer} and approved`);
    } catch (e) {
      q.correctAnswer = prev; q.status = prevSt;
      showToast(`Error: ${e.message}`, true);
    }
    updateStats(); buildSidebar(); renderQuestion();
  });

  ['test', 'practice', 'both'].forEach(p => {
    document.getElementById(`pool-${p}`)?.addEventListener('click', async () => {
      const prev = q.pool;
      q.pool = p;
      try {
        await apiPatch(`/api/admin/questions/${q.id}/pool`, { pool: p });
        showToast(`Pool → ${p}`);
        ['test','practice','both'].forEach(pp => {
          const b = document.getElementById(`pool-${pp}`);
          if (b) b.className = `pool-btn${pp === p ? ' active-' + pp : ''}`;
        });
      } catch (e) {
        q.pool = prev;
        showToast(`Error: ${e.message}`, true);
      }
    });
  });
}

/* ═══════════════════════════════════════════════════════════════
   HELPERS
═══════════════════════════════════════════════════════════════ */
function sectionLabel(s) {
  return s === 'math' ? 'Math' : s === 'reading_writing' ? 'R&W' : s || '?';
}

function domainLabel(d) {
  const M = {
    algebra: 'Algebra', advanced_math: 'Adv Math',
    problem_solving_data: 'Problem Solving', geometry_trigonometry: 'Geometry',
    information_ideas: 'Info & Ideas', craft_structure: 'Craft & Structure',
    expression_ideas: 'Expression', standard_english: 'Standard English'
  };
  return M[d] || d || '?';
}

function escHtml(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

function processText(text) {
  if (!text) return '';
  const raw = String(text);

  // Split into math blocks and prose segments.
  // \n → <br> must only happen in prose — inserting <br> inside \[...\] or \(...\)
  // breaks the text node that KaTeX scans, preventing math from rendering.
  const mathRe = /(\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))/g;
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
      // Math block — HTML-escape, then strip standalone \n (not part of a LaTeX command).
      // Only replace \n NOT followed by a letter — avoids breaking \neq, \nabla, \not etc.
      return seg.t
        .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
        .replace(/\\n(?![a-zA-Z])/g, ' ')  // literal \n that is NOT a LaTeX command
        .replace(/\n/g, ' ');               // actual newline
    }
    // Prose — full processing: HTML-escape, un-escape table tags, newlines → <br>
    return seg.t
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
      .replace(/&lt;(\/?)table(\s[^>]*)?&gt;/gi, (_,a,b)=>`<${a}table${b||''}>`)
      .replace(/&lt;(\/?)thead(&gt;|[^>]*>)/gi, (_,a)=>`<${a}thead>`)
      .replace(/&lt;(\/?)tbody(&gt;|[^>]*>)/gi, (_,a)=>`<${a}tbody>`)
      .replace(/&lt;(\/?)tr(&gt;|[^>]*>)/gi,    (_,a)=>`<${a}tr>`)
      .replace(/&lt;th([^>]*)?&gt;/gi, (_,a)=>`<th${a||''}>`)
      .replace(/&lt;\/th&gt;/gi, `</th>`)
      .replace(/&lt;td([^>]*)?&gt;/gi, (_,a)=>`<td${a||''}>`)
      .replace(/&lt;\/td&gt;/gi, `</td>`)
      .replace(/\\n(?![a-zA-Z])/g, '<br>')  // literal \n not part of a LaTeX command
      .replace(/\n/g, '<br>');              // actual newline
  }).join('');
}

function renderKaTeXIn(el) {
  if (window.renderMathInElement && el) {
    renderMathInElement(el, {
      delimiters: [
        { left: '\\(', right: '\\)', display: false },
        { left: '\\[', right: '\\]', display: true  },
        { left: '$$',  right: '$$',  display: true  },
        { left: '$',   right: '$',   display: false }
      ],
      throwOnError: false
    });
  }
}

/* ═══════════════════════════════════════════════════════════════
   COVERAGE VIEW
═══════════════════════════════════════════════════════════════ */

// Official SAT skill taxonomy — mirrors sat_taxonomy.json exactly.
// Coverage matching uses EXACT skill_key slug (q.skillKey === sk.key).
// Older questions without skill_key are counted at domain level but show as 0 per skill.
const SAT_TAXONOMY = [
  {
    section: 'math', sectionLabel: 'Math',
    domains: [
      {
        key: 'algebra', label: 'Algebra', color: '#2563eb', target: 20,
        skills: [
          { key: 'linear_eq_one_var',             label: 'Linear equations in one variable',          desc: 'Solve linear equations with one variable, including equations with variables on both sides, fractions, and parentheses' },
          { key: 'linear_eq_word_problems',        label: 'Linear equation word problems',             desc: 'Translate real-world situations into linear equations and solve; interpret the solution in context' },
          { key: 'linear_eq_two_var',              label: 'Linear equations in two variables',         desc: 'Write, interpret, and solve linear equations in two variables; slope, intercepts, standard form, slope-intercept form, point-slope form' },
          { key: 'graphs_linear',                  label: 'Graphs of linear equations and functions',  desc: 'Interpret and create graphs of linear equations; identify slope, x-intercept, y-intercept from a graph; match graphs to equations' },
          { key: 'linear_functions',               label: 'Linear functions',                          desc: 'Define and evaluate linear functions; understand rate of change and initial value; model linear relationships' },
          { key: 'linear_functions_word_problems', label: 'Linear function word problems',             desc: 'Create and interpret linear functions from context; determine what the slope and intercept represent in the real world' },
          { key: 'systems_linear_eq',              label: 'Systems of two linear equations',           desc: 'Solve systems of two linear equations by substitution, elimination, or graphing; interpret number of solutions (one, none, infinite)' },
          { key: 'systems_linear_word_problems',   label: 'Systems of linear equations — word problems', desc: 'Model real-world problems with systems of two linear equations and solve; interpret solutions in context' },
          { key: 'linear_inequalities_one_var',    label: 'Linear inequalities in one variable',       desc: 'Solve and graph linear inequalities in one variable; interpret solution sets' },
          { key: 'linear_inequalities_two_var',    label: 'Linear inequalities in two variables',      desc: 'Graph linear inequalities in two variables; determine which region satisfies the inequality; write inequalities from graphs' },
          { key: 'systems_linear_inequalities',    label: 'Systems of linear inequalities',            desc: 'Graph and interpret systems of linear inequalities; identify feasible regions; model constraints with inequality systems' },
        ]
      },
      {
        key: 'advanced_math', label: 'Advanced Math', color: '#7c3aed', target: 15,
        skills: [
          { key: 'equivalent_expressions',         label: 'Equivalent expressions',                              desc: 'Rewrite algebraic expressions in equivalent forms; factor, expand, simplify; recognize structure in expressions' },
          { key: 'polynomial_operations',          label: 'Operations with polynomials',                         desc: 'Add, subtract, multiply, and divide polynomials; understand polynomial long division and synthetic division' },
          { key: 'factoring',                      label: 'Factoring quadratic and polynomial expressions',       desc: 'Factor quadratics (GCF, difference of squares, trinomial factoring); factor higher-degree polynomials; use factoring to solve equations' },
          { key: 'quadratic_equations',            label: 'Solving quadratic equations',                         desc: 'Solve quadratic equations by factoring, completing the square, and the quadratic formula; determine number and nature of solutions' },
          { key: 'quadratic_functions',            label: 'Quadratic functions and graphs',                      desc: 'Interpret vertex, axis of symmetry, intercepts, and direction of parabolas; convert between standard, vertex, and factored forms' },
          { key: 'exponential_functions',          label: 'Exponential functions',                               desc: 'Understand exponential growth and decay; percent change; interpret parameters in exponential models; compare linear vs. exponential growth' },
          { key: 'polynomial_functions',           label: 'Polynomial functions',                                desc: 'End behavior based on degree and leading coefficient; zeros and multiplicity; graph behavior; factor theorem' },
          { key: 'radicals_rational_exponents',    label: 'Radicals and rational exponents',                     desc: 'Simplify expressions with radicals and rational exponents; convert between radical and exponential notation; solve equations with radicals' },
          { key: 'rational_expressions',           label: 'Rational expressions and equations',                  desc: 'Simplify, add, subtract, multiply, and divide rational expressions; solve rational equations; identify extraneous solutions' },
          { key: 'radical_rational_abs_equations', label: 'Radical, rational, and absolute value equations',     desc: 'Solve equations involving radicals, rational expressions, and absolute value; check for and eliminate extraneous solutions' },
          { key: 'nonlinear_eq_systems',           label: 'Systems of one linear and one nonlinear equation',    desc: 'Solve systems where one equation is linear and one is quadratic or other nonlinear; interpret number of intersection points' },
          { key: 'function_notation',              label: 'Function notation, composition, and transformations', desc: 'Evaluate and interpret function notation; compose functions; understand transformations (shifts, reflections, stretches)' },
        ]
      },
      {
        key: 'problem_solving_data', label: 'Problem Solving & Data Analysis', color: '#0284c7', target: 20,
        skills: [
          { key: 'ratios_rates',               label: 'Ratios and rates',                              desc: 'Set up and solve ratio problems; understand rates and unit rates; work with part-to-part and part-to-whole ratios' },
          { key: 'proportional_relationships', label: 'Proportional relationships',                    desc: 'Identify and use proportional relationships; solve proportions; understand direct and inverse proportionality' },
          { key: 'unit_conversion',            label: 'Units and unit conversion',                     desc: 'Convert between units using dimensional analysis; work with derived units; interpret units in context' },
          { key: 'percentages',                label: 'Percentages',                                   desc: 'Calculate percent of a quantity; percent increase and decrease; percent change; working backwards from a percentage' },
          { key: 'data_center',                label: 'Measures of center',                            desc: 'Calculate and interpret mean, median, and mode; effect of adding/removing data on measures of center' },
          { key: 'data_spread',                label: 'Measures of spread',                            desc: 'Calculate and interpret range, interquartile range, and standard deviation; understand variability; compare distributions' },
          { key: 'data_distributions',         label: 'Data distributions',                            desc: 'Interpret histograms, dot plots, box plots, and frequency tables; describe shape (symmetric, skewed); identify outliers' },
          { key: 'scatterplots',               label: 'Scatterplots and lines of best fit',            desc: 'Interpret scatterplots; draw and use lines of best fit; understand positive/negative/no correlation; predict values' },
          { key: 'two_var_models',             label: 'Two-variable data models',                      desc: 'Determine whether a linear, quadratic, or exponential model best fits data; interpret the model in context' },
          { key: 'probability',                label: 'Probability',                                   desc: 'Calculate theoretical and experimental probability; use sample spaces; understand complementary and mutually exclusive events' },
          { key: 'conditional_probability',    label: 'Conditional probability and two-way tables',    desc: 'Calculate conditional probabilities from two-way tables; P(A|B) notation; independence; relative frequency' },
          { key: 'inference_statistics',       label: 'Inference from sample statistics',              desc: 'Understand margin of error; make inferences about populations from samples; interpret confidence intervals' },
          { key: 'evaluating_claims',          label: 'Evaluating statistical claims',                 desc: 'Distinguish observational studies from experiments; understand confounding variables, bias, and causation vs. correlation' },
        ]
      },
      {
        key: 'geometry_trigonometry', label: 'Geometry & Trigonometry', color: '#059669', target: 15,
        skills: [
          { key: 'area_2d',                    label: 'Area of 2D figures',                   desc: 'Calculate area of triangles, quadrilaterals (rectangles, parallelograms, trapezoids), and composite figures' },
          { key: 'perimeter_2d',               label: 'Perimeter and circumference',          desc: 'Calculate perimeter of polygons and circumference of circles; work with arcs' },
          { key: 'volume_surface_area',        label: 'Volume and surface area',              desc: 'Calculate volume and surface area of prisms, cylinders, pyramids, cones, and spheres; composite 3D figures' },
          { key: 'lines_angles',               label: 'Lines and angles',                     desc: 'Supplementary, complementary, vertical angles; angles formed by parallel lines cut by a transversal (corresponding, alternate interior, co-interior)' },
          { key: 'triangles',                  label: 'Triangle properties',                  desc: 'Triangle angle sum; exterior angles; isosceles and equilateral triangles; triangle inequality' },
          { key: 'similar_congruent_triangles', label: 'Similar and congruent triangles',     desc: 'Similarity criteria (AA, SAS, SSS); congruence criteria; use proportions to find missing sides in similar figures' },
          { key: 'special_right_triangles',    label: 'Special right triangles',              desc: '30-60-90 and 45-45-90 triangle side ratios; apply to find missing lengths without trigonometry' },
          { key: 'pythagorean_theorem',        label: 'Pythagorean theorem',                  desc: 'Apply the Pythagorean theorem to find missing sides; Pythagorean triples; distance in the coordinate plane' },
          { key: 'right_triangle_trig',        label: 'Right triangle trigonometry',          desc: 'SOH-CAH-TOA; find missing sides and angles using sine, cosine, tangent; apply to word problems (angles of elevation/depression)' },
          { key: 'law_sines_cosines',          label: 'Law of sines and cosines',             desc: 'Apply law of sines and law of cosines to non-right triangles; determine which law to use' },
          { key: 'unit_circle_radians',        label: 'Unit circle and radian measure',       desc: 'Convert between degrees and radians; find sine and cosine values using the unit circle; understand periodicity' },
          { key: 'circle_properties',          label: 'Circle properties — arcs and angles',  desc: 'Central angles and inscribed angles; arc length; sector area; arc and chord relationships' },
          { key: 'circle_equations',           label: 'Equation of a circle',                 desc: 'Write and interpret the standard equation of a circle (x-h)²+(y-k)²=r²; complete the square to find center and radius' },
          { key: 'coordinate_geometry',        label: 'Coordinate geometry',                  desc: 'Midpoint and distance formulas; slopes of parallel and perpendicular lines; geometric figures on the coordinate plane' },
        ]
      },
    ]
  },
  {
    section: 'reading_writing', sectionLabel: 'Reading & Writing',
    domains: [
      {
        key: 'information_ideas', label: 'Information & Ideas', color: '#d97706', target: 10,
        skills: [
          { key: 'central_ideas',                 label: 'Central ideas and details',              desc: 'Identify the main idea of a passage; distinguish central ideas from supporting details' },
          { key: 'command_evidence_textual',       label: 'Command of evidence — textual',          desc: 'Identify which quote or detail best supports a claim; evaluate evidence quality and relevance' },
          { key: 'command_evidence_quantitative',  label: 'Command of evidence — quantitative',     desc: 'Interpret data from graphs, tables, or charts alongside a passage; select evidence from quantitative sources' },
          { key: 'inferences',                    label: 'Inferences',                             desc: 'Draw logical inferences from the passage; understand what the text implies but does not state directly' },
          { key: 'cross_text_connections',        label: 'Cross-text connections',                 desc: 'Compare two passages; identify agreements, disagreements, or relationships between authors\' ideas' },
        ]
      },
      {
        key: 'craft_structure', label: 'Craft & Structure', color: '#c2410c', target: 10,
        skills: [
          { key: 'words_in_context',              label: 'Words in context',                       desc: 'Determine the meaning of a word or phrase as used in context; choose the most precise word for a given context' },
          { key: 'text_structure_purpose',        label: 'Text structure and purpose',             desc: 'Identify how a text is organized; understand the author\'s purpose; analyze how a specific sentence or paragraph functions' },
          { key: 'rhetorical_devices',            label: 'Rhetorical devices and author\'s perspective', desc: 'Identify rhetorical strategies (contrast, analogy, counterargument); understand tone; interpret the author\'s point of view' },
        ]
      },
      {
        key: 'expression_ideas', label: 'Expression of Ideas', color: '#0f766e', target: 10,
        skills: [
          { key: 'rhetorical_synthesis',          label: 'Rhetorically effective synthesis',       desc: 'Select information from notes or multiple sources to best accomplish a rhetorical goal; complete a sentence to support an argument' },
          { key: 'transitions',                   label: 'Transitions',                            desc: 'Choose the transition word or phrase that best connects ideas between sentences or paragraphs (contrast, addition, cause/effect, sequence)' },
        ]
      },
      {
        key: 'standard_english', label: 'Standard English Conventions', color: '#6d28d9', target: 10,
        skills: [
          { key: 'boundaries',                    label: 'Sentence boundaries',                    desc: 'Correct run-on sentences and fragments; use punctuation (period, semicolon, comma + conjunction) to join or separate clauses' },
          { key: 'subject_verb_agreement',        label: 'Subject-verb agreement',                 desc: 'Ensure verbs agree with their subjects in number; handle tricky cases (intervening phrases, inverted sentences, collective nouns)' },
          { key: 'pronoun_agreement',             label: 'Pronoun-antecedent agreement',           desc: 'Ensure pronouns agree with their antecedents in number and gender; avoid ambiguous pronoun reference' },
          { key: 'verb_tense_form',               label: 'Verb tense and form',                    desc: 'Choose the correct verb tense (past, present, future, perfect) and form (infinitive, gerund, participle) for the context' },
          { key: 'punctuation',                   label: 'Punctuation',                            desc: 'Use commas, colons, semicolons, dashes, and apostrophes correctly; punctuate nonrestrictive and restrictive clauses' },
          { key: 'modifiers',                     label: 'Modifiers',                              desc: 'Correct dangling and misplaced modifiers; ensure modifying phrases are adjacent to what they modify' },
        ]
      },
    ]
  }
];

let viewMode = 'review'; // 'review' | 'coverage'

function toggleView() {
  viewMode = viewMode === 'review' ? 'coverage' : 'review';
  const btn = document.getElementById('btn-coverage');
  const nav = document.getElementById('nav-controls');

  if (viewMode === 'coverage') {
    btn.textContent   = '← Back to Review';
    btn.style.cssText = 'border-color:#6366f1;color:#4f46e5;';
    nav.style.display = 'none';
    renderCoverage();
  } else {
    btn.textContent   = '📊 Coverage';
    btn.style.cssText = 'border-color:#6366f1;color:#4f46e5;';
    nav.style.display = '';
    renderQuestion();
  }
}

// Exact match on skill_key slug — no fuzzy matching.
// Questions generated before skill_key was tracked (skillKey == null) count only
// toward the domain total bar, not toward any individual skill row.
function skillCount(domainKey, skillKey) {
  return allQuestions.filter(q =>
    q.domain === domainKey && q.skillKey === skillKey
  ).length;
}

function renderCoverage() {
  const area = document.getElementById('question-area');

  const domainCounts = {};
  allQuestions.forEach(q => {
    if (!domainCounts[q.domain]) domainCounts[q.domain] = { total: 0, approved: 0 };
    domainCounts[q.domain].total++;
    if (q.status === 'approved') domainCounts[q.domain].approved++;
  });

  let html = '<div class="cov-grid">';

  SAT_TAXONOMY.forEach(sec => {
    html += `<div class="cov-section-header">${sec.sectionLabel}</div>`;

    sec.domains.forEach(dom => {
      const dc       = domainCounts[dom.key] || { total: 0, approved: 0 };
      const total    = dc.total;
      const approved = dc.approved;
      const pct      = Math.min(100, Math.round((total / dom.target) * 100));

      const barColor = pct < 25 ? '#ef4444' : pct < 60 ? '#f59e0b' : dom.color;
      const badgeBg  = pct < 25 ? '#fee2e2' : pct < 60 ? '#fef3c7' : '#dcfce7';
      const badgeFg  = pct < 25 ? '#b91c1c' : pct < 60 ? '#92400e' : '#15803d';

      const skillRows = dom.skills.map(sk => {
        const cnt = skillCount(dom.key, sk.key);
        const dot = cnt > 0 ? dom.color : '#e2e8f0';
        const fg  = cnt > 0 ? '#1e293b' : '#94a3b8';
        return `<div class="cov-skill-row">
          <span class="cov-skill-dot" style="background:${dot};margin-top:3px;"></span>
          <span class="cov-skill-body">
            <span class="cov-skill-name" style="color:${fg};">${sk.label}</span>
            <span class="cov-skill-desc">${sk.desc}</span>
          </span>
          <span class="cov-skill-count" style="color:${cnt > 0 ? dom.color : '#cbd5e1'};">${cnt}</span>
        </div>`;
      }).join('');

      html += `
        <div class="cov-card">
          <div class="cov-card-header">
            <span class="cov-domain-name">${dom.label}</span>
            <span class="cov-count-badge" style="background:${badgeBg};color:${badgeFg};">
              ${total} / ${dom.target}
            </span>
          </div>
          <div class="cov-bar-track">
            <div class="cov-bar-fill" style="width:${pct}%;background:${barColor};"></div>
          </div>
          ${skillRows}
          ${approved < total
            ? `<p class="text-xs text-slate-400 mt-2">${approved} approved · ${total - approved} pending review</p>`
            : total > 0
              ? `<p class="text-xs text-green-600 mt-2">All ${approved} approved ✓</p>`
              : ''}
        </div>`;
    });
  });

  html += '</div>';
  area.innerHTML = html;
}

/* ═══════════════════════════════════════════════════════════════
   BOOT
═══════════════════════════════════════════════════════════════ */
(async () => {
  try {
    const resp = await fetch('/api/admin/questions');
    if (!resp.ok) throw new Error(`HTTP ${resp.status} — is the Spring Boot server running?`);
    allQuestions = await resp.json();
    updateStats();
    buildSidebar();
    renderQuestion();
  } catch (err) {
    document.getElementById('question-area').innerHTML = `
      <div class="empty-panel">
        <div style="font-size:2.5rem">⚠️</div>
        <p class="mt-3 text-red-500 font-semibold">Failed to load questions</p>
        <p class="text-sm mt-1 text-slate-400">${err.message}</p>
      </div>`;
    document.getElementById('header-sub').textContent = 'Could not reach API';
  }
})();
