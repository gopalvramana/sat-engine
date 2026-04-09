import { useState, useCallback } from 'react'
import * as api from '../api/client'

/**
 * Manages the full lifecycle of a practice session:
 *   idle → loading → question → feedback → question → ... → summary
 *
 * Review mode: pressing Back navigates through answered history.
 * reviewIndex === null  → live view (current question or just-submitted feedback)
 * reviewIndex === N     → showing history[N].question + history[N].feedback
 */
export function useSession() {
  const [sessionId, setSessionId]         = useState(null)
  const [liveQuestion, setLiveQuestion]   = useState(null)
  const [liveFeedback, setLiveFeedback]   = useState(null)
  const [liveAnswer, setLiveAnswer]       = useState(null)   // student's answer for live Q
  const [sessionInfo, setSessionInfo]     = useState(null)
  const [history, setHistory]             = useState([])     // [{question, feedback, studentAnswer}]
  const [livePhase, setLivePhase]         = useState('idle') // idle|loading|question|feedback|summary
  const [error, setError]                 = useState(null)
  const [reviewIndex, setReviewIndex]     = useState(null)   // null = live; number = history index

  // ── Derived display values (review overrides live) ────────────────
  const isReviewing   = reviewIndex !== null
  const question      = isReviewing ? history[reviewIndex]?.question      : liveQuestion
  const feedback      = isReviewing ? history[reviewIndex]?.feedback      : liveFeedback
  const studentAnswer = isReviewing ? history[reviewIndex]?.studentAnswer : liveAnswer
  const phase         = isReviewing ? 'feedback' : livePhase

  // ── Start a new session ───────────────────────────────────────────
  const startSession = useCallback(async (sessionType, section, domainBandCounts) => {
    setLivePhase('loading')
    setError(null)
    setReviewIndex(null)
    try {
      const session = await api.createSession(sessionType, section, domainBandCounts)
      setSessionId(session.id)
      setSessionInfo(session)
      setHistory([])
      await _loadNext(session.id)
    } catch (e) {
      setError(e.message)
      setLivePhase('idle')
    }
  }, [])

  // ── Load the next question ────────────────────────────────────────
  const _loadNext = useCallback(async (sid) => {
    setLivePhase('loading')
    setLiveFeedback(null)
    setLiveQuestion(null)
    setLiveAnswer(null)
    setReviewIndex(null)   // exit review mode when a new question loads
    try {
      const q = await api.getNextQuestion(sid)
      if (!q) {
        const info = await api.getSession(sid)
        setSessionInfo(info)
        setLivePhase('summary')
      } else {
        setLiveQuestion(q)
        setLivePhase('question')
      }
    } catch (e) {
      setError(e.message)
    }
  }, [])

  // ── Submit an answer ──────────────────────────────────────────────
  const submitAnswer = useCallback(async (answer) => {
    if (!sessionId || !liveQuestion) return
    setLiveAnswer(answer)
    setLivePhase('loading')
    try {
      const fb = await api.submitAnswer(sessionId, liveQuestion.id, answer)
      setLiveFeedback(fb)
      setHistory(h => [...h, { question: liveQuestion, feedback: fb, studentAnswer: answer }])
      const info = await api.getSession(sessionId)
      setSessionInfo(info)
      setLivePhase('feedback')
    } catch (e) {
      setError(e.message)
      setLivePhase('question')
    }
  }, [sessionId, liveQuestion])

  // ── Next: advance history review OR load fresh question ──────────
  const nextQuestion = useCallback(() => {
    if (isReviewing) {
      // If there are more history items ahead, advance; else return to live view
      if (reviewIndex < history.length - 1) {
        setReviewIndex(reviewIndex + 1)
      } else {
        setReviewIndex(null)   // back to current live state
      }
    } else {
      if (sessionId) _loadNext(sessionId)
    }
  }, [isReviewing, reviewIndex, history.length, sessionId, _loadNext])

  // ── Back: go to previous answered question ────────────────────────
  const goBack = useCallback(() => {
    if (isReviewing) {
      if (reviewIndex > 0) setReviewIndex(reviewIndex - 1)
      // At index 0 — already at earliest; do nothing
    } else {
      // Live view → jump to last answered question
      if (history.length > 0) setReviewIndex(history.length - 1)
    }
  }, [isReviewing, reviewIndex, history.length])

  // ── End session early → go to summary ────────────────────────────
  const endSession = useCallback(async () => {
    if (!sessionId) { setLivePhase('idle'); return }
    try {
      const info = await api.getSession(sessionId)
      setSessionInfo(info)
    } catch { /* ignore */ }
    setReviewIndex(null)
    setLivePhase('summary')
  }, [sessionId])

  return {
    phase,          // derived: 'idle'|'loading'|'question'|'feedback'|'summary'
    question,       // derived: live or history[reviewIndex]
    feedback,       // derived: live or history[reviewIndex]
    studentAnswer,  // derived: live or history[reviewIndex]
    sessionInfo,
    history,
    isReviewing,
    reviewIndex,
    error,
    startSession,
    submitAnswer,
    nextQuestion,
    goBack,
    endSession,
  }
}
