import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import styles from './DashboardPage.module.css'
import log from '../lib/logger'

/* ── Domain label map ───────────────────────────────────────────── */
const DOMAIN_LABELS = {
  algebra:                 'Algebra',
  advanced_math:           'Advanced Math',
  problem_solving_data:    'Problem Solving & Data',
  geometry_trigonometry:   'Geometry & Trig',
  information_ideas:       'Information & Ideas',
  craft_structure:         'Craft & Structure',
  expression_ideas:        'Expression of Ideas',
  standard_english:        'Standard English',
}
function labelFor(domain) {
  return DOMAIN_LABELS[domain] ?? domain.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

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

  // Derive weakest / strongest domain from accuracy map
  const domainEntries = data?.domainAccuracy ? Object.entries(data.domainAccuracy) : []
  const weakestDomain  = domainEntries.length > 0
    ? domainEntries.reduce((a, b) => a[1] <= b[1] ? a : b)
    : null
  const strongestDomain = domainEntries.length > 0
    ? domainEntries.reduce((a, b) => a[1] >= b[1] ? a : b)
    : null

  // Interpretation helpers for stat cards
  function accuracyInsight(pct) {
    if (pct == null) return null
    if (weakestDomain && pct < 40)
      return `Weakest: ${labelFor(weakestDomain[0])} (${weakestDomain[1]}%) — start here`
    if (strongestDomain && pct > 70)
      return `Strongest: ${labelFor(strongestDomain[0])} (${strongestDomain[1]}%)`
    if (pct < 40)  return 'Focus on fundamentals'
    if (pct <= 70) return 'On track — keep going'
    return 'Strong — try harder questions'
  }
  function timeInsight(s) {
    if (s == null) return null
    if (s < 15)  return 'Answering very fast — slow down to improve accuracy'
    if (s <= 90) return 'Good pace — keep it up'
    return 'Taking longer than usual — aim for 30–90s per question'
  }
  function sessionsInsight(n) {
    if (n === 0) return 'Start your first session below'
    if (n <= 5)  return 'Building your habit'
    return 'Good consistency'
  }
  function questionsInsight(n) {
    if (n === 0) return 'No questions yet'
    if (n < 50)  return 'Warming up'
    if (n < 200) return 'Building volume'
    return 'Strong reps — keep it up'
  }

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
          {!loading && <span className={styles.statInsight}>{sessionsInsight(data?.sessionsCompleted ?? 0)}</span>}
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>{fmt(data?.questionsAnswered)}</span>
          <span className={styles.statLabel}>Questions Practiced</span>
          {!loading && <span className={styles.statInsight}>{questionsInsight(data?.questionsAnswered ?? 0)}</span>}
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>{fmt(data?.accuracyPct, '%')}</span>
          <span className={styles.statLabel}>Accuracy</span>
          {!loading && <span className={styles.statInsight}>{accuracyInsight(data?.accuracyPct) ?? 'Answer questions to see insight'}</span>}
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>
            {loading ? '…' : data?.avgTimeSeconds == null ? '—'
              : data.avgTimeSeconds < 60
                ? `${data.avgTimeSeconds}s`
                : `${Math.floor(data.avgTimeSeconds / 60)}m ${data.avgTimeSeconds % 60}s`}
          </span>
          <span className={styles.statLabel}>Avg. Time / Question</span>
          {!loading && <span className={styles.statInsight}>{timeInsight(data?.avgTimeSeconds) ?? 'Answer questions to see insight'}</span>}
        </div>
      </div>

      {/* CTA — personalized when domain data exists, generic otherwise */}
      {!loading && weakestDomain ? (
        <div className={`${styles.ctaCard} ${styles.ctaCardFocused}`}>
          <div className={styles.ctaLeft}>
            <div className={styles.ctaIcon}>🎯</div>
            <div>
              <div className={styles.ctaTitle}>Practice your weakest area</div>
              <div className={styles.ctaSub}>
                {labelFor(weakestDomain[0])} — {weakestDomain[1]}% accuracy
              </div>
            </div>
          </div>
          <Link
            to="/practice"
            state={{ prefillDomain: weakestDomain[0] }}
            className={styles.ctaBtn}
          >
            Start 5 questions →
          </Link>
        </div>
      ) : (
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
      )}

      {/* Domain accuracy */}
      {!loading && data?.domainAccuracy && Object.keys(data.domainAccuracy).length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Accuracy by Domain</h2>
          <div className={styles.domainGrid}>
            {Object.entries(data.domainAccuracy).map(([domain, pct]) => (
              <div key={domain} className={styles.domainRow}>
                <div className={styles.domainMeta}>
                  <span className={styles.domainName}>
                    {domain.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                  <span className={`${styles.domainPct} ${pct >= 70 ? styles.good : pct >= 50 ? styles.mid : styles.bad}`}>
                    {pct}%
                  </span>
                </div>
                <div className={styles.domainBarTrack}>
                  <div
                    className={`${styles.domainBarFill} ${pct >= 70 ? styles.barGood : pct >= 50 ? styles.barMid : styles.barBad}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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
