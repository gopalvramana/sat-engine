import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { usePracticeSession } from '../hooks/usePracticeSession'
import ProgressBar from '../components/ProgressBar/ProgressBar'
import QuestionCard from '../components/QuestionCard/QuestionCard'
import FeedbackPanel from '../components/FeedbackPanel/FeedbackPanel'
import Toolbar from '../components/Toolbar/Toolbar'
import { useState } from 'react'
import styles from './PracticePage.module.css'

export default function PracticePage() {
  const { sessionId } = useParams()
  const navigate      = useNavigate()

  const {
    phase, question, feedback, sessionInfo,
    submitAnswer, nextQuestion, goBack, endSession,
    studentAnswer, timeTaken, isReviewing, error, loadNext,
  } = usePracticeSession(sessionId)

  // Load first question on mount
  useEffect(() => {
    loadNext()
  }, []) // intentionally empty — fire once on mount

  // Mark-for-review state
  const [markedIds, setMarkedIds] = useState(new Set())
  const isMarked = markedIds.has(question?.id)
  function handleMarkToggle() {
    if (!question?.id) return
    setMarkedIds(prev => {
      const next = new Set(prev)
      next.has(question.id) ? next.delete(question.id) : next.add(question.id)
      return next
    })
  }

  if (error) {
    return (
      <div style={{ padding: 40, textAlign: 'center', fontFamily: 'Inter, system-ui' }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#ef4444', marginBottom: 8 }}>
          Something went wrong
        </div>
        <div style={{ fontSize: 14, color: '#64748b' }}>{error}</div>
        <button
          onClick={() => navigate('/practice')}
          style={{ marginTop: 20, padding: '8px 24px', background: '#d97706', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 14 }}
        >
          Back to Practice
        </button>
      </div>
    )
  }

  const answered = sessionInfo?.questionsAnswered ?? 0
  const correct  = sessionInfo?.correctCount      ?? 0
  const total    = sessionInfo?.totalQuestions    ?? 0
  const current  = phase === 'feedback' ? answered : answered + 1

  return (
    <div className={styles.page}>
      <ProgressBar
        current={current}
        total={total}
        correct={correct}
        onBack={goBack}
        onEnd={endSession}
        isReviewing={isReviewing}
      />

      <Toolbar
        phase={phase}
        calculatorOk={question?.calculatorOk ?? true}
      />

      <div className={styles.content}>
        {phase === 'loading' && (
          <div className={styles.loading}>
            <div className={styles.spinner} />
            <span>Loading…</span>
          </div>
        )}

        {(phase === 'question' || phase === 'feedback') && question && (
          <div className={`${styles.questionWrap} ${phase === 'question' ? styles.questionOnly : ''}`}>
            {/* Left: question + choices (sticky) */}
            <div className={styles.leftCol}>
              <QuestionCard
                question={question}
                onSubmit={submitAnswer}
                disabled={phase === 'feedback' || phase === 'loading'}
                feedback={phase === 'feedback' ? feedback : null}
                studentAnswer={studentAnswer}
                timeTaken={timeTaken}
                isMarked={isMarked}
                onMarkToggle={handleMarkToggle}
              />
            </div>

            {/* Right: feedback panel — only visible after answering */}
            {phase === 'feedback' && feedback && (
              <div className={styles.rightCol}>
                <FeedbackPanel
                  feedback={feedback}
                  question={question}
                  studentAnswer={studentAnswer}
                  onNext={nextQuestion}
                  isReviewing={isReviewing}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
