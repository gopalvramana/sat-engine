/**
 * SessionNavBar — sticky bottom bar for SAT-style sessions.
 * Prev / question-number chip (opens grid) / Next / Mark for Review / Submit
 */
import styles from './SessionNavBar.module.css'

export default function SessionNavBar({
  currentIdx,
  total,
  isMarked,
  onPrev,
  onNext,
  onOpenGrid,
  onToggleMark,
  onSubmit,
  submitting,
  answeredCount,
}) {
  const isFirst = currentIdx === 0
  const isLast  = currentIdx === total - 1
  const unanswered = total - answeredCount

  return (
    <div className={styles.bar}>

      {/* Left: Prev */}
      <button
        className={styles.navBtn}
        onClick={onPrev}
        disabled={isFirst}
        aria-label="Previous question"
      >
        ← Back
      </button>

      {/* Center: question number chip + mark button */}
      <div className={styles.center}>
        <button className={styles.gridChip} onClick={onOpenGrid} title="View all questions">
          <span className={styles.chipLabel}>Q{currentIdx + 1}</span>
          <span className={styles.chipTotal}> / {total}</span>
          <span className={styles.chipArrow}>▾</span>
        </button>
        <button
          className={`${styles.markBtn} ${isMarked ? styles.markBtnActive : ''}`}
          onClick={onToggleMark}
          title={isMarked ? 'Remove mark' : 'Mark for review'}
          aria-label={isMarked ? 'Remove mark' : 'Mark for review'}
        >
          {isMarked ? '🔖 Marked' : '🔖 Mark'}
        </button>
      </div>

      {/* Right: Next or Submit */}
      <div className={styles.right}>
        {!isLast && (
          <button className={styles.navBtn} onClick={onNext} aria-label="Next question">
            Next →
          </button>
        )}
        <button
          className={styles.submitBtn}
          onClick={onSubmit}
          disabled={submitting}
          title={unanswered > 0 ? `${unanswered} question${unanswered !== 1 ? 's' : ''} unanswered` : 'Submit session'}
        >
          {submitting ? 'Submitting…' : 'Submit Session'}
        </button>
      </div>

    </div>
  )
}
