import { useEffect, useState } from 'react'
import { analyzeGap } from '../../api/client'
import MathText from '../MathText/MathText'
import styles from './FindMyGap.module.css'

/**
 * Renders the gap analysis content.
 * Called lazily — only when the student opens the accordion.
 *
 * Props:
 *   questionId    — UUID of the question
 *   studentAnswer — letter the student chose
 */
export default function FindMyGap({ questionId, studentAnswer }) {
  const [gaps, setGaps]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [active, setActive]   = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setGaps(null)
    setError(null)

    analyzeGap(questionId, studentAnswer)
      .then(data => {
        if (cancelled) return
        const parsed = typeof data === 'string' ? JSON.parse(data) : data
        setGaps(parsed?.gaps || [])
        setActive(0)
      })
      .catch(e => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })

    return () => { cancelled = true }
  }, [questionId, studentAnswer])

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <span>Diagnosing your gap…</span>
      </div>
    )
  }

  if (error) {
    return <div className={styles.error}>Could not load gap analysis. {error}</div>
  }

  if (!gaps || gaps.length === 0) {
    return <div className={styles.empty}>No specific gaps identified.</div>
  }

  return (
    <div>
      {/* Trigger pills */}
      <div className={styles.triggers}>
        {gaps.map((gap, i) => (
          <button
            key={i}
            className={`${styles.trigger} ${active === i ? styles.triggerActive : ''}`}
            onClick={() => setActive(i)}
          >
            {gap.trigger}
          </button>
        ))}
      </div>

      {/* Active gap card */}
      <GapCard gap={gaps[active]} />
    </div>
  )
}

function GapCard({ gap }) {
  if (!gap) return null
  return (
    <div className={styles.card}>
      <div className={styles.cardTitle}>{gap.title}</div>
      <MathText text={gap.body} as="p" className={styles.body} />
      {gap.example && (
        <div className={styles.example}>
          <div className={styles.exampleLabel}>Example</div>
          <MathText text={gap.example} as="div" className={styles.exampleText} />
        </div>
      )}
      {gap.takeaway && (
        <div className={styles.takeaway}>
          <span className={styles.takeawayIcon}>💡</span>
          <MathText text={gap.takeaway} as="span" />
        </div>
      )}
    </div>
  )
}
