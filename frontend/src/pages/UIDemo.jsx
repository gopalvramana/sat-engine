/**
 * UIDemo — dev-only playground for GamePlan + SessionSummaryPanel.
 * Route: /demo  (add to App.jsx when needed, remove before prod)
 */
import { useState } from 'react'
import GamePlan from '../components/GamePlan/GamePlan'
import SessionSummaryPanel from '../components/SessionSummaryPanel/SessionSummaryPanel'
import AnswerBurst from '../components/AnswerBurst/AnswerBurst'
import styles from './UIDemo.module.css'

const GAME_PLAN_STEPS = [
  'Read the question stem carefully — identify what you are solving for.',
  'List the given values and label the unknown.',
  'Choose a strategy: direct equation, substitution, or elimination.',
  'Solve and double-check units / reasonableness.',
]

const HINTS = [
  {
    label: 'Hint 1',
    text: 'Let x = the number of adult tickets. Then the number of child tickets is (200 − x).',
  },
  {
    label: 'Hint 2',
    text: 'Write an equation for total revenue: 12x + 7(200 − x) = 1950.',
  },
]

const DOMAINS = [
  { name: 'Algebra',                correct: 7, total: 9,  avgTime: 58  },
  { name: 'Advanced Math',          correct: 3, total: 6,  avgTime: 12  },
  { name: 'Problem Solving & Data', correct: 5, total: 5,  avgTime: 44  },
  { name: 'Geometry & Trig',        correct: 2, total: 5,  avgTime: 105 },
]

const BY_DIFF = [
  { label: 'd3', correct: 5, total: 5,  avgTime: 38 },
  { label: 'd4', correct: 7, total: 10, avgTime: 61 },
  { label: 'd5', correct: 5, total: 10, avgTime: 10 },
]

const TIMELINE = [
  { q: 1,  seconds: 45  },
  { q: 2,  seconds: 120 },
  { q: 3,  seconds: 30  },
  { q: 4,  seconds: 55  },
  { q: 5,  seconds: 9   },
  { q: 6,  seconds: 80  },
  { q: 7,  seconds: 95  },
  { q: 8,  seconds: 40  },
  { q: 9,  seconds: 11  },
  { q: 10, seconds: 65  },
]

export default function UIDemo() {
  const [showAnalytics, setShowAnalytics] = useState(true)
  const [burstKey,  setBurstKey]  = useState(0)
  const [burstType, setBurstType] = useState(true) // true = correct

  function fireBurst(isCorrect) {
    setBurstType(isCorrect)
    setBurstKey(k => k + 1)
  }

  return (
    <div className={styles.page}>
      <AnswerBurst key={burstKey} isCorrect={burstType} />

      <div className={styles.header}>
        <span className={styles.badge}>Dev Only</span>
        <h1 className={styles.title}>UI Component Demo</h1>
        <p className={styles.sub}>GamePlan (left) · SessionSummaryPanel (right) · AnswerBurst (buttons below)</p>
      </div>

      {/* Burst demo buttons */}
      <div className={styles.burstRow}>
        <span className={styles.colLabel} style={{ margin: 0 }}>AnswerBurst.jsx</span>
        <button className={styles.burstCorrect} onClick={() => fireBurst(true)}>
          Fire Correct 🎉
        </button>
        <button className={styles.burstWrong} onClick={() => fireBurst(false)}>
          Fire Wrong 💪
        </button>
      </div>

      <div className={styles.layout}>
        {/* Left: Game Plan */}
        <div>
          <div className={styles.colLabel}>GamePlan.jsx</div>
          <GamePlan
            questionNumber={3}
            gamePlanSteps={GAME_PLAN_STEPS}
            hints={HINTS}
          />
        </div>

        {/* Right: Session Analytics */}
        <div>
          <div className={styles.colLabel}>SessionSummaryPanel.jsx</div>
          {showAnalytics
            ? <SessionSummaryPanel
                domains={DOMAINS}
                byDiff={BY_DIFF}
                timeline={TIMELINE}
                onClose={() => setShowAnalytics(false)}
              />
            : <button className={styles.reopen} onClick={() => setShowAnalytics(true)}>
                Re-open Analytics Panel
              </button>
          }
        </div>
      </div>
    </div>
  )
}
