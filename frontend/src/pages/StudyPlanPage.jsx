import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as api from '../api/client'
import styles from './StudyPlanPage.module.css'

/* ── Helpers ───────────────────────────────────────────────────── */
function weekStart() {
  // Monday of the current week
  const d = new Date()
  const day = d.getDay() // 0=Sun
  const diff = day === 0 ? -6 : 1 - day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function addDays(base, n) {
  const d = new Date(base)
  d.setDate(d.getDate() + n)
  return d
}

function isToday(d) {
  const t = new Date()
  return d.getDate() === t.getDate() &&
         d.getMonth() === t.getMonth() &&
         d.getFullYear() === t.getFullYear()
}

function isPast(d) {
  const t = new Date(); t.setHours(0,0,0,0)
  return d < t
}

function fmtDay(d) {
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function fmtRange(mon, sun) {
  return `${mon.toLocaleDateString('en-US',{month:'short',day:'numeric'})} – ${sun.toLocaleDateString('en-US',{month:'short',day:'numeric'})}`
}

/* ── Dummy plan data (keyed by day index 0=Mon … 6=Sun) ─────────── */
const PLAN = [
  // Mon
  [
    { type: 'Study Session', topic: 'Algebra',                 done: 8,  total: 12 },
    { type: 'Study Session', topic: 'Advanced Math',           done: 12, total: 12 },
  ],
  // Tue
  [
    { type: 'Review Lab',    topic: 'Algebra',                 done: 5,  total: 5  },
    { type: 'Study Session', topic: 'Craft and Structure',     done: 4,  total: 10 },
    { type: 'Study Session', topic: 'Information and Ideas',   done: 0,  total: 10 },
  ],
  // Wed
  [
    { type: 'Review Lab',    topic: 'Nonlinear Functions',     done: 0,  total: 5  },
    { type: 'Study Session', topic: 'Expression of Ideas',     done: 0,  total: 5  },
    { type: 'Study Session', topic: 'Craft and Structure',     done: 0,  total: 10 },
    { type: 'Study Session', topic: 'Information and Ideas',   done: 0,  total: 10 },
  ],
  // Thu
  [
    { type: 'Study Session', topic: 'Algebra',                 done: 1,  total: 12 },
    { type: 'Study Session', topic: 'Standard English',        done: 0,  total: 5  },
    { type: 'Study Session', topic: 'Problem Solving & Data',  done: 0,  total: 10 },
    { type: 'Review Lab',    topic: 'Nonlinear Functions',     done: 0,  total: 5  },
  ],
  // Fri
  [
    { type: 'Study Session', topic: 'Information and Ideas',   done: 0,  total: 10 },
    { type: 'Review Lab',    topic: 'Nonlinear Functions',     done: 0,  total: 5  },
    { type: 'Study Session', topic: 'Craft and Structure',     done: 0,  total: 10 },
    { type: 'Study Session', topic: 'Expression of Ideas',     done: 0,  total: 5  },
  ],
  // Sat
  [
    { type: 'Practice Test', topic: 'Full',                    done: 0,  total: 98 },
    { type: 'Practice Test', topic: 'Half · Math · Medium',    done: 14, total: 98, pctOverride: 14 },
  ],
  // Sun
  [
    { type: 'Review Lab',    topic: 'Advanced Math',           done: 0,  total: 5  },
    { type: 'Study Session', topic: 'Algebra',                 done: 0,  total: 12 },
  ],
]

const DAY_NAMES = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

/* ── Type → accent ──────────────────────────────────────────────── */
function typeAccent(type) {
  if (type === 'Practice Test') return styles.typeTest
  if (type === 'Review Lab')    return styles.typeReview
  return styles.typeStudy
}

function topicAccent(type) {
  if (type === 'Practice Test') return styles.topicTest
  if (type === 'Review Lab')    return styles.topicReview
  return ''
}

/* ── Single session row ─────────────────────────────────────────── */
function SessionRow({ s }) {
  const done = s.done >= s.total && s.total > 0
  const pct  = s.pctOverride ?? (s.total ? Math.round(s.done / s.total * 100) : 0)
  return (
    <div className={`${styles.sessionRow} ${done ? styles.sessionRowDone : ''}`}>
      <div className={styles.sessionLeft}>
        <span className={`${styles.sessionType} ${typeAccent(s.type)}`}>{s.type}</span>
        <span className={`${styles.sessionTopic} ${topicAccent(s.type)}`}>{s.topic}</span>
      </div>
      <div className={styles.sessionRight}>
        {done
          ? <span className={styles.doneCheck}>✓</span>
          : s.pctOverride != null
            ? <span className={styles.progressBadge}>{pct}%&nbsp;✓</span>
            : <span className={styles.progressText}>{s.done}/{s.total}</span>
        }
      </div>
    </div>
  )
}

/* ── Day card ───────────────────────────────────────────────────── */
function DayCard({ date, sessions }) {
  const today  = isToday(date)
  const past   = isPast(date) && !today
  const fmted  = fmtDay(date)
  return (
    <div className={`${styles.dayCard} ${today ? styles.dayCardToday : ''} ${past ? styles.dayCardPast : ''}`}>
      <div className={styles.dayHeader}>
        <span className={`${styles.dayLabel} ${today ? styles.dayLabelToday : ''}`}>
          {fmted}
        </span>
        {today && <span className={styles.todayPill}>Today</span>}
      </div>
      <div className={styles.sessionList}>
        {sessions.map((s, i) => <SessionRow key={i} s={s} />)}
      </div>
    </div>
  )
}

/* ── Page ────────────────────────────────────────────────────────── */
export default function StudyPlanPage() {
  const navigate = useNavigate()
  const mon  = weekStart()
  const sun  = addDays(mon, 6)
  const days = DAY_NAMES.map((name, i) => ({ name, date: addDays(mon, i), sessions: PLAN[i] }))

  // Resume detection — check for an active session on mount
  const [activeSession, setActiveSession] = useState(null)
  useEffect(() => {
    api.getActiveSession()
      .then(sess => { if (sess) setActiveSession(sess) })
      .catch(() => {})
  }, [])

  return (
    <div className={styles.page}>

      {/* ── Resume banner ── */}
      {activeSession && (
        <div className={styles.resumeBanner}>
          <span className={styles.resumeIcon}>📝</span>
          <div className={styles.resumeText}>
            <strong>Unfinished session</strong>
            <span>{activeSession.questionsAnswered} of {activeSession.totalQuestions} questions answered</span>
          </div>
          <button
            className={styles.resumeBtn}
            onClick={() => navigate(`/session/${activeSession.id}`)}
          >
            Resume →
          </button>
          <button
            className={styles.resumeDismiss}
            onClick={() => setActiveSession(null)}
            aria-label="Dismiss"
          >✕</button>
        </div>
      )}

      {/* ── Top bar ── */}
      <div className={styles.topBar}>
        <h1 className={styles.weekRange}>{fmtRange(mon, sun)}</h1>
        <div className={styles.notice}>
          🚧&nbsp; Sample plan — personalised plans coming soon
        </div>
      </div>

      {/* ── 2-column calendar grid ── */}
      <div className={styles.calGrid}>
        {days.map(d => (
          <DayCard key={d.name} date={d.date} sessions={d.sessions} />
        ))}
      </div>
    </div>
  )
}
