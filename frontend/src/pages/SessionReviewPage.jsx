import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import QuestionCard from '../components/QuestionCard/QuestionCard'
import FeedbackPanel from '../components/FeedbackPanel/FeedbackPanel'
import styles from './SessionReviewPage.module.css'

export default function SessionReviewPage() {
  const { sessionId, index: indexStr } = useParams()
  const navigate = useNavigate()
  const index = parseInt(indexStr, 10) || 0

  const [answers, setAnswers] = useState(null) // SessionAnswerDetail[]
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(false)

  useEffect(() => {
    fetch(`/api/sessions/${sessionId}/answers`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) { setError(true); return }
        setAnswers(data)
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [sessionId])

  const goTo = useCallback((i) => {
    navigate(`/session/${sessionId}/review/${i}`, { replace: true })
  }, [navigate, sessionId])

  const goNext = useCallback(() => {
    if (!answers) return
    if (index < answers.length - 1) goTo(index + 1)
    else navigate(`/session/${sessionId}/summary`)
  }, [answers, index, goTo, navigate, sessionId])

  const goPrev = useCallback(() => {
    if (index > 0) goTo(index - 1)
  }, [index, goTo])

  if (loading) return <div className={styles.centred}>Loading…</div>
  if (error || !answers) return <div className={styles.centred}>Could not load session.</div>

  const a   = answers[index]
  const total = answers.length
  const isLast = index === total - 1

  if (!a) {
    navigate(`/session/${sessionId}/summary`)
    return null
  }

  // Build question object for QuestionCard (matches QuestionResponse shape)
  const question = {
    id:                  a.questionId,
    questionStem:        a.questionStem,
    domain:              a.domain,
    skill:               a.skill,
    difficulty:          a.difficulty,
    questionType:        a.questionType,
    optionA:             a.optionA,
    optionB:             a.optionB,
    optionC:             a.optionC,
    optionD:             a.optionD,
    passageText:         a.passageText,
    passageSource:       a.passageSource,
    diagramJson:         a.diagramJson,
    animationJson:       a.animationJson,
    coreConceptJson:     a.coreConceptJson,
    choiceExplanations:  a.choiceExplanations,
    alternativeApproach: a.alternativeApproach,
    skillKey:            a.skillKey,
    calculatorOk:        true,
  }

  // Build feedback object for FeedbackPanel (matches AnswerFeedback shape)
  const feedback = {
    isCorrect:        a.isCorrect,
    correctAnswer:    a.correctAnswer,
    explanationShort: a.explanationShort,
    explanationSteps: a.explanationSteps,
  }

  return (
    <div className={styles.page}>
      {/* ── Top bar ──────────────────────────────────────────── */}
      <div className={styles.topBar}>
        <button className={styles.backBtn} onClick={() => navigate(`/session/${sessionId}/summary`)}>
          ← Summary
        </button>

        <div className={styles.navCenter}>
          {/* Dot indicators */}
          <div className={styles.dotRow}>
            {answers.map((ans, i) => (
              <button
                key={i}
                onClick={() => goTo(i)}
                className={`${styles.dot} ${i === index ? styles.dotCurrent : ans.isCorrect ? styles.dotCorrect : styles.dotWrong}`}
                title={`Q${i + 1}: ${ans.isCorrect ? 'Correct' : 'Incorrect'}`}
              />
            ))}
          </div>
          <span className={styles.navLabel}>Q{index + 1} of {total}</span>
        </div>

        <div className={styles.navBtns}>
          <button className={styles.navBtn} onClick={goPrev} disabled={index === 0}>← Prev</button>
          <button className={styles.navBtn} onClick={goNext}>
            {isLast ? 'Summary →' : 'Next →'}
          </button>
        </div>
      </div>

      {/* ── Two-column layout (mirrors PracticePage) ─────────── */}
      <div className={styles.content}>
        <div className={styles.questionWrap}>
          <div className={styles.leftCol}>
            <QuestionCard
              question={question}
              feedback={feedback}
              studentAnswer={a.studentAnswer}
              timeTaken={a.timeSpentSeconds}
              disabled
              reviewMode
            />
          </div>
          <div className={styles.rightCol}>
            <FeedbackPanel
              feedback={feedback}
              question={question}
              studentAnswer={a.studentAnswer}
              onNext={goNext}
              isReviewing
              isLastQuestion={isLast}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
