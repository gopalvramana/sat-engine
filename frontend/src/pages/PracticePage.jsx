import ProgressBar from '../components/ProgressBar/ProgressBar'
import QuestionCard from '../components/QuestionCard/QuestionCard'
import FeedbackPanel from '../components/FeedbackPanel/FeedbackPanel'
import styles from './PracticePage.module.css'

/**
 * The main practice loop.
 *
 * Props come from useSession() in App.jsx:
 *   phase, question, feedback, sessionInfo, submitAnswer, nextQuestion,
 *   endSession, onBack, onHome, studentAnswer, isReviewing
 */
export default function PracticePage({
  phase, question, feedback, sessionInfo,
  submitAnswer, nextQuestion, endSession, onBack, onHome, studentAnswer, isReviewing,
}) {
  const answered = sessionInfo?.questionsAnswered ?? 0
  const correct  = sessionInfo?.correctCount      ?? 0
  const total    = sessionInfo?.totalQuestions    ?? 0

  // During 'question' phase the current Q hasn't been submitted yet → answered+1
  // During 'feedback' phase the current Q was just answered → answered
  const current = phase === 'feedback' ? answered : answered + 1

  return (
    <div className={styles.page}>
      <ProgressBar
        current={current}
        total={total}
        correct={correct}
        onBack={onBack}
        onEnd={endSession}
        isReviewing={isReviewing}
      />

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
