import { useState, useEffect } from 'react'
import styles from './GamificationPanel.module.css'

/* ── Level system ─────────────────────────────────────────────────────────
   XP earned: 5 per question answered, +3 per correct answer
   ──────────────────────────────────────────────────────────────────────── */
const LEVELS = [
  { name: 'Newcomer',  threshold: 0     },
  { name: 'Learner',   threshold: 300   },
  { name: 'Student',   threshold: 700   },
  { name: 'Achiever',  threshold: 1500  },
  { name: 'Scholar',   threshold: 3000  },
  { name: 'Expert',    threshold: 5500  },
  { name: 'Veteran',   threshold: 9000  },
  { name: 'Master',    threshold: 13500 },
  { name: 'Champion',  threshold: 20000 },
  { name: 'Legend',    threshold: 30000 },
]

function computeLevel(xp) {
  let idx = 0
  for (let i = 0; i < LEVELS.length; i++) {
    if (xp >= LEVELS[i].threshold) idx = i
    else break
  }
  const next = LEVELS[idx + 1] ?? { threshold: LEVELS[idx].threshold + 10000, name: 'MAX' }
  const start = LEVELS[idx].threshold
  const current = xp - start
  const needed  = next.threshold - start
  return {
    level:   idx + 1,
    name:    LEVELS[idx].name,
    current,
    needed,
    pct: Math.round(current / needed * 100),
  }
}

function computeXp(totalQ, accuracyPct) {
  const q = totalQ ?? 0
  const acc = accuracyPct ?? 0
  const correct = Math.round(q * acc / 100)
  return q * 5 + correct * 3
}

/* ── Score estimate ────────────────────────────────────────────────────── */
function estimateScore(totalQ, accuracyPct) {
  if (!totalQ || totalQ < 5) return null
  const acc = (accuracyPct ?? 0) / 100
  // 800 floor + up to 800 bonus, accuracy-weighted + volume bonus
  const vol  = Math.min(1, totalQ / 500)
  const raw  = 800 + 800 * (acc * 0.75 + vol * 0.25)
  return Math.round(raw / 10) * 10   // round to nearest 10
}

/* ── Streak week dots ──────────────────────────────────────────────────── */
const DAY_LETTERS = ['M','T','W','T','F','S','S']
// Dummy streak: last 12 days active (except Sat/Sun of previous week as rest days)
const DUMMY_STREAK_ACTIVE = [true, true, true, true, true, false, false]
  .map((_, i, arr) => arr[i])
// Override with today and preceding 4 days active, rest TBD
function buildWeekDots() {
  const today = new Date().getDay() // 0=Sun
  const todayIdx = today === 0 ? 6 : today - 1 // 0=Mon
  return DAY_LETTERS.map((l, i) => ({
    letter: l,
    active: i <= todayIdx && (i < 5 || todayIdx >= 5), // weekdays always active if before today
    isToday: i === todayIdx,
  }))
}

/* ── Badge rarity config ───────────────────────────────────────────────── */
const RARITY = {
  common:    { ring: '#94a3b8', bg: '#f8fafc', glow: '0 0 0 3px rgba(148,163,184,0.28)', label: 'Common'    },
  rare:      { ring: '#2563eb', bg: '#eff6ff', glow: '0 0 0 3px rgba(37,99,235,0.28)',   label: 'Rare'      },
  epic:      { ring: '#7c3aed', bg: '#f5f3ff', glow: '0 0 0 3px rgba(124,58,237,0.28)',  label: 'Epic'      },
  legendary: { ring: '#d97706', bg: '#fffbeb', glow: '0 0 0 4px rgba(217,119,6,0.32)',   label: 'Legendary' },
}

/* ── Badges ────────────────────────────────────────────────────────────── */
const BADGES = [
  // Common ─────────────────────────────────────────────────────────────────
  { emoji: '🚀', label: 'First Launch',   desc: 'Answered your very first question',   rarity: 'common',    earned: true  },
  // Rare ───────────────────────────────────────────────────────────────────
  { emoji: '💯', label: 'Perfect 10',     desc: '10 correct answers in a row',         rarity: 'rare',      earned: true  },
  { emoji: '⚡', label: 'Quick Draw',     desc: 'Average under 45s per question',      rarity: 'rare',      earned: true  },
  // Epic ───────────────────────────────────────────────────────────────────
  { emoji: '🔥', label: 'Pyromania',      desc: 'Study 7 days in a row',               rarity: 'epic',      earned: false },
  { emoji: '🧠', label: 'Big Brain',      desc: '90%+ accuracy across any 5 sessions', rarity: 'epic',      earned: false },
  { emoji: '🏛️', label: 'Math Olympian',  desc: '90%+ accuracy in Math',               rarity: 'epic',      earned: false },
  { emoji: '📡', label: 'Word Wizard',    desc: '90%+ accuracy in Reading & Writing',  rarity: 'epic',      earned: false },
  // Legendary ──────────────────────────────────────────────────────────────
  { emoji: '💎', label: 'Diamond Mind',   desc: 'Score estimate above 1500',           rarity: 'legendary', earned: false },
  { emoji: '👑', label: 'SAT Royalty',    desc: 'Ace a full-length practice test',     rarity: 'legendary', earned: false },
]

/* ── Badge tile ─────────────────────────────────────────────────────────── */
function BadgeTile({ b }) {
  const r = RARITY[b.rarity]
  return (
    <div
      className={`${styles.badge} ${b.earned ? styles.badgeEarned : styles.badgeLocked}`}
      style={b.earned ? { background: r.bg, borderColor: r.ring, boxShadow: r.glow } : {}}
      title={`${r.label} · ${b.label}: ${b.desc}`}
    >
      <span className={styles.badgeEmoji}>{b.emoji}</span>
      {!b.earned && <span className={styles.badgeLockDot}>🔒</span>}
    </div>
  )
}

