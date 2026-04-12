import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import styles from './DashboardPage.module.css'
import log from '../lib/logger'

export default function DashboardPage() {
  const { user } = useAuth()
  const firstName = user?.name?.split(' ')[0] || 'Student'

  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    log.debug('dashboard fetch started')
    fetch('/api/dashboard')
      .then(r => r.ok ? r.json() : null)
      .then(json => {
        if (json) {
          log.info('dashboard loaded', { sessions: json.sessionsCompleted, questions: json.questionsAnswered, accuracy: json.accuracyPct })
        }
        setData(json)
        setLoading(false)
      })
      .catch(error => {
        log.error('dashboard fetch failed', { error })
        setLoading(false)
      })
  }, [])

  const fmt = (val, suffix = '') =>
    loading ? '…' : val == null ? '—' : `${val}${suffix}`

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Welcome back, {firstName}</h1>
          <p className={styles.subtitle}>Ready to practice? Pick up where you left off.</p>
        </div>
      </div>

      {/* Quick stats */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statVal}>{fmt(data?.sessionsCompleted)}</span>
          <span className={styles.statLabel}>Sessions</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>{fmt(data?.questionsAnswered)}</span>
          <span className={styles.statLabel}>Questions Practiced</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>{fmt(data?.accuracyPct, '%')}</span>
          <span className={styles.statLabel}>Accuracy</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>
            {loading ? '…' : data?.avgTimeSeconds == null ? '—'
              : data.avgTimeSeconds < 60
                ? `${data.avgTimeSeconds}s`
                : `${Math.floor(data.avgTimeSeconds / 60)}m ${data.avgTimeSeconds % 60}s`}
          </span>
          <span className={styles.statLabel}>Avg. Time / Question</span>
        </div>
      </div>

      {/* CTA */}
      <div className={styles.ctaCard}>
        <div className={styles.ctaLeft}>
          <div className={styles.ctaIcon}>✏</div>
          <div>
            <div className={styles.ctaTitle}>Practice Exams</div>
            <div className={styles.ctaSub}>
              Choose your topics and difficulty, then start a focused session.
            </div>
          </div>
        </div>
        <Link to="/practice" className={styles.ctaBtn}>Start Practice →</Link>
      </div>

      {/* Recent sessions */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Recent Sessions</h2>

        {loading ? (
          <div className={styles.emptyState}>Loading…</div>
        ) : !data?.recentSessions?.length ? (
          <div className={styles.emptyState}>
            No sessions yet. Start your first practice session above.
          </div>
        ) : (
          <div className={styles.sessionList}>
            {data.recentSessions.map(s => (
              <div key={s.id} className={styles.sessionRow}>
                <div className={styles.sessionLeft}>
                  <span className={styles.sessionSection}>
                    {s.section ? s.section.replace('_', ' & ') : 'Mixed'}
                  </span>
                  <span className={styles.sessionDate}>
                    {s.startedAt ? new Date(s.startedAt).toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric', year: 'numeric'
                    }) : ''}
                  </span>
                </div>
                <div className={styles.sessionRight}>
                  <span className={styles.sessionQuestions}>
                    {s.questionsAnswered} questions
                  </span>
                  <span className={
                    styles.sessionAccuracy + ' ' +
                    (s.accuracyPct >= 70 ? styles.good : s.accuracyPct >= 50 ? styles.mid : styles.bad)
                  }>
                    {s.accuracyPct != null ? `${s.accuracyPct}%` : '—'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
