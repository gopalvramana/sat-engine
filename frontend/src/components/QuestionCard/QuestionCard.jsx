import { useState } from 'react'
import MathText from '../MathText/MathText'
import DiagramPanel from '../DiagramPanel/DiagramPanel'
import styles from './QuestionCard.module.css'

const LETTERS = ['A', 'B', 'C', 'D']

/**
 * Renders a question and collects the student's answer.
 *
 * Props:
 *   question   — QuestionResponse from the API
 *   onSubmit   — called with the chosen answer string (letter for MCQ, number for SPR)
 *   disabled   — true while submitting
 */
export default function QuestionCard({ question, onSubmit, disabled, feedback, studentAnswer }) {
  const [selected, setSelected] = useState(null)
  const [sprValue, setSprValue] = useState('')

  const isMCQ = question.questionType === 'mcq'
  const isSPR = question.questionType === 'spr'
  const options = {
    A: question.optionA, B: question.optionB,
    C: question.optionC, D: question.optionD,
  }

  function handleSubmit() {
    if (disabled) return
    if (isMCQ && !selected) return
    if (isSPR && sprValue.trim() === '') return
    onSubmit(isMCQ ? selected : sprValue.trim())
    setSelected(null)
    setSprValue('')
  }

  const diffDots = Array.from({ length: 7 }, (_, i) => (
    <span key={i} className={i < question.difficulty ? styles.dotFilled : styles.dotEmpty} />
  ))

  return (
    <div className={styles.card}>
      {/* ── Meta ──────────────────────────────────────────────── */}
      <div className={styles.meta}>
        <span className={styles.domain}>{domainLabel(question.domain)}</span>
        <span className={styles.diff}>{diffDots}</span>
      </div>

      {/* ── Passage (R&W only) ─────────────────────────────────── */}
      {question.passageText && (
        <div className={styles.passage}>
          <MathText text={question.passageText} as="div" />
        </div>
      )}

      {/* ── Diagram (math) ────────────────────────────────────── */}
      {question.diagramJson && (
        <DiagramPanel diagramJson={question.diagramJson} />
      )}

      {/* ── Question stem ─────────────────────────────────────── */}
      <div className={styles.stem}>
        <MathText text={question.questionStem} as="div" />
      </div>

      {/* ── MCQ choices ───────────────────────────────────────── */}
      {isMCQ && (
        <div className={styles.choices}>
          {LETTERS.map(letter => {
            const text = options[letter]
            if (!text) return null
            // Color-code after submission
            const isCorrect  = feedback && letter === feedback.correctAnswer
            const isStudentWrong = feedback && letter === studentAnswer && letter !== feedback.correctAnswer
            const colorClass = isCorrect ? styles.choiceCorrect
                             : isStudentWrong ? styles.choiceWrong
                             : feedback ? styles.choiceDimmed : ''
            return (
              <button
                key={letter}
                className={`${styles.choice} ${!feedback && selected === letter ? styles.choiceSelected : ''} ${colorClass}`}
                onClick={() => !disabled && setSelected(letter)}
                disabled={disabled}
              >
                <span className={`${styles.choiceLetter} ${isCorrect ? styles.choiceLetterCorrect : isStudentWrong ? styles.choiceLetterWrong : ''}`}>{letter}</span>
                <MathText text={text} as="span" className={styles.choiceText} />
                {isCorrect && <span className={styles.choiceBadge}>✓ Correct</span>}
                {isStudentWrong && <span className={styles.choiceBadgeWrong}>✗ Your answer</span>}
              </button>
            )
          })}
        </div>
      )}

      {/* ── SPR input ─────────────────────────────────────────── */}
      {isSPR && (
        <div className={styles.sprWrap}>
          <input
            type="text"
            className={styles.sprInput}
            placeholder={`Enter answer${question.sprMin != null ? ` (${question.sprMin}–${question.sprMax})` : ''}`}
            value={sprValue}
            onChange={e => setSprValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSubmit()}
            disabled={disabled}
          />
        </div>
      )}

      {/* ── Submit ────────────────────────────────────────────── */}
      <div className={styles.submitRow}>
        <button
          className={styles.submitBtn}
          onClick={handleSubmit}
          disabled={disabled || (isMCQ && !selected) || (isSPR && !sprValue.trim())}
        >
          Confirm Answer
        </button>
      </div>
    </div>
  )
}

function domainLabel(d) {
  const M = {
    algebra: 'Algebra', advanced_math: 'Advanced Math',
    problem_solving_data: 'Problem Solving & Data',
    geometry_trigonometry: 'Geometry & Trig',
    information_ideas: 'Information & Ideas',
    craft_structure: 'Craft & Structure',
    expression_ideas: 'Expression of Ideas',
    standard_english: 'Standard English',
  }
  return M[d] || d || ''
}
