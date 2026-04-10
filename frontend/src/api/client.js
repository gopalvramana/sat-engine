/**
 * API client — all URLs are relative so they work in both:
 *   dev  : Vite proxies /api → localhost:8080
 *   prod : same origin, Spring Boot serves everything
 */

async function request(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${method} ${url} → ${res.status}: ${text}`)
  }
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

/** POST /api/sessions/{id}/answers — submit answer, get feedback */
export function submitAnswer(sessionId, questionId, studentAnswer) {
  return request('POST', `/api/sessions/${sessionId}/answers`, { questionId, studentAnswer })
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
