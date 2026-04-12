import { useLocation, useNavigate } from 'react-router-dom'
import { formatTime } from '../hooks/useTimer'
import styles from './SummaryPage.module.css'

export default function SummaryPage() {
  const location = useLocation()
  const navigate  = useNavigate()

  // History and session info are passed via router state from PracticePage
  // On hard refresh the state is lost — we show what we can from sessionInfo
  const history     = location.state?.history     ?? []
  const sessionInfo = location.state?.sessionInfo ?? null

  const total   = sessionInfo?.questionsAnswered ?? history.length
  const correct = sessionInfo?.correctCount ?? history.filter(h => h.feedback?.isCorrect).length
  const pct     = total > 0 ? Math.round((correct / total) * 100) : 0
  const totalSeconds = history.reduce((sum, h) => sum + (h.timeTaken ?? 0), 0)

  // Group by skill (fall back to domain label if skill not set)
  const skills = {}
  history.forEach(({ question, feedback }) => {
    const key = question.skill || domainLabel(question.domain)
    if (!skills[key]) skills[key] = { correct: 0, total: 0 }
    skills[key].total++
    if (feedback.isCorrect) skills[key].correct++
  })

  const skillEntries = Object.entries(skills).sort(([, a], [, b]) => {
    const aPct = a.correct / a.total
    const bPct = b.correct / b.total
    if (bPct !== aPct) return bPct - aPct
    return 0
  })

  return (
    <div className={styles.page}>
      <div className={styles.inner}>

        {/* ── Score card ─────────────────────────────────── */}
        <div className={styles.scoreCard}>
          <div className={styles.scoreCircle}>
            <span className={styles.scorePct}>{pct}%</span>
            <span className={styles.scoreLabel}>score</span>
          </div>
          <div className={styles.scoreDetail}>
            <div className={styles.scoreTitle}>Session Complete!</div>
            <div className={styles.scoreSub}>
              <strong>{correct}</strong> of <strong>{total}</strong> correct
            </div>
            {totalSeconds > 0 && (
              <div className={styles.scoreTiming}>
                ⏱ {formatTime(totalSeconds)}
                {total > 0 && (
                  <span className={styles.avgTime}> · avg {formatTime(Math.round(totalSeconds / total))} / question</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Performance by Skill ───────────────────────── */}
        {skillEntries.length > 0 && (
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Performance by Skill</h3>
            <div className={styles.skillGrid}>
              {skillEntries.map(([skill, data]) => {
                const wrong    = data.total - data.correct
                const fillPct  = Math.round((data.correct / data.total) * 100)
                const allRight = data.correct === data.total
                return (
                  <div key={skill} className={styles.skillCard}>
                    <div className={styles.skillHeader}>
                      <span className={styles.skillName}>{skill}</span>
                      <span className={`${styles.skillScore} ${allRight ? styles.skillScoreGood : styles.skillScoreBad}`}>
                        {data.correct}/{data.total}
                      </span>
                    </div>
                    <div className={styles.skillBar}>
                      <div
                        className={`${styles.skillFill} ${allRight ? styles.skillFillGood : styles.skillFillBad}`}
                        style={{ width: `${fillPct}%` }}
                      />
                    </div>
                    {wrong > 0 && (
                      <div className={styles.skillWrong}>
                        {wrong} question{wrong > 1 ? 's' : ''} incorrect
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        <div className={styles.restartRow}>
          <button className={styles.restartBtn} onClick={() => navigate('/practice')}>
            Practice Again
          </button>
          <button className={styles.homeBtn} onClick={() => navigate('/')}>
            Back to Dashboard
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
