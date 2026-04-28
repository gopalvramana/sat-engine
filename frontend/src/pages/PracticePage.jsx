import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useSatSession } from '../hooks/useSatSession'
import QuestionCard from '../components/QuestionCard/QuestionCard'
import Toolbar from '../components/Toolbar/Toolbar'
import QuestionGrid from '../components/QuestionGrid/QuestionGrid'
import SessionNavBar from '../components/SessionNavBar/SessionNavBar'
import styles from './PracticePage.module.css'

export default function PracticePage() {
  const { sessionId } = useParams()
  const navigate      = useNavigate()

  const {
    loading, error, submitting,
    questions, currentIdx, currentQuestion,
    total, answeredCount, markedCount,
    localAnswers,
    init, selectAnswer, goTo, goNext, goPrev,
    toggleMark, finishSession,
  } = useSatSession(sessionId)

  const [gridOpen,   setGridOpen]   = useState(false)
  const [confirmEnd, setConfirmEnd] = useState(false)

  // Load questions on mount
  useEffect(() => { init() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Error ─────────────────────────────────────────────────────────────
  if (error) {
    return (
      <div className={styles.centred}>
        <div className={styles.errorTitle}>Something went wrong</div>
        <div className={styles.errorSub}>{error}</div>
        <button className={styles.errorBtn} onClick={() => navigate('/practice')}>
          Back to Practice
        </button>
      </div>
    )
  }

  // ── Loading ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className={styles.centred}>
        <div className={styles.spinner} />
        <span className={styles.loadingText}>Loading questions…</span>
      </div>
    )
  }

  const sq             = currentQuestion        // SessionQuestionResponse
  const question       = sq?.question ?? null   // QuestionResponse
  const isMarked       = sq?.marked ?? false
  const selectedAnswer = sq ? (localAnswers[question?.id]?.answer ?? sq.existingAnswer ?? null) : null
  const unanswered     = total - answeredCount

  function handleSubmitClick() {
    if (unanswered > 0) {
      setConfirmEnd(true)
    } else {
      finishSession()
    }
  }

  return (
    <div className={styles.page}>

      {/* ── Top strip: progress + timer + end button ───────────── */}
      <div className={styles.topStrip}>
        <div className={styles.topLeft}>
          <div className={styles.progressWrap}>
            <div
              className={styles.progressFill}
              style={{ width: `${total > 0 ? (answeredCount / total) * 100 : 0}%` }}
            />
          </div>
          <span className={styles.progressLabel}>
            {answeredCount} / {total} answered
            {markedCount > 0 && <span className={styles.markedBadge}> · {markedCount} 🔖</span>}
          </span>
        </div>
        <button
          className={styles.endBtn}
          onClick={() => navigate('/practice')}
          title="Exit session"
        >
          ✕ Exit
        </button>
      </div>

      {/* ── Toolbar (calculator + reference) ──────────────────── */}
      <Toolbar phase="question" calculatorOk={question?.calculatorOk ?? true} />

      {/* ── Question area ─────────────────────────────────────── */}
      <div className={styles.content}>
        {question ? (
          <div className={styles.questionWrap}>
            <QuestionCard
              question={question}
              satMode
              selectedAnswer={selectedAnswer}
              onAnswerSelect={selectAnswer}
              isMarked={isMarked}
              onMarkToggle={() => toggleMark(question.id)}
              disabled={false}
            />
          </div>
        ) : (
          <div className={styles.centred}>
            <span className={styles.loadingText}>No questions available.</span>
          </div>
        )}
      </div>

      {/* ── Bottom nav bar ────────────────────────────────────── */}
      <SessionNavBar
        currentIdx={currentIdx}
        total={total}
        isMarked={isMarked}
        onPrev={goPrev}
        onNext={goNext}
        onOpenGrid={() => setGridOpen(true)}
        onToggleMark={() => question && toggleMark(question.id)}
        onSubmit={handleSubmitClick}
        submitting={submitting}
        answeredCount={answeredCount}
      />

      {/* ── Question grid overlay ─────────────────────────────── */}
      {gridOpen && (
        <QuestionGrid
          questions={questions}
          localAnswers={localAnswers}
          currentIdx={currentIdx}
          onJump={goTo}
          onClose={() => setGridOpen(false)}
        />
      )}

      {/* ── Confirm submit dialog (unanswered questions remain) ── */}
      {confirmEnd && (
        <div className={styles.dialogBackdrop} onClick={() => setConfirmEnd(false)}>
          <div className={styles.dialog} onClick={e => e.stopPropagation()}>
            <div className={styles.dialogTitle}>Submit Session?</div>
            <div className={styles.dialogBody}>
              You have <strong>{unanswered}</strong> unanswered question{unanswered !== 1 ? 's' : ''}.
              Unanswered questions will be marked incorrect.
            </div>
            <div className={styles.dialogActions}>
              <button className={styles.dialogCancel} onClick={() => setConfirmEnd(false)}>
                Go Back
              </button>
              <button className={styles.dialogConfirm} onClick={() => { setConfirmEnd(false); finishSession() }}>
                Submit Anyway
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
