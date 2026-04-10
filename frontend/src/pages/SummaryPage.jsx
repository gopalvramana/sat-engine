import MathText from '../components/MathText/MathText'
import { formatTime } from '../hooks/useTimer'
import styles from './SummaryPage.module.css'

/**
 * Session summary shown when all questions are exhausted.
 *
 * Props:
 *   sessionInfo — SessionResponse { questionsAnswered, correctCount, ... }
 *   history     — [{question: QuestionResponse, feedback: AnswerFeedback}]
 *   onRestart   — called when student clicks "Practice Again"
 */
export default function SummaryPage({ sessionInfo, history, onRestart }) {
  const total   = sessionInfo?.questionsAnswered ?? history.length
  const correct = sessionInfo?.correctCount      ?? history.filter(h => h.feedback.isCorrect).length
  const pct     = total > 0 ? Math.round((correct / total) * 100) : 0

  // Total time across session
  const totalSeconds = history.reduce((sum, h) => sum + (h.timeTaken ?? 0), 0)

  // Domain breakdown
  const domains = {}
  history.forEach(({ question, feedback }) => {
    const d = question.domain
    if (!domains[d]) domains[d] = { correct: 0, total: 0, label: domainLabel(d) }
    domains[d].total++
    if (feedback.isCorrect) domains[d].correct++
  })

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        {/* ── Score ─────────────────────────────────────────── */}
        <div className={styles.scoreCard}>
          <div className={styles.scoreCircle}>
            <span className={styles.scorePct}>{pct}%</span>
            <span className={styles.scoreLabel}>score</span>
          </div>
          <div className={styles.scoreDetail}>
            <div className={styles.scoreTitle}>Session Complete!</div>
            <div className={styles.scoreSub}>
              You got <strong>{correct}</strong> out of <strong>{total}</strong> questions correct.
            </div>
            {totalSeconds > 0 && (
              <div className={styles.scoreTiming}>
                ⏱ Total time: <strong>{formatTime(totalSeconds)}</strong>
                {total > 0 && <span className={styles.avgTime}> · avg {formatTime(Math.round(totalSeconds / total))} / question</span>}
              </div>
            )}
          </div>
        </div>

        {/* ── Domain breakdown ──────────────────────────────── */}
        {Object.keys(domains).length > 0 && (
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>By Domain</h3>
            {Object.entries(domains).map(([key, d]) => {
              const dpct = Math.round((d.correct / d.total) * 100)
              return (
                <div key={key} className={styles.domainRow}>
                  <div className={styles.domainName}>{d.label}</div>
                  <div className={styles.domainBar}>
                    <div className={styles.domainFill} style={{ width: `${dpct}%` }} />
                  </div>
                  <div className={styles.domainScore}>{d.correct}/{d.total}</div>
                </div>
              )
            })}
          </div>
        )}

        {/* ── Question review list ──────────────────────────── */}
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Review</h3>
          <div className={styles.reviewList}>
            {history.map(({ question, feedback, timeTaken }, i) => (
              <div key={i} className={`${styles.reviewItem} ${feedback.isCorrect ? styles.reviewCorrect : styles.reviewWrong}`}>
                <span className={styles.reviewIcon}>{feedback.isCorrect ? '✓' : '✗'}</span>
                <div className={styles.reviewBody}>
                  <div className={styles.reviewMeta}>
                    <div className={styles.reviewDomain}>{domainLabel(question.domain)}</div>
                    {timeTaken > 0 && (
                      <span className={styles.reviewTime}>⏱ {formatTime(timeTaken)}</span>
                    )}
                  </div>
                  <MathText
                    text={question.questionStem?.slice(0, 120) + (question.questionStem?.length > 120 ? '…' : '')}
                    as="div"
                    className={styles.reviewStem}
                  />
                  {!feedback.isCorrect && (
                    <div className={styles.reviewAnswer}>
                      Correct answer: <strong>{feedback.correctAnswer}</strong>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.restartRow}>
          <button className={styles.restartBtn} onClick={onRestart}>
            Practice Again
          </button>
        </div>
      </div>
    </div>
  )
}

function domainLabel(d) {
  const M = {
    algebra: 'Algebra', advanced_math: 'Advanced Math',
    problem_solving_data: 'Problem Solving & Data',
    geometry_trigonometry: 'Geometry & Trig',
    information_ideas: 'Information & Ideas',
    craft_structure: 'Craft & Structure',
    expression_ideas: 'Expression of Ideas',
    standard_english: 'Standard English',
  }
  return M[d] || d || 'Other'
}
