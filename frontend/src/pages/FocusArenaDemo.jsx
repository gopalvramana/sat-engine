/**
 * FocusArenaDemo — Science-backed practice page concept.
 *
 * Confidence approach:
 *  - PRE-answer:  NO blocking tap — submit activates on answer selection alone
 *  - POST-answer: optional "Were you sure?" micro-tap appears in InsightPanel
 *  - FALLBACK:    timing proxy (< 15s = confident, 15-75s = unsure, > 75s = guessing)
 *
 * Route: /app/focus-demo  (dev only)
 */
import { useState, useEffect, useRef } from 'react'
import InsightPanel  from '../components/InsightPanel/InsightPanel'
import CircularTimer from '../components/CircularTimer/CircularTimer'
import AnswerBurst   from '../components/AnswerBurst/AnswerBurst'
import styles from './FocusArenaDemo.module.css'

// ── Mock question ──────────────────────────────────────────────
const QUESTION = {
  number: 7, total: 20,
  domain: 'Algebra', section: 'math', difficulty: 4,
  stem: 'A line passes through the points (−2, 5) and (4, −1). What is the y-intercept of this line?',
  choices: { A: 'y = 1', B: 'y = 3', C: 'y = −2', D: 'y = 5' },
  correct: 'B',
}
const DOMAIN_ACCURACY = 68
const DIFF_LABELS = { 1:'Easy',2:'Easy',3:'Medium',4:'Medium',5:'Hard',6:'Hard',7:'Expert' }
const DIFF_COLORS = { 1:'#4ade80',2:'#4ade80',3:'#fb923c',4:'#fb923c',5:'#f43f5e',6:'#f43f5e',7:'#a78bfa' }

/** Timing proxy — infer confidence from how long student took */
function inferConfidence(seconds) {
  if (seconds < 15)  return 'confident'
  if (seconds < 75)  return 'unsure'
  return 'guessing'
}

export default function FocusArenaDemo() {
  const [selected,    setSelected]    = useState(null)
  const [confidence,  setConfidence]  = useState(null)   // set post-answer (optional tap)
  const [phase,       setPhase]       = useState('question')
  const [isCorrect,   setIsCorrect]   = useState(null)
  const [elapsed,     setElapsed]     = useState(0)
  const [burstKey,    setBurstKey]    = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    if (phase !== 'question') return
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
    return () => clearInterval(timerRef.current)
  }, [phase])

  function handleSubmit() {
    clearInterval(timerRef.current)
    setIsCorrect(selected === QUESTION.correct)
    setPhase('feedback')
    setBurstKey(k => k + 1)
  }

  function handleReset() {
    setSelected(null)
    setConfidence(null)
    setPhase('question')
    setIsCorrect(null)
    setElapsed(0)
    setBurstKey(0)
  }

  // Effective confidence: explicit tap OR timing proxy
  const effectiveConfidence = confidence ?? (phase === 'feedback' ? inferConfidence(elapsed) : null)
  const d = QUESTION.difficulty

  return (
    <div className={styles.page}>
      {phase === 'feedback' && <AnswerBurst key={burstKey} isCorrect={isCorrect} />}

      {/* ── Top bar ───────────────────────────────────────── */}
      <div className={styles.topBar}>
        <button className={styles.backBtn} onClick={handleReset}>← Back</button>
        <div className={styles.progressWrap}>
          <div className={styles.progressMeta}>
            <span className={styles.qCount}>Q<strong>{QUESTION.number}</strong> / {QUESTION.total}</span>
            <span className={styles.domainTag}>{QUESTION.domain}</span>
            <span className={styles.correctCount}>6 correct</span>
          </div>
          <div className={styles.progressTrack}>
            <div className={styles.progressFill} style={{ width: `${((QUESTION.number-1)/QUESTION.total)*100}%` }} />
          </div>
        </div>
        <button className={styles.endBtn}>End Session</button>
      </div>

      {/* ── Arena ────────────────────────────────────────── */}
      <div className={`${styles.arena} ${phase === 'feedback' ? styles.arenaFeedback : ''}`}>

        {/* Left: question card */}
        <div className={`${styles.cardWrap} ${phase === 'feedback' ? styles.cardLocked : ''}`}>
          <div className={styles.watermark}>{QUESTION.domain}</div>
          <div className={styles.card}>

            {/* Card header */}
            <div className={styles.cardHeader}>
              <span
                className={styles.diffPill}
                style={{ background: DIFF_COLORS[d]+'22', color: DIFF_COLORS[d], borderColor: DIFF_COLORS[d]+'55' }}
              >
                d{d} · {DIFF_LABELS[d]}
              </span>
              <CircularTimer elapsed={elapsed} total={120} size={48} />
            </div>

            {/* Stem */}
            <p className={styles.stem}>{QUESTION.stem}</p>

            {/* Choices */}
            <div className={styles.choices}>
              {Object.entries(QUESTION.choices).map(([letter, text]) => {
                const locked  = phase === 'feedback'
                const isRight = letter === QUESTION.correct
                const isPicked = letter === selected
                return (
                  <button
                    key={letter}
                    className={`${styles.choice}
                      ${isPicked && !locked ? styles.choiceSelected : ''}
                      ${locked && isRight   ? styles.choiceCorrect  : ''}
                      ${locked && isPicked && !isRight ? styles.choiceWrong : ''}`}
                    onClick={() => !locked && setSelected(letter)}
                    disabled={locked}
                  >
                    <span className={styles.choiceLetter}>{letter}</span>
                    <span className={styles.choiceText}>{text}</span>
                    {locked && isRight           && <span className={styles.choiceMark}>✓</span>}
                    {locked && isPicked && !isRight && <span className={styles.choiceMark}>✗</span>}
                  </button>
                )
              })}
            </div>

            {/* Submit — activates on answer selection alone, no confidence gate */}
            {phase === 'question' && (
              <button
                className={`${styles.submitBtn} ${selected ? styles.submitBtnReady : ''}`}
                onClick={handleSubmit}
                disabled={!selected}
              >
                {selected ? 'Check Answer →' : 'Select an answer'}
              </button>
            )}
          </div>
        </div>

        {/* Right: InsightPanel with post-answer confidence tap */}
        {phase === 'feedback' && isCorrect !== null && (
          <div className={styles.insightWrap}>
            <InsightPanel
              isCorrect={isCorrect}
              confidence={effectiveConfidence}
              explicitConfidence={confidence}
              onConfidenceChange={setConfidence}
              timeTaken={elapsed}
              avgTime={57}
              domain={QUESTION.domain}
              domainAccuracy={DOMAIN_ACCURACY}
              difficulty={d}
              targetScore={1350}
              streakCorrect={isCorrect ? 4 : 0}
              onNext={handleReset}
              isLastQuestion={false}
            />
          </div>
        )}
      </div>

      <div className={styles.devLabel}>Focus Arena · Dev Prototype · /app/focus-demo</div>
    </div>
  )
}
