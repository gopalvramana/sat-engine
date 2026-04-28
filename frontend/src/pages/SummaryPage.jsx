import { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import MathText from '../components/MathText/MathText'
import FeedbackPanel from '../components/FeedbackPanel/FeedbackPanel'
import { formatTime } from '../hooks/useTimer'
import styles from './SummaryPage.module.css'

const LETTERS = ['A', 'B', 'C', 'D']

export default function SummaryPage() {
  const location      = useLocation()
  const navigate      = useNavigate()
  const { sessionId } = useParams()

  // ── Mode A: came from PracticePage with router state ──────────────────
  const stateHistory     = location.state?.history     ?? null
  const stateSessionInfo = location.state?.sessionInfo ?? null
  const hasState = stateHistory !== null

  // ── Mode B: opened from History page — fetch from API ─────────────────
  const [apiLoading, setApiLoading] = useState(!hasState)
  const [apiError,   setApiError]   = useState(false)
  const [apiAnswers, setApiAnswers] = useState([])
  const [apiSession, setApiSession] = useState(null)

  useEffect(() => {
    if (hasState || !sessionId) return
    Promise.all([
      fetch(`/api/sessions/${sessionId}`).then(r => r.ok ? r.json() : null),
      fetch(`/api/sessions/${sessionId}/answers`).then(r => r.ok ? r.json() : []),
    ])
      .then(([sess, answers]) => {
        if (!sess) { setApiError(true); return }
        setApiSession(sess)
        setApiAnswers(answers)
      })
      .catch(() => setApiError(true))
      .finally(() => setApiLoading(false))
  }, [sessionId, hasState])

  // ── Unified item list ─────────────────────────────────────────────────
  const items = hasState
    ? stateHistory.map(h => ({
        domain:              h.question?.domain,
        skillKey:            h.question?.skillKey,
        difficulty:          h.question?.difficulty,
        questionStem:        h.question?.questionStem,
        questionType:        h.question?.questionType,
        optionA:             h.question?.optionA,
        optionB:             h.question?.optionB,
        optionC:             h.question?.optionC,
        optionD:             h.question?.optionD,
        correctAnswer:       h.feedback?.correctAnswer ?? h.question?.correctAnswer,
        studentAnswer:       h.studentAnswer,
        isCorrect:           h.feedback?.isCorrect,
        timeTaken:           h.timeTaken ?? 0,
        explanationShort:    h.feedback?.explanationShort,
        explanationSteps:    h.feedback?.explanationSteps,
        coreConceptJson:     h.question?.coreConceptJson,
        alternativeApproach: h.question?.alternativeApproach,
        choiceExplanations:  h.question?.choiceExplanations,
        animationJson:       h.question?.animationJson,
      }))
    : apiAnswers.map(a => ({
        domain:              a.domain,
        skillKey:            a.skillKey,
        difficulty:          a.difficulty,
        questionStem:        a.questionStem,
        questionType:        a.questionType,
        optionA:             a.optionA,
        optionB:             a.optionB,
        optionC:             a.optionC,
        optionD:             a.optionD,
        correctAnswer:       a.correctAnswer,
        studentAnswer:       a.studentAnswer,
        isCorrect:           a.isCorrect,
        timeTaken:           a.timeSpentSeconds ?? 0,
        explanationShort:    a.explanationShort,
        explanationSteps:    a.explanationSteps,      // DTO field name (not rawExplanationSteps)
        coreConceptJson:     a.coreConceptJson,        // DTO field name (not rawCoreConcept)
        alternativeApproach: a.alternativeApproach,
        choiceExplanations:  a.choiceExplanations,    // DTO field name (not rawDistractorRationale)
        animationJson:       a.animationJson,
      }))

  // ── Aggregate stats ───────────────────────────────────────────────────
  const total        = hasState ? (stateSessionInfo?.questionsAnswered ?? items.length) : (apiSession?.questionsAnswered ?? items.length)
  const correct      = items.filter(i => i.isCorrect).length
  const pct          = total > 0 ? Math.round(correct / total * 100) : 0
  const totalSeconds = items.reduce((sum, i) => sum + (i.timeTaken ?? 0), 0)

  // ── Domain breakdown ──────────────────────────────────────────────────
  const domainMap = {}
  items.forEach(item => {
    const d = item.domain || 'other'
    if (!domainMap[d]) domainMap[d] = { correct: 0, total: 0 }
    domainMap[d].total++
    if (item.isCorrect) domainMap[d].correct++
  })

  // ── Selected question (master-detail) ────────────────────────────────
  const [selectedIdx, setSelectedIdx] = useState(0)
  const selected = items[selectedIdx] ?? null

  // ── Loading / error ───────────────────────────────────────────────────
  if (apiLoading) return (
    <div className={styles.page}>
      <div className={styles.loadingMsg}>Loading session…</div>
    </div>
  )

  if (apiError) return (
    <div className={styles.page}>
      <div className={styles.errorMsg}>Could not load session.</div>
      <div className={styles.errorActions}>
        <button className={styles.actionSecondary} onClick={() => navigate('/history')}>Back to History</button>
      </div>
    </div>
  )

  return (
    <div className={styles.page}>
      {/* ══ LEFT PANEL ══════════════════════════════════════════════════ */}
      <div className={styles.left}>

        {/* ① Score header */}
        <div className={styles.scoreCard}>
          <div className={styles.scoreCircle}>
            <span className={styles.scorePct}>{pct}%</span>
            <span className={styles.scoreLabel}>score</span>
          </div>
          <div className={styles.scoreDetail}>
            <div className={styles.scoreTitle}>
              {hasState ? 'Session Complete!' : 'Session Review'}
            </div>
            <div className={styles.scoreSub}>
              <strong>{correct}</strong> of <strong>{total}</strong> correct
            </div>
            {totalSeconds > 0 && (
              <div className={styles.scoreTiming}>
                ⏱ {formatTime(totalSeconds)}
                {total > 0 && <span className={styles.avgTime}> · avg {formatTime(Math.round(totalSeconds / total))}/q</span>}
              </div>
            )}
          </div>
        </div>

        {/* ② Domain breakdown */}
        {Object.keys(domainMap).length > 0 && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>By Domain</div>
            <div className={styles.domainList}>
              {Object.entries(domainMap).map(([domain, data]) => {
                const pctD = Math.round(data.correct / data.total * 100)
                return (
                  <div key={domain} className={styles.domainRow}>
                    <div className={styles.domainLabel}>{domainLabel(domain)}</div>
                    <div className={styles.domainBar}>
                      <div className={styles.domainFill} style={{ width: `${pctD}%` }} />
                    </div>
                    <div className={styles.domainPct}>{pctD}%</div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* ③ Question list */}
        {items.length > 0 && (
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Questions</div>
            <div className={styles.questionList}>
              {items.map((item, i) => (
                <button
                  key={i}
                  className={`${styles.qRow} ${item.isCorrect ? styles.qRowCorrect : styles.qRowWrong} ${selectedIdx === i ? styles.qRowSelected : ''}`}
                  onClick={() => setSelectedIdx(i)}
                >
                  <span className={`${styles.qStatus} ${item.isCorrect ? styles.qStatusCorrect : styles.qStatusWrong}`}>
                    {item.isCorrect ? '✓' : '✗'}
                  </span>
                  <span className={styles.qIndex}>Q{i + 1}</span>
                  <span className={styles.qDomain}>{domainLabel(item.domain)}</span>
                  <span className={styles.qDots}>
                    {Array.from({ length: 3 }, (_, di) => (
                      <span key={di} className={di < (item.difficulty ?? 1) ? styles.dotFilled : styles.dotEmpty} />
                    ))}
                  </span>
                  <span className={styles.qTime}>{formatTime(item.timeTaken)}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ④ Actions */}
        <div className={styles.actions}>
          <button className={styles.actionPrimary} onClick={() => navigate('/practice')}>
            Practice Again
          </button>
          <button className={styles.actionSecondary} onClick={() => navigate('/history')}>
            {hasState ? 'View History' : 'Back to History'}
          </button>
        </div>

      </div>

      {/* ══ RIGHT PANEL (detail) ════════════════════════════════════════ */}
      <div className={styles.right}>
        {selected ? (
          <div className={styles.detail}>

            {/* Question stem */}
            <div className={styles.detailStem}>
              <MathText text={selected.questionStem} as="div" />
            </div>

            {/* MCQ choices */}
            {selected.questionType !== 'spr' && (
              <div className={styles.choices}>
                {LETTERS.map(letter => {
                  const text = { A: selected.optionA, B: selected.optionB, C: selected.optionC, D: selected.optionD }[letter]
                  if (!text) return null
                  const isCorrect      = letter === selected.correctAnswer
                  const isStudentWrong = letter === selected.studentAnswer && !isCorrect
                  const isDimmed       = !isCorrect && !isStudentWrong
                  return (
                    <div
                      key={letter}
                      className={`${styles.choice} ${isCorrect ? styles.choiceCorrect : ''} ${isStudentWrong ? styles.choiceWrong : ''} ${isDimmed ? styles.choiceDimmed : ''}`}
                    >
                      <span className={styles.choiceLetter}>{letter}</span>
                      <MathText text={text} as="span" className={styles.choiceText} />
                      {isCorrect      && <span className={styles.badgeCorrect}>✓ Correct</span>}
                      {isStudentWrong && <span className={styles.badgeWrong}>✗ Your answer</span>}
                    </div>
                  )
                })}
              </div>
            )}

            {/* SPR answer */}
            {selected.questionType === 'spr' && (
              <div className={styles.sprSummary}>
                <span>Your answer: <strong>{selected.studentAnswer || '—'}</strong></span>
                {!selected.isCorrect && <span className={styles.sprCorrect}>Correct: <strong>{selected.correctAnswer}</strong></span>}
              </div>
            )}

            {/* Rich explanation via FeedbackPanel in reviewMode */}
            <FeedbackPanel
              reviewMode
              feedback={{
                isCorrect:        selected.isCorrect,
                correctAnswer:    selected.correctAnswer,
                explanationShort: selected.explanationShort,
                explanationSteps: selected.explanationSteps,
              }}
              question={{
                domain:              selected.domain,
                skillKey:            selected.skillKey,
                optionA:             selected.optionA,
                optionB:             selected.optionB,
                optionC:             selected.optionC,
                optionD:             selected.optionD,
                coreConceptJson:     selected.coreConceptJson,
                alternativeApproach: selected.alternativeApproach,
                choiceExplanations:  selected.choiceExplanations,
                animationJson:       selected.animationJson,
              }}
              studentAnswer={selected.studentAnswer}
              onNext={() => {}}
              isReviewing
              hideChoiceExpl={false}
            />

          </div>
        ) : (
          <div className={styles.emptyDetail}>
            Select a question to review
          </div>
        )}
      </div>
    </div>
  )
}

function domainLabel(d) {
  const M = {
    algebra:               'Algebra',
    advanced_math:         'Advanced Math',
    problem_solving_data:  'Problem Solving & Data',
    geometry_trigonometry: 'Geometry & Trig',
    information_ideas:     'Information & Ideas',
    craft_structure:       'Craft & Structure',
    expression_ideas:      'Expression of Ideas',
    standard_english:      'Standard English',
  }
  return M[d] || d || 'Other'
}
