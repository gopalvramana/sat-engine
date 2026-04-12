import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { formatTime } from '../hooks/useTimer'
import styles from './SummaryPage.module.css'

export default function SummaryPage() {
  const location   = useLocation()
  const navigate   = useNavigate()
  const { sessionId } = useParams()

  // ── Mode A: came from PracticePage with router state ──────────────────────
  const stateHistory     = location.state?.history     ?? null
  const stateSessionInfo = location.state?.sessionInfo ?? null
  const hasState = stateHistory !== null

  // ── Mode B: opened from History page — fetch from API ─────────────────────
  const [apiLoading, setApiLoading] = useState(!hasState)
  const [apiError,   setApiError]   = useState(false)
  const [apiAnswers, setApiAnswers] = useState([])   // SessionAnswerDetail[]
  const [apiSession, setApiSession] = useState(null) // SessionResponse

  useEffect(() => {
    if (hasState || !sessionId) return
    Promise.all([
      fetch(`/api/sessions/${sessionId}`).then(r => r.ok ? r.json() : null),
      fetch(`/api/sessions/${sessionId}/answers`).then(r => r.ok ? r.json() : []),
    ])
      .then(([sess, answers]) => {
        if (!sess) { setApiError(true); return }
        setApiSession(sess)
        setApiAnswers(answers)
      })
      .catch(() => setApiError(true))
      .finally(() => setApiLoading(false))
  }, [sessionId, hasState])

  // ── Unify into shared shape ────────────────────────────────────────────────
  // history entries: { question, feedback, timeTaken }
  const history = hasState
    ? stateHistory
    : apiAnswers.map(a => ({
        question: {
          domain: a.domain,
          skill:  a.skill,
        },
        feedback: { isCorrect: a.isCorrect },
        timeTaken: a.timeSpentSeconds ?? 0,
      }))

  const sessionInfo = hasState
    ? stateSessionInfo
    : apiSession
      ? { questionsAnswered: apiSession.questionsAnswered, correctCount: apiSession.correctCount }
      : null

  const total   = sessionInfo?.questionsAnswered ?? history.length
  const correct = sessionInfo?.correctCount ?? history.filter(h => h.feedback?.isCorrect).length
  const pct     = total > 0 ? Math.round((correct / total) * 100) : 0
  const totalSeconds = history.reduce((sum, h) => sum + (h.timeTaken ?? 0), 0)

  // Group by skill
  const skills = {}
  history.forEach(({ question, feedback }) => {
    const key = question.skill || domainLabel(question.domain)
    if (!skills[key]) skills[key] = { correct: 0, total: 0 }
    skills[key].total++
    if (feedback?.isCorrect) skills[key].correct++
  })

  const skillEntries = Object.entries(skills).sort(([, a], [, b]) => {
    const aPct = a.correct / a.total
    const bPct = b.correct / b.total
    return bPct - aPct
  })

  // ── Loading / error states ─────────────────────────────────────────────────
  if (apiLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <div className={styles.loadingMsg}>Loading session…</div>
        </div>
      </div>
    )
  }

  if (apiError) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <div className={styles.errorMsg}>
            Could not load session. It may have been deleted or you don't have access.
          </div>
          <div className={styles.restartRow}>
            <button className={styles.homeBtn} onClick={() => navigate('/history')}>
              Back to History
            </button>
          </div>
        </div>
      </div>
    )
  }

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
            <div className={styles.scoreTitle}>
              {hasState ? 'Session Complete!' : 'Session Review'}
            </div>
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

        {/* ── Per-question review (API mode only) ────────── */}
        {!hasState && apiAnswers.length > 0 && (
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>Question Review</h3>
            <div className={styles.reviewList}>
              {apiAnswers.map((a, i) => (
                <div key={a.questionId} className={`${styles.reviewItem} ${a.isCorrect ? styles.reviewCorrect : styles.reviewWrong}`}>
                  <div className={styles.reviewHeader}>
                    <span className={styles.reviewNum}>Q{i + 1}</span>
                    <span className={`${styles.reviewBadge} ${a.isCorrect ? styles.badgeCorrect : styles.badgeWrong}`}>
                      {a.isCorrect ? '✓ Correct' : '✗ Incorrect'}
                    </span>
                    {a.timeSpentSeconds != null && (
                      <span className={styles.reviewTime}>{a.timeSpentSeconds}s</span>
                    )}
                  </div>
                  {a.questionStem && (
                    <div className={styles.reviewStem}>{a.questionStem}</div>
                  )}
                  <div className={styles.reviewAnswers}>
                    <span className={styles.reviewAnswerLabel}>Your answer:</span>
                    <span className={a.isCorrect ? styles.reviewAnswerCorrect : styles.reviewAnswerWrong}>
                      {a.studentAnswer ?? '—'}
                    </span>
                    {!a.isCorrect && a.correctAnswer && (
                      <>
                        <span className={styles.reviewAnswerLabel}> · Correct:</span>
                        <span className={styles.reviewAnswerCorrect}> {a.correctAnswer}</span>
                      </>
                    )}
                  </div>
                  {!a.isCorrect && a.explanationShort && (
                    <div className={styles.reviewExplanation}>{a.explanationShort}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Action buttons ─────────────────────────────── */}
        <div className={styles.restartRow}>
          <button className={styles.restartBtn} onClick={() => navigate('/practice')}>
            Practice Again
          </button>
          {hasState ? (
            <button className={styles.homeBtn} onClick={() => navigate('/')}>
              Back to Dashboard
            </button>
          ) : (
            <button className={styles.homeBtn} onClick={() => navigate('/history')}>
              Back to History
            </button>
          )}
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
