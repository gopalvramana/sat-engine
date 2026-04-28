import { useState } from 'react'
import MathText from '../MathText/MathText'
import styles from './ChoiceExplanations.module.css'

/**
 * Collapsible distractor rationale cards.
 * Each choice is a row with a colored chip + expand/collapse.
 * The student's wrong answer starts open by default.
 */
export default function ChoiceExplanations({
  choiceExplanations,
  correctAnswer,
  studentAnswer,
  options = {},
}) {
  let expl = null
  try {
    expl = typeof choiceExplanations === 'string'
      ? JSON.parse(choiceExplanations) : choiceExplanations
  } catch { return null }
  if (!expl) return null

  const letters = ['A','B','C','D'].filter(l => expl[l] || options[l])
  if (!letters.length) return null

  return (
    <div className={styles.wrap}>
      <div className={styles.heading}>Why Each Answer Is Wrong</div>
      <div className={styles.list}>
        {letters.map(letter => (
          <DistractorRow
            key={letter}
            letter={letter}
            text={options[letter] || ''}
            explanation={expl[letter] || ''}
            isCorrect={letter === correctAnswer}
            isStudent={letter === studentAnswer}
            defaultOpen={letter === studentAnswer && letter !== correctAnswer}
          />
        ))}
      </div>
    </div>
  )
}

function DistractorRow({ letter, text, explanation, isCorrect, isStudent, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen)

  const chipClass = isCorrect
    ? styles.chipCorrect
    : isStudent
      ? styles.chipWrong
      : styles.chipNeutral

  const rowClass = `${styles.row} ${isCorrect ? styles.rowCorrect : isStudent ? styles.rowWrong : ''}`

  return (
    <div className={rowClass}>
      <button className={styles.header} onClick={() => setOpen(o => !o)} aria-expanded={open}>
        <span className={styles.letter}>{letter}</span>
        <span className={`${styles.chip} ${chipClass}`}>
          <MathText text={text} as="span" />
          {isCorrect && ' ✓'}
        </span>
        {isStudent && !isCorrect && (
          <span className={styles.yourTag}>Your answer</span>
        )}
        <span className={styles.chevron}>{open ? '▾' : '›'}</span>
      </button>

      {open && explanation && (
        <div className={styles.body}>
          <MathText text={explanation} as="p" className={styles.bodyText} />
        </div>
      )}
    </div>
  )
}
