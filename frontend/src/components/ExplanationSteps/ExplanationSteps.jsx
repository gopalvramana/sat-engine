import { useState, useRef } from 'react'
import MathText from '../MathText/MathText'
import styles from './ExplanationSteps.module.css'

/**
 * Accordion step-by-step solution panel.
 * stepsJson — raw JSON string from question.explanationSteps (array of {title, content, math})
 */
export default function ExplanationSteps({ stepsJson, hideHeading }) {
  const [open, setOpen] = useState(0)

  let steps = []
  try {
    steps = typeof stepsJson === 'string' ? JSON.parse(stepsJson) : (stepsJson || [])
  } catch { return null }

  if (!steps.length) return null

  return (
    <div className={styles.wrap}>
      {!hideHeading && <h4 className={styles.heading}>Step-by-Step Solution</h4>}
      {steps.map((step, i) => (
        <StepItem key={i} step={step} index={i} total={steps.length}
          isOpen={open === i} onToggle={() => setOpen(open === i ? -1 : i)} />
      ))}
    </div>
  )
}

function StepItem({ step, index, total, isOpen, onToggle }) {
  const bodyRef = useRef(null)
  return (
    <div className={`${styles.step} ${isOpen ? styles.stepOpen : ''}`}>
      <button className={styles.stepHeader} onClick={onToggle}>
        <span className={styles.stepNum}>Step {index + 1} of {total}</span>
        <span className={styles.stepTitle}>
          <MathText text={step.title} />
        </span>
        <span className={styles.chevron}>{isOpen ? '▲' : '▼'}</span>
      </button>
      {isOpen && (
        <div className={styles.stepBody} ref={bodyRef}>
          {step.math && (
            <div className={styles.mathBlock}>
              <MathText text={`\\[${step.math}\\]`} as="div" />
            </div>
          )}
          {step.content && (
            <MathText text={step.content} as="p" className={styles.content} />
          )}
        </div>
      )}
    </div>
  )
}
