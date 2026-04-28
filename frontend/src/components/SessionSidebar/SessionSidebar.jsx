import { useState } from 'react'
import AchievementCard from '../AchievementCard/AchievementCard'
import styles from './SessionSidebar.module.css'

/**
 * Left panel shown during session review.
 * Computes stats from the answers array (already fetched by SessionReviewPage).
 * TODO: wire achievements to user_achievements API once DB tables are created.
 */
export default function SessionSidebar({ answers = [] }) {
  const [stars, setStars] = useState(0)
  const [chatInput, setChatInput] = useState('')

  // ── Compute session stats from answers ──────────────────────
  const total    = answers.length
  const correct  = answers.filter(a => a.isCorrect).length
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0
  const avgTime  = total > 0
    ? Math.round(answers.reduce((s, a) => s + (a.timeSpentSeconds || 0), 0) / total)
    : 0

  // ── Rule-based achievements (placeholder until user_achievements table) ──
  const achievements = []
  if (correct >= 2) {
    achievements.push({
      id: 'dragon',
      icon: '🐉', count: correct, name: 'correct', sticker: 'Keep Slaying!',
      stickerVariant: 'green', tailIcon: '⚔️', variant: 'indigo',
    })
  }
  const isWeekend = [0, 6].includes(new Date().getDay())
  if (isWeekend || total >= 10) {
    achievements.push({
      id: 'warrior',
      icon: '🥷', count: `${Math.ceil(total / 10)}×`, name: 'weekend warrior',
      sticker: 'Fearless', stickerVariant: 'amber', tailIcon: '⚡', variant: 'amber',
    })
  }

  // ── Accuracy ring (SVG arc) ──────────────────────────────────
  const R   = 17
  const circ = 2 * Math.PI * R
  const offset = circ * (1 - accuracy / 100)

  return (
    <aside className={styles.sidebar}>

      {/* Stats */}
      <div className={styles.statsSection}>
        <div className={styles.sectionLabel}>Session Summary</div>
        <div className={styles.statsRow}>

          <div className={`${styles.statCard} ${styles.statAcc}`}>
            <div className={styles.ring}>
              <svg width="42" height="42" viewBox="0 0 42 42">
                <circle cx="21" cy="21" r={R} fill="none" stroke="#f1f5f9" strokeWidth="3.5"/>
                <circle
                  cx="21" cy="21" r={R} fill="none"
                  stroke="url(#accGrad)" strokeWidth="3.5"
                  strokeDasharray={circ}
                  strokeDashoffset={offset}
                  strokeLinecap="round"
                  transform="rotate(-90 21 21)"
                />
                <defs>
                  <linearGradient id="accGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#f43f5e"/>
                    <stop offset="100%" stopColor="#f59e0b"/>
                  </linearGradient>
                </defs>
              </svg>
              <div className={styles.ringVal}>{accuracy}%</div>
            </div>
            <div className={styles.statLabel}>accuracy</div>
          </div>

          <div className={`${styles.statCard} ${styles.statQs}`}>
            <div className={styles.statVal}>{total}</div>
            <div className={styles.statLabel}>questions</div>
          </div>

          <div className={`${styles.statCard} ${styles.statSpd}`}>
            <div className={styles.statVal}>{avgTime}s</div>
            <div className={styles.statLabel}>per q</div>
          </div>

        </div>
      </div>

      {/* Star feedback */}
      <div className={styles.feedbackSection}>
        <div className={styles.sectionLabel}>Your Feedback</div>
        <div className={styles.feedbackQ}>How was your experience?</div>
        <div className={styles.stars}>
          {[1,2,3,4,5].map(n => (
            <button
              key={n}
              className={`${styles.star} ${n <= stars ? styles.starOn : styles.starOff}`}
              onClick={() => setStars(n)}
              aria-label={`${n} star${n !== 1 ? 's' : ''}`}
            >★</button>
          ))}
        </div>
      </div>

      {/* Achievements */}
      {achievements.length > 0 && (
        <div className={styles.achievementsSection}>
          <div className={styles.sectionLabel}>Achievements Unlocked</div>
          <div className={styles.achList}>
            {achievements.map(a => (
              <AchievementCard key={a.id} {...a} />
            ))}
          </div>
        </div>
      )}

      {/* AI Chat */}
      <div className={styles.chatArea}>
        <button className={styles.explainBtn}>✦ Explain in simpler terms</button>
        <div className={styles.chatRow}>
          <input
            type="text"
            className={styles.chatInput}
            placeholder="Ask anything about this question…"
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
          />
          <button className={styles.sendBtn} aria-label="Send">↑</button>
        </div>
      </div>

    </aside>
  )
}
