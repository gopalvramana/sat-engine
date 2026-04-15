import styles from './ConfidenceTap.module.css'

/**
 * ConfidenceTap — science-backed metacognitive micro-interaction.
 * Based on retrieval-practice research: asking "how sure were you?"
 * BEFORE revealing the answer improves long-term retention by ~20%.
 *
 * Props:
 *   value     – current selection: null | 'guessing' | 'unsure' | 'confident'
 *   onChange  – (value) => void
 */
const OPTIONS = [
  { id: 'guessing',   label: 'Guessing',  emoji: '🎲', desc: 'Not sure at all' },
  { id: 'unsure',     label: 'Unsure',    emoji: '🤔', desc: 'Somewhat sure'   },
  { id: 'confident',  label: 'Confident', emoji: '💡', desc: 'Pretty certain'  },
]

export default function ConfidenceTap({ value, onChange }) {
  return (
    <div className={styles.wrap}>
      <div className={styles.prompt}>How sure are you?</div>
      <div className={styles.options}>
        {OPTIONS.map(o => (
          <button
            key={o.id}
            className={`${styles.option} ${value === o.id ? styles.selected : ''}`}
            onClick={() => onChange(o.id)}
            type="button"
            aria-pressed={value === o.id}
          >
            <span className={styles.emoji}>{o.emoji}</span>
            <span className={styles.label}>{o.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
