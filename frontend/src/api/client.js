/**
 * API client — all URLs are relative so they work in both:
 *   dev  : Vite proxies /api → localhost:8080
 *   prod : same origin, Spring Boot serves everything
 */
import log from '../lib/logger'

async function request(method, url, body) {
  log.debug('→ API', { method, url, body: body ? '(body)' : undefined })
  const t0  = performance.now()
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) {
    log.debug('← API 204', { method, url })
    return null
  }
  if (!res.ok) {
    const text = await res.text()
    log.error('← API error', { method, url, status: res.status, body: text, ms: Math.round(performance.now() - t0) })
    throw new Error(`${method} ${url} → ${res.status}: ${text}`)
  }
  log.debug('← API', { method, url, status: res.status, ms: Math.round(performance.now() - t0) })
  return res.json()
}

// ── Sessions ────────────────────────────────────────────────────────

/** POST /api/sessions — create a new practice session */
export function createSession(sessionType, section, domainBandCounts) {
  return request('POST', '/api/sessions', {
    sessionType,
    section: section || null,
    domainBandCounts: domainBandCounts || null,
  })
}

/** GET /api/questions/count — counts per domain broken down by difficulty band */
export function getQuestionCounts(section) {
  const params = new URLSearchParams()
  if (section) params.set('section', section)
  return request('GET', `/api/questions/count?${params}`)
}

/** GET /api/sessions/{id} — current session status + counts */
export function getSession(id) {
  return request('GET', `/api/sessions/${id}`)
}

/** GET /api/sessions/{id}/next — next question; null when exhausted (204) */
export function getNextQuestion(id) {
  return request('GET', `/api/sessions/${id}/next`)
}

/** POST /api/sessions/{id}/answers — submit (or update) answer, get feedback */
export function submitAnswer(sessionId, questionId, studentAnswer, timeSpentSeconds) {
  return request('POST', `/api/sessions/${sessionId}/answers`, { questionId, studentAnswer, timeSpentSeconds })
}

/** GET /api/sessions/{id}/questions — all pre-queued questions with marks + existing answers */
export function getSessionQuestions(sessionId) {
  return request('GET', `/api/sessions/${sessionId}/questions`)
}

/** PATCH /api/sessions/{id}/questions/{questionId}/mark — toggle mark-for-review */
export function toggleMarkQuestion(sessionId, questionId) {
  return request('PATCH', `/api/sessions/${sessionId}/questions/${questionId}/mark`, {})
}

/** POST /api/sessions/{id}/complete — mark session as completed */
export function completeSession(sessionId) {
  return request('POST', `/api/sessions/${sessionId}/complete`)
}

/** GET /api/sessions/active — active (unfinished) session for the user, or null (204) */
export function getActiveSession() {
  return request('GET', '/api/sessions/active')
}

// ── Gap analysis ─────────────────────────────────────────────────────

/** POST /api/gaps/analyze — get gap cards for a wrong answer */
export function analyzeGap(questionId, studentAnswer) {
  return request('POST', '/api/gaps/analyze', { questionId, studentAnswer })
}

// ── Skill content ─────────────────────────────────────────────────────

/** GET /api/skills/{skillKey}/content — skill study content JSON */
export function getSkillContent(skillKey) {
  return request('GET', `/api/skills/${skillKey}/content`)
}
