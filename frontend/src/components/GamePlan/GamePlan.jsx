import styles from './GamePlan.module.css'

/**
 * GamePlan — left-panel tutoring overlay.
 *
 * Props:
 *   questionNumber  – current question number (1-based)
 *   gamePlanSteps   – string[] shown as numbered list
 *   hints           – { label: string, text: string }[] — shown as mint pills
 *   onClose         – called when user dismisses the panel
 */
export default function GamePlan({ questionNumber = 1, gamePlanSteps = [], hints = [], onClose }) {
  return (
    <div className={styles.panel}>

      {/* Header */}
      <div className={styles.header}>
        <span className={styles.handwritten}>Game Plan</span>
        {onClose && (
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close">✕</button>
        )}
      </div>

      {/* Question tag */}
      <div className={styles.questionTag}>
        <span className={styles.handwritten}>{`Question ${questionNumber}`}</span>
      </div>

      {/* Game plan steps */}
      {gamePlanSteps.length > 0 && (
        <ol className={styles.stepList}>
          {gamePlanSteps.map((step, i) => (
            <li key={i} className={styles.step}>{step}</li>
          ))}
        </ol>
      )}

      {/* Hints */}
      {hints.length > 0 && (
        <div className={styles.hintSection}>
          {hints.map((h, i) => (
            <div key={i} className={styles.hintBlock}>
              <span className={styles.hintPill}>
                <span className={styles.handwritten}>{h.label || `Hint ${i + 1}`}</span>
              </span>
              <p className={styles.hintText}>{h.text}</p>
            </div>
          ))}
        </div>
      )}

    </div>
  )
}
