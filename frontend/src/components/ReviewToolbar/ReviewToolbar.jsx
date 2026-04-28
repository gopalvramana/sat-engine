import styles from './ReviewToolbar.module.css'

/**
 * Top chrome for the review page.
 * Shows centered timer, breadcrumb + progress badge, icon toolbar.
 * Thin indigo gradient progress strip runs below the bar.
 */
export default function ReviewToolbar({
  index,          // 0-based current question index
  total,          // total questions in session
  sessionName,    // e.g. "Practice Set 3"
  domain,         // e.g. "Algebra"
  difficulty,     // 1 | 2 | 3
  onClose,        // navigate to summary
}) {
  const diffLabel = difficulty === 1 ? 'Easy' : difficulty === 2 ? 'Medium' : 'Hard'
  const pct = total > 0 ? Math.round(((index + 1) / total) * 100) : 0

  return (
    <div className={styles.root}>
      {/* ── Main toolbar row ── */}
      <div className={styles.bar}>

        {/* Left: icon buttons */}
        <div className={styles.icons}>
          <button className={styles.iconBtn} title="Bookmark">🔖</button>
          <button className={styles.iconBtn} title="Flag">🚩</button>
          <button className={styles.iconBtn} title="Calculator">🧮</button>
          <button className={styles.iconBtn} title="Reference sheet">📋</button>
          <button className={styles.iconBtn} title="Annotate">✏️</button>
        </div>

        {/* Center: timer */}
        <div className={styles.center}>
          <span className={styles.timer}>00:00</span>
          <span className={styles.hideLabel}>Hide</span>
        </div>

        {/* Right: close */}
        <button className={styles.closeBtn} onClick={onClose} title="Back to summary">✕</button>
      </div>

      {/* ── Progress strip ── */}
      <div className={styles.progressTrack}>
        <div className={styles.progressFill} style={{ width: `${pct}%` }} />
      </div>

      {/* ── Breadcrumb row ── */}
      <div className={styles.crumbRow}>
        <div className={styles.crumb}>
          Review Answers · <strong>{sessionName || 'Session'}</strong>
          {domain ? ` · ${domain}` : ''}
          {diffLabel ? ` · ${diffLabel}` : ''}
        </div>
        <div className={styles.badge}>{index + 1} / {total}</div>
      </div>
    </div>
  )
}
