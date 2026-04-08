import MathText from '../MathText/MathText'
import styles from './ChoiceExplanations.module.css'

/**
 * Shows why each choice is correct or incorrect.
 * choiceExplanations — object { A: string, B: string, C: string, D: string }
 * correctAnswer      — "A" | "B" | "C" | "D"
 * studentAnswer      — letter the student chose
 */
export default function ChoiceExplanations({ choiceExplanations, correctAnswer, studentAnswer }) {
  let expl = null
  try {
    expl = typeof choiceExplanations === 'string'
      ? JSON.parse(choiceExplanations) : choiceExplanations
  } catch { return null }
  if (!expl) return null

  const letters = ['A', 'B', 'C', 'D'].filter(l => expl[l])

  return (
    <div className={styles.wrap}>
      <h4 className={styles.heading}>Why Each Answer</h4>
      <div className={styles.list}>
        {letters.map(letter => {
          const isCorrect = letter === correctAnswer
          const isStudent = letter === studentAnswer
          return (
            <div key={letter} className={`${styles.row} ${isCorrect ? styles.correct : styles.wrong}`}>
              <div className={styles.badge}>
                <span className={styles.letter}>{letter}</span>
                {isCorrect && <span className={styles.tag}>✓ Correct</span>}
                {isStudent && !isCorrect && <span className={styles.tagWrong}>Your answer</span>}
              </div>
              <MathText text={expl[letter]} as="p" className={styles.text} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
