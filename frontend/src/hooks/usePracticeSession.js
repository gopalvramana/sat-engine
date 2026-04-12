import { useState, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api/client'
import { useTimer } from './useTimer'
import log from '../lib/logger'

/**
 * Manages the question/feedback loop for an active practice session.
 * Reads from a fixed sessionId (from URL); navigates to summary when done.
 *
 * Phases:
 *   loading   → fetching next question or submitting
 *   question  → student answering
 *   feedback  → answer submitted, showing result
 *   (no idle/summary — those are separate pages)
 *
 * Review mode: reviewIndex !== null → showing a past question from history.
 */
export function usePracticeSession(sessionId) {
  const navigate = useNavigate()

  const [liveQuestion, setLiveQuestion] = useState(null)
  const [liveFeedback, setLiveFeedback] = useState(null)
  const [liveAnswer,   setLiveAnswer]   = useState(null)
  const [sessionInfo,  setSessionInfo]  = useState(null)
  const [livePhase,    setLivePhase]    = useState('loading')
  const [error,        setError]        = useState(null)
  const [reviewIndex,  setReviewIndex]  = useState(null)

  // history kept in both a ref (stale-closure-safe) and state (render trigger)
  const historyRef = useRef([])
  const [history, setHistory] = useState([])

  const timer = useTimer()

  function appendHistory(item) {
    const next = [...historyRef.current, item]
    historyRef.current = next
    setHistory(next)
  }

  // ── Derived display values ───────────────────────────────────────────
  const isReviewing   = reviewIndex !== null
  const question      = isReviewing ? history[reviewIndex]?.question      : liveQuestion
  const feedback      = isReviewing ? history[reviewIndex]?.feedback      : liveFeedback
  const studentAnswer = isReviewing ? history[reviewIndex]?.studentAnswer : liveAnswer
  const phase         = isReviewing ? 'feedback' : livePhase

  const timeTaken = isReviewing
    ? (historyRef.current[reviewIndex]?.timeTaken ?? 0)
    : liveFeedback
      ? (historyRef.current[historyRef.current.length - 1]?.timeTaken ?? 0)
      : timer.seconds

  // ── Load next question (or navigate to summary) ──────────────────────
  const loadNext = useCallback(async () => {
    log.debug('loadNext', { sessionId, historyLength: historyRef.current.length })
    setLivePhase('loading')
    setLiveFeedback(null)
    setLiveQuestion(null)
    setLiveAnswer(null)
    setReviewIndex(null)
    try {
      const q = await api.getNextQuestion(sessionId)
      if (!q) {
        log.info('session exhausted', { sessionId, totalAnswered: historyRef.current.length })
        // Session exhausted — navigate to summary, passing history via state
        const info = await api.getSession(sessionId)
        navigate(`/session/${sessionId}/summary`, {
          state: { sessionInfo: info, history: historyRef.current },
          replace: true,
        })
      } else {
        log.info('question loaded', { questionId: q.id, domain: q.domain, difficulty: q.difficulty, phase: 'question' })
        setLiveQuestion(q)
        setLivePhase('question')
        timer.start()
      }
    } catch (e) {
      log.error('session error', { error: e.message, phase: livePhase })
      setError(e.message)
    }
  }, [sessionId, navigate])

  // ── Submit answer ────────────────────────────────────────────────────
  const submitAnswer = useCallback(async (answer) => {
    if (!liveQuestion) return
    log.debug('submitting answer', { questionId: liveQuestion?.id, answer })
    const t = timer.stop()
    setLiveAnswer(answer)
    setLivePhase('loading')
    try {
      const fb   = await api.submitAnswer(sessionId, liveQuestion.id, answer)
      const info = await api.getSession(sessionId)
      log.info('answer result', { questionId: liveQuestion.id, correct: fb.isCorrect, timeSecs: t })
      setLiveFeedback(fb)
      setSessionInfo(info)
      appendHistory({ question: liveQuestion, feedback: fb, studentAnswer: answer, timeTaken: t })
      log.debug('review mode', { index: historyRef.current.length - 1 })
      setLivePhase('feedback')
    } catch (e) {
      log.error('session error', { error: e.message, phase: livePhase })
      setError(e.message)
      setLivePhase('question')
    }
  }, [sessionId, liveQuestion])

  // ── Next: advance review OR load fresh question ──────────────────────
  const nextQuestion = useCallback(() => {
    if (isReviewing) {
      if (reviewIndex < historyRef.current.length - 1) {
        setReviewIndex(reviewIndex + 1)
      } else {
        setReviewIndex(null)
      }
    } else {
      loadNext()
    }
  }, [isReviewing, reviewIndex, loadNext])

  // ── Back: enter review mode ──────────────────────────────────────────
  const goBack = useCallback(() => {
    if (isReviewing) {
      if (reviewIndex > 0) setReviewIndex(reviewIndex - 1)
    } else {
      if (historyRef.current.length > 0) setReviewIndex(historyRef.current.length - 1)
    }
  }, [isReviewing, reviewIndex])

  // ── End session early → navigate to summary ──────────────────────────
  const endSession = useCallback(async () => {
    log.info('session ended early', { sessionId, answered: historyRef.current.length })
    try {
      const info = await api.getSession(sessionId)
      navigate(`/session/${sessionId}/summary`, {
        state: { sessionInfo: info, history: historyRef.current },
        replace: true,
      })
    } catch {
      navigate(`/session/${sessionId}/summary`, {
        state: { sessionInfo: null, history: historyRef.current },
        replace: true,
      })
    }
  }, [sessionId, navigate])

  return {
    phase, question, feedback, studentAnswer,
    sessionInfo, history, timeTaken, isReviewing, error,
    loadNext, submitAnswer, nextQuestion, goBack, endSession,
  }
}
