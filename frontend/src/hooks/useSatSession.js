/**
 * useSatSession — manages a SAT-style practice session.
 *
 * All N questions are loaded upfront. The student navigates freely,
 * selects answers, and marks questions for review. Answers are submitted
 * silently to the backend as the student moves between questions.
 * On finishSession(), the session is marked completed and the student
 * is sent to the SummaryPage.
 */
import { useState, useCallback, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api/client'

export function useSatSession(sessionId) {
  const navigate = useNavigate()

  // All pre-queued questions (SessionQuestionResponse[])
  const [questions,   setQuestions]   = useState([])
  const [currentIdx,  setCurrentIdx]  = useState(0)
  // { [questionId]: { answer, timeSpentSeconds } }
  const [localAnswers, setLocalAnswers] = useState({})
  const [loading,     setLoading]     = useState(true)
  const [submitting,  setSubmitting]  = useState(false)
  const [error,       setError]       = useState(null)

  // Per-question elapsed seconds (wall-clock from when question was shown)
  const questionStartRef = useRef(Date.now())
  const localAnswersRef  = useRef({})
  const questionsRef     = useRef([])

  // Keep refs in sync so callbacks don't close over stale state
  useEffect(() => { localAnswersRef.current = localAnswers }, [localAnswers])
  useEffect(() => { questionsRef.current = questions },       [questions])

  // ── Init: load all questions ─────────────────────────────────────────
  const init = useCallback(async () => {
    try {
      const qs = await api.getSessionQuestions(sessionId)
      setQuestions(qs)
      questionsRef.current = qs

      // Restore existing answers (session resume)
      const restored = {}
      qs.forEach(sq => {
        if (sq.existingAnswer) {
          restored[sq.question.id] = { answer: sq.existingAnswer, timeSpentSeconds: 0 }
        }
      })
      setLocalAnswers(restored)
      localAnswersRef.current = restored

      // Jump to first unanswered question on resume
      const firstUnanswered = qs.findIndex(sq => !sq.existingAnswer)
      const startIdx = firstUnanswered >= 0 ? firstUnanswered : 0
      setCurrentIdx(startIdx)

      questionStartRef.current = Date.now()
      setLoading(false)
    } catch (e) {
      setError(e.message || 'Failed to load questions')
      setLoading(false)
    }
  }, [sessionId])

  // ── Derived ──────────────────────────────────────────────────────────
  const currentQuestion  = questions[currentIdx] ?? null
  const total            = questions.length
  const answeredCount    = Object.keys(localAnswers).length
  const markedCount      = questions.filter(q => q.marked).length

  // ── Select an answer for the current question ────────────────────────
  const selectAnswer = useCallback((answer) => {
    if (!currentQuestion) return
    const qid = currentQuestion.question.id
    const elapsed = Math.round((Date.now() - questionStartRef.current) / 1000)
    setLocalAnswers(prev => {
      const updated = { ...prev, [qid]: { answer, timeSpentSeconds: elapsed } }
      localAnswersRef.current = updated
      return updated
    })
  }, [currentQuestion])

  // ── Submit current question's answer silently ────────────────────────
  const submitCurrentSilently = useCallback(async (qid) => {
    const local = localAnswersRef.current[qid]
    if (!local?.answer) return
    try {
      await api.submitAnswer(sessionId, qid, local.answer, local.timeSpentSeconds)
    } catch (e) {
      // Log but don't block navigation — will retry on next visit or resume
      console.warn('Silent submit failed:', e.message)
    }
  }, [sessionId])

  // ── Navigate to a question by index ─────────────────────────────────
  const goTo = useCallback(async (idx) => {
    if (idx < 0 || idx >= questionsRef.current.length) return
    // Submit current answer before leaving
    const cur = questionsRef.current[currentIdx]
    if (cur) await submitCurrentSilently(cur.question.id)
    // Reset timer
    questionStartRef.current = Date.now()
    setCurrentIdx(idx)
  }, [currentIdx, submitCurrentSilently])

  const goNext = useCallback(() => goTo(currentIdx + 1), [currentIdx, goTo])
  const goPrev = useCallback(() => goTo(currentIdx - 1), [currentIdx, goTo])

  // ── Toggle mark for review ───────────────────────────────────────────
  const toggleMark = useCallback(async (questionId) => {
    // Optimistic update
    setQuestions(prev => prev.map(sq =>
      sq.question.id === questionId ? { ...sq, marked: !sq.marked } : sq
    ))
    try {
      await api.toggleMarkQuestion(sessionId, questionId)
    } catch (e) {
      // Revert on failure
      setQuestions(prev => prev.map(sq =>
        sq.question.id === questionId ? { ...sq, marked: !sq.marked } : sq
      ))
      console.warn('Mark toggle failed:', e.message)
    }
  }, [sessionId])

  // ── Finish session ───────────────────────────────────────────────────
  const finishSession = useCallback(async () => {
    setSubmitting(true)
    try {
      // Submit current question's answer
      const cur = questionsRef.current[currentIdx]
      if (cur) await submitCurrentSilently(cur.question.id)
      // Mark session completed
      await api.completeSession(sessionId)
    } catch (e) {
      console.warn('Finish session error:', e.message)
    } finally {
      navigate(`/session/${sessionId}/summary`, { replace: true })
    }
  }, [currentIdx, submitCurrentSilently, sessionId, navigate])

  return {
    // State
    loading, error, submitting,
    questions, currentIdx, currentQuestion,
    total, answeredCount, markedCount,
    localAnswers,
    // Actions
    init, selectAnswer, goTo, goNext, goPrev,
    toggleMark, finishSession,
  }
}
