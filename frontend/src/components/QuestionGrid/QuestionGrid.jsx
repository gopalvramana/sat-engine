/**
 * QuestionGrid — Bluebook-style question number overlay.
 * Shows all N question circles with status:
 *   ○ = unanswered   ● = answered   🔖 = marked   [border] = current
 */
import styles from './QuestionGrid.module.css'

export default function QuestionGrid({ questions, localAnswers, currentIdx, onJump, onClose }) {
  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div className={styles.panel} onClick={e => e.stopPropagation()}>

        <div className={styles.header}>
          <span className={styles.title}>Question Map</span>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close">✕</button>
        </div>

        {/* Legend */}
        <div className={styles.legend}>
          <span className={styles.legendItem}><span className={`${styles.dot} ${styles.dotUnanswered}`} /> Unanswered</span>
          <span className={styles.legendItem}><span className={`${styles.dot} ${styles.dotAnswered}`} /> Answered</span>
          <span className={styles.legendItem}><span className={`${styles.dot} ${styles.dotMarked}`} />🔖 Marked</span>
        </div>

        {/* Grid */}
        <div className={styles.grid}>
          {questions.map((sq, idx) => {
            const qid      = sq.question?.id
            const answered = !!localAnswers[qid]?.answer || !!sq.existingAnswer
            const marked   = sq.marked
            const isCurrent = idx === currentIdx

            return (
              <button
                key={idx}
                className={`
                  ${styles.cell}
                  ${isCurrent  ? styles.cellCurrent  : ''}
                  ${answered   ? styles.cellAnswered  : styles.cellUnanswered}
                  ${marked     ? styles.cellMarked    : ''}
                `}
                onClick={() => { onJump(idx); onClose() }}
                title={`Q${idx + 1}${marked ? ' · Marked for review' : ''}${answered ? ' · Answered' : ''}`}
              >
                {idx + 1}
                {marked && <span className={styles.markDot}>🔖</span>}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
