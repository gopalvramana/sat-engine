import { useState, useCallback } from 'react'
import * as api from '../api/client'

/**
 * Manages the full lifecycle of a practice session:
 *   idle → loading → question → feedback → question → ... → summary
 */
export function useSession() {
  const [sessionId, setSessionId]     = useState(null)
  const [question, setQuestion]       = useState(null)   // current QuestionResponse
  const [feedback, setFeedback]       = useState(null)   // AnswerFeedback after submit
  const [sessionInfo, setSessionInfo] = useState(null)   // SessionResponse (counts)
  const [history, setHistory]         = useState([])     // [{question, feedback}] for summary
  const [phase, setPhase]             = useState('idle') // idle | loading | question | feedback | summary
  const [error, setError]             = useState(null)

  // ── Start a new session ───────────────────────────────────────────
  const startSession = useCallback(async (sessionType, section, domainBandCounts) => {
    setPhase('loading')
    setError(null)
    try {
      const session = await api.createSession(sessionType, section, domainBandCounts)
      setSessionId(session.id)
      setSessionInfo(session)
      setHistory([])
      await _loadNext(session.id)
    } catch (e) {
      setError(e.message)
      setPhase('idle')
    }
  }, [])

  // ── Load the next question ────────────────────────────────────────
  const _loadNext = useCallback(async (sid) => {
    setPhase('loading')
    setFeedback(null)
    setQuestion(null)
    try {
      const q = await api.getNextQuestion(sid)
      if (!q) {
        // 204 — pool exhausted
        const info = await api.getSession(sid)
        setSessionInfo(info)
        setPhase('summary')
      } else {
        setQuestion(q)
        setPhase('question')
      }
    } catch (e) {
      setError(e.message)
    }
  }, [])

  // ── Submit an answer ──────────────────────────────────────────────
  const submitAnswer = useCallback(async (answer) => {
    if (!sessionId || !question) return
    setPhase('loading')
    try {
      const fb = await api.submitAnswer(sessionId, question.id, answer)
      setFeedback(fb)
      setHistory(h => [...h, { question, feedback: fb }])
      // Refresh session counts
      const info = await api.getSession(sessionId)
      setSessionInfo(info)
      setPhase('feedback')
    } catch (e) {
      setError(e.message)
      setPhase('question')
    }
  }, [sessionId, question])

  // ── Move to next question ─────────────────────────────────────────
  const nextQuestion = useCallback(() => {
    if (sessionId) _loadNext(sessionId)
  }, [sessionId, _loadNext])

  return {
    phase,        // 'idle' | 'loading' | 'question' | 'feedback' | 'summary'
    question,     // QuestionResponse
    feedback,     // AnswerFeedback
    sessionInfo,  // SessionResponse
    history,      // [{question, feedback}]
    error,
    startSession,
    submitAnswer,
    nextQuestion,
  }
}
