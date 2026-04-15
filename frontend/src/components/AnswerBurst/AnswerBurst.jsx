import { useEffect, useState } from 'react'
import styles from './AnswerBurst.module.css'

const CORRECT_STAMPS = ['🎯', '⭐', '🔥', '💡', '🚀', '✨']
const WRONG_MESSAGES = ['You got this 💪', 'Almost there!', 'Review & retry 🔄', 'Keep pushing 🧠']

// 8 directions for scatter dots
const SCATTER_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
const DOT_COLORS = ['#4ade80', '#facc15', '#60a5fa', '#f472b6', '#a78bfa', '#34d399', '#fb923c', '#38bdf8']

export default function AnswerBurst({ isCorrect }) {
  const [visible, setVisible] = useState(false)
  const [stamp]  = useState(() => CORRECT_STAMPS[Math.floor(Math.random() * CORRECT_STAMPS.length)])
  const [msg]    = useState(() => WRONG_MESSAGES[Math.floor(Math.random() * WRONG_MESSAGES.length)])

  useEffect(() => {
    setVisible(true)
    const t = setTimeout(() => setVisible(false), 2400)
    return () => clearTimeout(t)
  }, [])

  if (!visible) return null

  return (
    <div className={styles.root} aria-hidden="true">
      {isCorrect ? (
        <>
          {/* Shockwave rings — 3 staggered circles expanding from screen center */}
          {[0, 1, 2].map(i => (
            <div key={i} className={styles.ring} style={{ animationDelay: `${i * 0.15}s` }} />
          ))}

          {/* Center emoji stamp — scales in with bounce, fades out */}
          <div className={styles.stamp}>{stamp}</div>

          {/* Scatter dots — 8 directions */}
          {SCATTER_ANGLES.map((deg, i) => (
            <div
              key={i}
              className={styles.dot}
              style={{
                '--angle':  `${deg}deg`,
                '--color':  DOT_COLORS[i],
                animationDelay: `${0.05 * i}s`,
              }}
            />
          ))}
        </>
      ) : (
        <>
          {/* Red vignette at screen edges — two pulses */}
          <div className={styles.vignette} />

          {/* Motivational card — slides in from right */}
          <div className={styles.nudge}>{msg}</div>
        </>
      )}
    </div>
  )
}
