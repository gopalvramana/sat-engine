import styles from './ReviewBottomBar.module.css'

export default function ReviewBottomBar({
  index,        // 0-based
  total,
  onPrev,
  onNext,
  onResults,
  isLast,
}) {
  return (
    <div className={styles.bar}>
      <div className={styles.left}>
        <button className={styles.ghostBtn}>Hide Chat</button>
        <div className={styles.qPill}>
          Question {index + 1}
          <span className={styles.pillChevron}>▲</span>
        </div>
      </div>

      <div className={styles.nav}>
        <button
          className={styles.navBtn}
          onClick={onPrev}
          disabled={index === 0}
        >
          ← Previous
        </button>
        <button className={styles.navBtn} onClick={onNext} disabled={isLast && !onResults}>
          Next →
        </button>
        <button className={styles.resultsBtn} onClick={onResults}>
          Results
        </button>
      </div>
    </div>
  )
}