/* ── Component ─────────────────────────────────────────────────────────── */
export default function GamificationPanel() {
  const [analytics, setAnalytics] = useState(null)

  useEffect(() => {
    fetch('/api/analytics')
      .then(r => r.ok ? r.json() : null)
      .then(setAnalytics)
      .catch(() => {})
  }, [])

  // Derived values
  const totalQ    = analytics?.totalQuestions ?? 0
  const accuracy  = analytics?.accuracyPct ?? 0
  const xp        = computeXp(totalQ, accuracy)
  const lvl       = computeLevel(xp)
  const score     = estimateScore(totalQ, accuracy)

  // Today's questions from daily activity
  const todayStr  = new Date().toISOString().slice(0, 10)
  const todayQ    = analytics?.dailyActivity?.find(d => d.date === todayStr)?.questions ?? 0
  const goalQ     = 20
  const goalPct   = Math.min(100, Math.round(todayQ / goalQ * 100))

  const weekDots   = buildWeekDots()
  const earnedCount = BADGES.filter(b => b.earned).length
  const nextLocked  = BADGES.find(b => !b.earned)

  return (
    <aside className={styles.panel}>

      {/* ── Level + XP ── */}
      <div className={styles.levelSection}>
        <div className={styles.levelTopRow}>
          <span className={styles.levelChip}>LV {lvl.level}</span>
          <span className={styles.totalXp}>{xp.toLocaleString()} XP</span>
        </div>
        <div className={styles.levelName}>{lvl.name}</div>
        <div className={styles.xpTrack}>
          <div className={styles.xpFill} style={{ width: `${lvl.pct}%` }} />
        </div>
        <div className={styles.xpCaption}>
          {lvl.current.toLocaleString()} / {lvl.needed.toLocaleString()} to next level
        </div>
      </div>

      <div className={styles.divider} />

      {/* ── Streak ── */}
      <div className={styles.streakSection}>
        <div className={styles.streakHeader}>
          <span className={styles.streakFlame}>🔥</span>
          <div>
            <span className={styles.streakNum}>12</span>
            <span className={styles.streakLabel}> day streak</span>
          </div>
        </div>
        <div className={styles.weekDots}>
          {weekDots.map((d, i) => (
            <div key={i} className={styles.dotCol}>
              <div
                className={`${styles.dot} ${d.active ? styles.dotActive : styles.dotInactive} ${d.isToday ? styles.dotToday : ''}`}
              />
              <span className={styles.dotLabel}>{d.letter}</span>
            </div>
          ))}
        </div>
      </div>

      <div className={styles.divider} />

      {/* ── Daily goal ── */}
      <div className={styles.goalSection}>
        <div className={styles.sectionHeading}>
          Today's Goal
          <span className={styles.goalXpTag}>+50 XP</span>
        </div>
        <div className={styles.goalCount}>
          <span className={styles.goalDone}>{todayQ}</span>
          <span className={styles.goalOf}> / {goalQ} questions</span>
        </div>
        <div className={styles.goalTrack}>
          <div
            className={`${styles.goalFill} ${goalPct >= 100 ? styles.goalComplete : ''}`}
            style={{ width: `${goalPct}%` }}
          />
        </div>
        {goalPct >= 100 && <div className={styles.goalDoneMsg}>🎉 Goal reached!</div>}
      </div>

      <div className={styles.divider} />

      {/* ── Badges ── */}
      <div className={styles.badgesSection}>
        <div className={styles.sectionHeading}>
          Badges
          <span className={styles.badgeCount}>{earnedCount}/{BADGES.length}</span>
        </div>

        {/* 3-column grid: earned (colored) + locked (gray) */}
        <div className={styles.badgeGrid}>
          {BADGES.map(b => <BadgeTile key={b.label} b={b} />)}
        </div>

        {/* Next badge to unlock — tinted with its rarity color */}
        {nextLocked && (
          <div
            className={styles.nextBadge}
            style={{ borderColor: RARITY[nextLocked.rarity].ring + '55' }}
          >
            <span className={styles.nextBadgeEmoji}>{nextLocked.emoji}</span>
            <div className={styles.nextBadgeInfo}>
              <span
                className={styles.nextBadgeName}
                style={{ color: RARITY[nextLocked.rarity].ring }}
              >
                {nextLocked.label}
              </span>
              <span className={styles.nextBadgeDesc}>{nextLocked.desc}</span>
            </div>
          </div>
        )}
      </div>

      <div className={styles.divider} />

      {/* ── Score estimate ── */}
      <div className={styles.scoreSection}>
        <div className={styles.sectionHeading}>Est. SAT Score</div>
        {score != null ? (
          <>
            <div className={styles.scoreNum}>{score.toLocaleString()}</div>
            <div className={styles.scoreSub}>
              <span className={styles.scoreDelta}>▲ +35 pts this week</span>
            </div>
            <div className={styles.scoreBar}>
              <div className={styles.scoreBarFill} style={{ width: `${Math.round((score - 800) / 8)}%` }} />
            </div>
            <div className={styles.scoreRange}>
              <span>800</span>
              <span>1600</span>
            </div>
          </>
        ) : (
          <div className={styles.scoreBlank}>
            Answer a few more questions to unlock your score estimate.
          </div>
        )}
      </div>

    </aside>
  )
}
