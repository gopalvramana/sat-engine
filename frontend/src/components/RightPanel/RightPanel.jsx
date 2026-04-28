import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import styles from './RightPanel.module.css'

/* ── Dummy "next up" sessions (placeholder until personalised plans land) ── */
const UPCOMING = [
  { type: 'Review Lab',    topic: 'Nonlinear Functions',    done: 0, total: 5  },
  { type: 'Study Session', topic: 'Problem Solving & Data', done: 0, total: 10 },
  { type: 'Study Session', topic: 'Algebra',                done: 1, total: 12 },
  { type: 'Study Session', topic: 'Information & Ideas',    done: 4, total: 10 },
]

/* ── Helpers ── */
function fmtDate(isoStr) {
  if (!isoStr) return ''
  try {
    return new Date(isoStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch { return '' }
}

function fmtSessionType(type, section) {
  if (!type && !section) return 'Session'
  if (type === 'practice_test') return 'Practice Test'
  if (type === 'study')         return section === 'math' ? 'Math' : 'R&W'
  return type ?? section ?? 'Session'
}

/* ── Stat mini-cell ── */
function StatCell({ label, value }) {
  return (
    <div className={styles.statCell}>
      <div className={styles.statVal}>{value ?? '—'}</div>
      <div className={styles.statLabel}>{label}</div>
    </div>
  )
}

/* ── Stat block (24h or all-time) ── */
function StatBlock({ heading, questions, accuracyPct, difficultyPct }) {
  return (
    <div className={styles.statBlock}>
      <div className={styles.blockHeading}>{heading}</div>
      <div className={styles.statRow}>
        <StatCell label="Questions"  value={questions} />
        <StatCell label="Accuracy"   value={accuracyPct   != null ? `${accuracyPct}%`   : '—'} />
        <StatCell label="Difficulty" value={difficultyPct != null ? `${difficultyPct}%` : '—'} />
      </div>
    </div>
  )
}

/* ── Main component ── */
export default function RightPanel() {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetch('/api/analytics')
      .then(r => r.ok ? r.json() : null)
      .then(setData)
      .catch(() => {})
  }, [])

  const l24    = data?.last24h
  const recent = data?.recentSessions ?? []

  return (
    <aside className={styles.panel}>

      {/* ── Last 24 h ── */}
      <StatBlock
        heading="Last 24 hours"
        questions={l24?.questions ?? 0}
        accuracyPct={l24?.accuracyPct}
        difficultyPct={l24?.difficultyPct}
      />

      <div className={styles.divider} />

      {/* ── All-time ── */}
      <StatBlock
        heading="All-time"
        questions={data?.totalQuestions ?? 0}
        accuracyPct={data?.accuracyPct}
        difficultyPct={data?.difficultyPct}
      />

      <div className={styles.divider} />

      {/* ── Next up ── */}
      <div className={styles.sectionHeading}>Next up from your study plan:</div>
      <div className={styles.nextList}>
        {UPCOMING.map((s, i) => (
          <div key={i} className={styles.nextRow}>
            <div className={styles.nextLeft}>
              <span className={styles.nextType}>{s.type}</span>
              <span className={styles.nextTopic}>{s.topic}</span>
            </div>
            <span className={styles.nextProg}>{s.done}/{s.total}</span>
          </div>
        ))}
      </div>

      {/* ── Action buttons ── */}
      <div className={styles.actionGrid}>
        <Link to="/practice" className={`${styles.actionBtn} ${styles.actionPrimary}`}>
          + Study Session
        </Link>
        <Link to="/practice" className={`${styles.actionBtn} ${styles.actionSecondary}`}>
          ↗ Practice Test
        </Link>
        <Link to="/history"  className={`${styles.actionBtn} ${styles.actionSecondary}`}>
          ↺ Review Lab
        </Link>
      </div>

      {/* ── Recently completed ── */}
      {recent.length > 0 && (
        <>
          <div className={styles.divider} />
          <div className={styles.sectionHeading}>Recently completed:</div>
          <div className={styles.recentList}>
            {recent.map(s => (
              <div key={s.sessionId} className={styles.recentRow}>
                <div className={styles.recentLeft}>
                  <span className={styles.recentType}>
                    {fmtSessionType(s.sessionType, s.section)}
                  </span>
                  <span className={styles.recentDate}>{fmtDate(s.startedAt)}</span>
                </div>
                <span className={styles.recentScore}>
                  {s.accuracyPct != null ? `${s.accuracyPct}%` : `${s.correct}/${s.total}`}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

    </aside>
  )
}
