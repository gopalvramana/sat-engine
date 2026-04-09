import styles from './ProgressBar.module.css'

/**
 * Top bar shown during a practice session.
 *
 * Props:
 *   current   – the question number being shown (1-based)
 *   total     – total questions selected for this session
 *   correct   – correct answers so far
 *   onHome    – callback to abandon & go back to builder
 *   onEnd     – callback to end session early → summary
 */
export default function ProgressBar({ current, total, correct, onHome, onEnd }) {
  const answered = current - 1           // questions already submitted
  const pct = total > 0 ? Math.round((answered / total) * 100) : 0

  return (
    <div className={styles.bar}>
      <div className={styles.inner}>

        {/* Left: back to builder */}
        <button className={styles.homeBtn} onClick={onHome} title="Back to session builder">
          ← Back
        </button>

        {/* Centre: progress */}
        <div className={styles.centre}>
          <div className={styles.label}>
            <span>Question <strong>{current}</strong> of <strong>{total || '?'}</strong></span>
            <span className={styles.correct}><strong>{correct}</strong> correct</span>
          </div>
          <div className={styles.track}>
            <div className={styles.fill} style={{ width: `${pct}%` }} />
          </div>
        </div>

        {/* Right: end session */}
        <button className={styles.endBtn} onClick={onEnd} title="End session and see results">
          End Session
        </button>

      </div>
    </div>
  )
}
