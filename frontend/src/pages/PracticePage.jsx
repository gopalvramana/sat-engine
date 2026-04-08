import ProgressBar from '../components/ProgressBar/ProgressBar'
import QuestionCard from '../components/QuestionCard/QuestionCard'
import FeedbackPanel from '../components/FeedbackPanel/FeedbackPanel'
import styles from './PracticePage.module.css'

/**
 * The main practice loop.
 *
 * Props come from useSession() in App.jsx:
 *   phase, question, feedback, sessionInfo, submitAnswer, nextQuestion
 */
export default function PracticePage({
  phase, question, feedback, sessionInfo,
  submitAnswer, nextQuestion, studentAnswer,
}) {
  const answered  = sessionInfo?.questionsAnswered ?? 0
  const correct   = sessionInfo?.correctCount      ?? 0
  // Total is tricky without a count API — we show answered count and keep total open
  const total     = answered + (phase === 'question' || phase === 'feedback' ? 1 : 0)

  return (
    <div className={styles.page}>
      <ProgressBar answered={answered} total={total} correct={correct} />

      <div className={styles.content}>
        {phase === 'loading' && (
          <div className={styles.loading}>
            <div className={styles.spinner} />
            <span>Loading…</span>
          </div>
        )}

        {(phase === 'question' || phase === 'feedback') && question && (
          <div className={styles.questionWrap}>
            {/* Left: question + choices (sticky) */}
            <div className={styles.leftCol}>
              <QuestionCard
                question={question}
                onSubmit={submitAnswer}
                disabled={phase === 'feedback' || phase === 'loading'}
                feedback={phase === 'feedback' ? feedback : null}
                studentAnswer={studentAnswer}
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
                />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
