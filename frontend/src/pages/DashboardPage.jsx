import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import { Activity, Target, PieChart, Clock, ChevronRight } from 'lucide-react'
import styles from './DashboardPage.module.css'
import log from '../lib/logger'

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

const DOMAIN_ICONS = {
  algebra:                 'x²',
  advanced_math:           'f(x)',
  problem_solving_data:    '∑',
  geometry_trigonometry:   '△',
  information_ideas:       'Aa',
  craft_structure:         '✒',
  expression_ideas:        '✏',
  standard_english:        'Aa',
}

function labelFor(domain) {
  return DOMAIN_LABELS[domain] ?? domain.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function DashboardPage() {
  const { user } = useAuth()
  const firstName = user?.name?.split(' ')[0] || 'Student'

  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    log.debug('dashboard fetch started')
    fetch('/api/dashboard')
      .then(r => r.ok ? r.json() : null)
      .then(json => {
        if (json) log.info('dashboard loaded', { sessions: json.sessionsCompleted })
        setData(json)
        setLoading(false)
      })
      .catch(error => { log.error('dashboard fetch failed', { error }); setLoading(false) })
  }, [])

  const fmt = (val, suffix = '') =>
    loading ? '…' : val == null ? '—' : `${val}${suffix}`

  const domainEntries   = data?.domainAccuracy ? Object.entries(data.domainAccuracy) : []
  const weakestDomain   = domainEntries.length > 0 ? domainEntries.reduce((a, b) => a[1] <= b[1] ? a : b) : null
  const strongestDomain = domainEntries.length > 0 ? domainEntries.reduce((a, b) => a[1] >= b[1] ? a : b) : null
  const hasWeakDomain        = weakestDomain  && weakestDomain[1]  < 70
  const hasDistinctStrongest = domainEntries.length > 1 && strongestDomain

  function trendBadge(trend) {
    if (!trend || trend.length < 2) return null
    const half = Math.floor(trend.length / 2)
    const avg  = arr => arr.reduce((a, b) => a + b, 0) / arr.length
    const d    = avg(trend.slice(half)) - avg(trend.slice(0, half))
    if (d > 0)  return { label: '↑ Improving', cls: styles.trendUp }
    if (d < 0)  return { label: '↓ Declining', cls: styles.trendDown }
    return { label: '→ Steady', cls: styles.trendFlat }
  }
  const trend = trendBadge(data?.accuracyTrend)

  function accuracyInsight(pct) {
    if (pct == null) return null
    if (hasWeakDomain && pct < 40)     return `Weakest: ${labelFor(weakestDomain[0])} (${weakestDomain[1]}%)`
    if (hasDistinctStrongest && pct > 70) return `Strongest: ${labelFor(strongestDomain[0])} (${strongestDomain[1]}%)`
    if (pct < 40)  return 'Focus on fundamentals'
    if (pct <= 70) return 'On track — keep going'
    return 'Strong — try harder questions'
  }
  function timeInsight(s) {
    if (s == null) return null
    if (s < 15)  return 'Answering very fast'
    if (s <= 90) return 'Good pace'
    return 'Taking longer than usual'
  }

  const STAT_CARDS = [
    {
      Icon: Activity,
      color: '#6366f1',
      bg:    '#eef2ff',
      val:   fmt(data?.sessionsCompleted),
      label: 'Sessions',
      sub:   !loading ? (data?.sessionsCompleted === 0 ? 'Start your first below' : data?.sessionsCompleted <= 5 ? 'Building your habit' : 'Good consistency') : null,
    },
    {
      Icon: Target,
      color: '#d97706',
      bg:    '#fef3c7',
      val:   fmt(data?.questionsAnswered),
      label: 'Questions Practiced',
      sub:   !loading ? (data?.questionsAnswered < 50 ? 'Warming up' : data?.questionsAnswered < 200 ? 'Building volume' : 'Strong reps') : null,
    },
    {
      Icon: PieChart,
      color: '#16a34a',
      bg:    '#dcfce7',
      val:   fmt(data?.accuracyPct, '%'),
      label: 'Accuracy',
      sub:   !loading ? (accuracyInsight(data?.accuracyPct) ?? 'Answer questions to see insight') : null,
      badge: !loading ? trend : null,
    },
    {
      Icon: Clock,
      color: '#0ea5e9',
      bg:    '#e0f2fe',
      val:   loading ? '…' : data?.avgTimeSeconds == null ? '—'
               : data.avgTimeSeconds < 60 ? `${data.avgTimeSeconds}s`
               : `${Math.floor(data.avgTimeSeconds / 60)}m ${data.avgTimeSeconds % 60}s`,
      label: 'Avg Time / Question',
      sub:   !loading ? (timeInsight(data?.avgTimeSeconds) ?? 'Answer questions to see insight') : null,
    },
  ]

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Welcome back, {firstName}</h1>
        <p className={styles.subtitle}>Ready to practice? Pick up where you left off.</p>
      </div>

      {/* ── Stat cards ──────────────────────────────────────── */}
      <div className={styles.statsRow}>
        {STAT_CARDS.map(({ Icon, color, bg, val, label, sub, badge }) => (
          <div key={label} className={styles.statCard}>
            <div className={styles.statTop}>
              <span className={styles.statIconBox} style={{ background: bg, color }}>
                <Icon size={15} strokeWidth={2.2} />
              </span>
              {badge && (
                <span className={`${styles.trendBadge} ${badge.cls}`}>{badge.label}</span>
              )}
            </div>
            <span className={styles.statVal}>{val}</span>
            <span className={styles.statLabel}>{label}</span>
            {sub && <span className={styles.statSub}>{sub}</span>}
          </div>
        ))}
      </div>

      {/* ── CTA ─────────────────────────────────────────────── */}
      {!loading && hasWeakDomain ? (
        <div className={`${styles.ctaCard} ${styles.ctaCardFocused}`}>
          <div className={styles.ctaLeft}>
            <div className={styles.ctaIcon}>🎯</div>
            <div>
              <div className={styles.ctaTitle}>Practice your weakest area</div>
              <div className={styles.ctaSub}>{labelFor(weakestDomain[0])} — {weakestDomain[1]}% accuracy</div>
            </div>
          </div>
          <Link to="/practice" state={{ prefillDomain: weakestDomain[0] }} className={styles.ctaBtn}>
            Start 5 questions
          </Link>
        </div>
      ) : (
        <div className={styles.ctaCard}>
          <div className={styles.ctaLeft}>
            <div className={styles.ctaIcon}>✏</div>
            <div>
              <div className={styles.ctaTitle}>Practice Exams</div>
              <div className={styles.ctaSub}>Choose your topics and difficulty, then start a focused session.</div>
            </div>
          </div>
          <Link to="/practice" className={styles.ctaBtn}>Start Practice</Link>
        </div>
      )}

      {/* ── Domain accuracy ─────────────────────────────────── */}
      {!loading && domainEntries.length > 0 && (
        <div className={styles.section}>
          <h2 className={styles.sectionLabel}>Accuracy by Domain</h2>
          <div className={styles.domainList}>
            {domainEntries.map(([domain, pct]) => {
              const accClass = pct >= 70 ? styles.good : pct >= 50 ? styles.mid : styles.bad
              const pillClass = pct >= 70 ? styles.pillGood : pct >= 50 ? styles.pillMid : styles.pillBad
              return (
                <div key={domain} className={styles.domainRow}>
                  <span className={styles.domainIconBox}>
                    {DOMAIN_ICONS[domain] ?? '?'}
                  </span>
                  <div className={styles.domainMeta}>
                    <span className={styles.domainName}>{labelFor(domain)}</span>
                    <div className={styles.domainBarTrack}>
                      <div
                        className={`${styles.domainBarFill} ${accClass}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                  <span className={`${styles.accPill} ${pillClass}`}>{pct}%</span>
                  <Link
                    to="/practice"
                    state={{ prefillDomain: domain }}
                    className={styles.practiceBtn}
                  >
                    Practice <ChevronRight size={13} />
                  </Link>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* ── Recent sessions ──────────────────────────────────── */}
      <div className={styles.section}>
        <h2 className={styles.sectionLabel}>Recent Sessions</h2>
        {loading ? (
          <div className={styles.skeleton}>
            {[1,2,3].map(i => <div key={i} className={styles.skeletonRow} />)}
          </div>
        ) : !data?.recentSessions?.length ? (
          <div className={styles.emptyState}>No sessions yet. Start your first practice session above.</div>
        ) : (
          <div className={styles.sessionList}>
            {data.recentSessions.map(s => {
              const pillClass = s.accuracyPct >= 70 ? styles.pillGood : s.accuracyPct >= 50 ? styles.pillMid : styles.pillBad
              return (
                <div key={s.id} className={styles.sessionRow}>
                  <span className={styles.sessionIconBox}>
                    {s.section?.includes('math') ? '∑' : '📖'}
                  </span>
                  <div className={styles.sessionMeta}>
                    <span className={styles.sessionSection}>
                      {s.section ? s.section.replace('_', ' & ') : 'Mixed'}
                    </span>
                    <span className={styles.sessionDate}>
                      {s.startedAt ? new Date(s.startedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : ''}
                      {' · '}{s.questionsAnswered} question{s.questionsAnswered !== 1 ? 's' : ''}
                    </span>
                  </div>
                  {s.accuracyPct != null && (
                    <span className={`${styles.accPill} ${pillClass}`}>{s.accuracyPct}%</span>
                  )}
                  <Link to={`/session/${s.id}/summary`} className={styles.reviewBtn}>
                    Review <ChevronRight size={13} />
                  </Link>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
