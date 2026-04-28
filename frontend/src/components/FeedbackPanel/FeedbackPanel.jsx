import { useState, useEffect, useRef } from 'react'
import MathText from '../MathText/MathText'
import AnimationPanel from '../AnimationPanel/AnimationPanel'
import FindMyGap from '../FindMyGap/FindMyGap'
import SkillDrawer from '../SkillDrawer/SkillDrawer'
import AnswerBurst from '../AnswerBurst/AnswerBurst'
import styles from './FeedbackPanel.module.css'

const MATH_DOMAINS = new Set([
  'algebra', 'advanced_math', 'problem_solving_data', 'geometry_trigonometry',
])

function parseJson(v, fallback) {
  if (!v) return fallback
  try { return typeof v === 'string' ? JSON.parse(v) : v } catch { return fallback }
}

/* ── Reusable accordion item using native <details> ─────────── */
function AccordionItem({ icon, label, badge, badgeVariant, defaultOpen, onOpen, children }) {
  function handleToggle(e) {
    if (e.currentTarget.open && onOpen) onOpen()
  }
  return (
    <details
      className={styles.accordionItem}
      open={defaultOpen || undefined}
      onToggle={handleToggle}
    >
      <summary className={styles.accordionSummary}>
        <span className={styles.accordionIcon}>{icon}</span>
        <span className={styles.accordionLabel}>{label}</span>
        {badge && (
          <span className={`${styles.accordionBadge} ${badgeVariant === 'concept' ? styles.badgeConcept : badgeVariant === 'alt' ? styles.badgeAlt : ''}`}>
            {badge}
          </span>
        )}
        <span className={styles.accordionChevron}>▶</span>
      </summary>
      <div className={styles.accordionBody}>
        {children}
      </div>
    </details>
  )
}

/* ── Step List — all steps visible, each individually collapsible ── */
function StepList({ steps, allOpen }) {
  // Review mode: all steps open; practice mode: only first step open
  const [openSet, setOpenSet] = useState(() => allOpen ? new Set(steps.map((_, i) => i)) : new Set([0]))

  function toggle(i) {
    setOpenSet(prev => {
      const next = new Set(prev)
      next.has(i) ? next.delete(i) : next.add(i)
      return next
    })
  }

  if (!steps.length) return null

  return (
    <div className={styles.stepList}>
      {steps.map((step, i) => {
        const isOpen = openSet.has(i)
        const isLast = i === steps.length - 1
        return (
          <div key={i} className={`${styles.stepRow} ${isOpen ? styles.stepRowOpen : ''}`}>
            <button className={styles.stepRowHdr} onClick={() => toggle(i)}>
              <span className={`${styles.stepBadge} ${isLast ? styles.stepBadgeDone : ''}`}>
                {isLast ? '✓' : i + 1}
              </span>
              <MathText text={step.title || ''} as="span" className={styles.stepRowTitle} />
              <span className={styles.stepRowChevron}>{isOpen ? '▾' : '›'}</span>
            </button>
            {isOpen && (
              <div className={styles.stepRowBody}>
                {step.content && (
                  <MathText text={step.content} as="p" className={styles.stepRowContent} />
                )}
                {step.math && (
                  <div className={styles.stepRowMath}>
                    <MathText text={`\\[${step.math}\\]`} as="div" />
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ── Main component ─────────────────────────────────────────── */
export default function FeedbackPanel({ feedback, question, studentAnswer, onNext, isReviewing, isLastQuestion, hideChoiceExpl, reviewMode }) {
  const isCorrect = feedback.isCorrect
  const isMath    = MATH_DOMAINS.has(question.domain)

  // Find My Gap only fetches when student opens the accordion
  const [gapTriggered, setGapTriggered] = useState(false)

  // Skill drawer — open when student taps "Study this skill"
  const [skillDrawerOpen, setSkillDrawerOpen] = useState(false)

  // Animation uid — set by AnimationPanel once renderer mounts; used by StepNavigator to sync
  const [animUid, setAnimUid] = useState(null)

  // Burst key — increment each time a new question is answered to re-trigger the animation
  const burstKeyRef = useRef(0)
  const [burstKey, setBurstKey] = useState(0)
  useEffect(() => {
    burstKeyRef.current += 1
    setBurstKey(burstKeyRef.current)
  }, [feedback])

  // Keyboard shortcut: Enter or Space advances to next question (practice mode only)
  useEffect(() => {
    if (reviewMode) return
    function handleKey(e) {
      // Don't fire when user is typing in an input / textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        onNext()
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onNext, reviewMode])

  // Parse enrichment data
  const steps    = parseJson(feedback.explanationSteps, [])
  const cc       = parseJson(question.coreConceptJson, null)
  const altRaw   = question.alternativeApproach
  const alt      = parseJson(altRaw, null)
  const altFallback = (!alt && typeof altRaw === 'string' && altRaw.trim()) ? altRaw.trim() : null
  const choiceEx = parseJson(question.choiceExplanations, null)

  const hasAnimation = (() => {
    try {
      const a = parseJson(question.animationJson, null)
      return a?.frames?.length > 0
    } catch { return false }
  })()

  const hasChoiceEx = choiceEx && typeof choiceEx === 'object' &&
    ['A','B','C','D'].some(l => choiceEx[l])

  const hasAlt = isMath && (
    (alt?.title && Array.isArray(alt.steps) && alt.steps.length > 0) || !!altFallback
  )

  /* ── Solution body: animation panel (if any) above step list ── */
  function renderSolutionBody() {
    const stepsEl = steps.length > 0
      ? <StepList steps={steps} allOpen={reviewMode} />
      : <p className={styles.accordionEmpty}>{feedback.explanationShort || 'No solution available.'}</p>

    if (hasAnimation) {
      return (
        <div className={styles.solutionSplit}>
          <div className={styles.solFig}>
            <AnimationPanel
              animationJson={question.animationJson}
              synced
              onReady={setAnimUid}
            />
          </div>
          <div className={styles.solSteps}>
            {stepsEl}
          </div>
        </div>
      )
    }
    return stepsEl
  }

  return (
    <div className={styles.wrap}>
      {/* ── Emoji burst — practice mode only ─────────────────── */}
      {!reviewMode && <AnswerBurst key={burstKey} isCorrect={isCorrect} />}

      {/* ── Result banner — practice mode only ───────────────── */}
      {!reviewMode && (
        <div className={`${styles.banner} ${isCorrect ? styles.bannerCorrect : styles.bannerWrong}`}>
          <div className={`${styles.bannerIcon} ${isCorrect ? styles.bannerIconCorrect : styles.bannerIconWrong}`}>
            {isCorrect ? '✓' : '✗'}
          </div>
          <div>
            <div className={styles.bannerTitle}>{isCorrect ? 'Correct!' : 'Not quite'}</div>
            <div className={styles.bannerSub}>
              {isCorrect ? 'Answer: ' : 'Correct answer: '}<strong>{feedback.correctAnswer}</strong>
            </div>
          </div>
        </div>
      )}

      {/* ── Short explanation (above accordion) ─────────────── */}
      {feedback.explanationShort && (
        <div className={styles.shortExpl}>
          <MathText text={feedback.explanationShort} as="div" />
        </div>
      )}

      {/* ── Study this skill button ──────────────────────────── */}
      {question.skillKey && (
        <button
          className={styles.studyBtn}
          onClick={() => setSkillDrawerOpen(true)}
        >
          <span className={styles.studyBtnIcon}>📚</span>
          <span className={styles.studyBtnText}>Study this skill</span>
          <span className={styles.studyBtnChevron}>→</span>
        </button>
      )}

      {/* ── Skill drawer overlay ──────────────────────────────── */}
      {skillDrawerOpen && question.skillKey && (
        <SkillDrawer
          skillKey={question.skillKey}
          onClose={() => setSkillDrawerOpen(false)}
        />
      )}

      {/* ── Accordion group ──────────────────────────────────── */}
      <div className={styles.accordionGroup}>

        {/* 1 — Solution */}
        <AccordionItem
          icon="📋"
          label="Solution"
          badge={steps.length ? `${steps.length} step${steps.length !== 1 ? 's' : ''}` : null}
          defaultOpen
        >
          {renderSolutionBody()}
        </AccordionItem>

        {/* 3 — Why each option (MCQ only) — hidden in review mode (shown in q-col instead) */}
        {!hideChoiceExpl && hasChoiceEx && (
          <AccordionItem icon="💬" label="Why each option?">
            <ChoiceWhyBody
              expl={choiceEx}
              options={{ A: question.optionA, B: question.optionB, C: question.optionC, D: question.optionD }}
              correctAnswer={feedback.correctAnswer}
              studentAnswer={studentAnswer}
            />
          </AccordionItem>
        )}

        {/* 4 — Core Concept (Math only) */}
        {isMath && cc?.title && (
          <AccordionItem icon="💡" label="Core Concept" badge={cc.title} badgeVariant="concept" defaultOpen={reviewMode}>
            <CoreConceptBody cc={cc} />
          </AccordionItem>
        )}

        {/* 5 — Alternative Approach (Math only) */}
        {hasAlt && (
          <AccordionItem icon="⇄" label="Alternative Approach" badge={alt?.title ?? 'Alternative Method'} badgeVariant="alt" defaultOpen={reviewMode}>
            {alt?.steps ? <AltApproachBody alt={alt} /> : <AltApproachFallback text={altFallback} />}
          </AccordionItem>
        )}

      </div>

      {/* ── Next question button — practice mode only ────────── */}
      {!reviewMode && (
        <div className={styles.nextRow}>
          <span className={styles.keyHint}>Enter ↵</span>
          <button className={styles.nextBtn} onClick={onNext}>
            {isReviewing ? 'Next →' : isLastQuestion ? 'See Results →' : 'Next Question →'}
          </button>
        </div>
      )}
    </div>
  )
}

/* ── Choice "why" body ──────────────────────────────────────── */
function ChoiceWhyBody({ expl, options, correctAnswer, studentAnswer }) {
  return (
    <div className={styles.choiceWhyList}>
      {['A','B','C','D'].filter(l => options[l]).map(letter => {
        const isCorrect = letter === correctAnswer
        const isStudent = letter === studentAnswer
        return (
          <div key={letter} className={`${styles.choiceWhyRow} ${isCorrect ? styles.choiceWhyCorrect : styles.choiceWhyWrong}`}>
            <div className={styles.choiceWhyHeader}>
              <span className={`${styles.choiceWhyIcon} ${isCorrect ? styles.iconCorrect : styles.iconWrong}`}>
                {isCorrect ? '✓' : '✗'}
              </span>
              <span className={styles.choiceWhyLetter}>{letter}</span>
              <MathText text={options[letter]} as="span" className={styles.choiceWhyText} />
              {isStudent && !isCorrect && <span className={styles.yourAnswer}>your answer</span>}
            </div>
            {expl[letter] && (
              <p className={styles.choiceWhyExpl}>{expl[letter]}</p>
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ── Core Concept body ──────────────────────────────────────── */
function CoreConceptBody({ cc }) {
  return (
    <div>
      {cc.summary && <MathText text={cc.summary} as="p" className={styles.conceptText} />}
      {cc.keyFormula && (
        <div className={styles.conceptFormula}>
          <MathText text={`\\[${cc.keyFormula}\\]`} as="div" />
        </div>
      )}
    </div>
  )
}

/* ── Alternative Approach body (structured JSON) ────────────── */
function AltApproachBody({ alt }) {
  return (
    <div className={styles.altBox}>
      {alt.steps.map((s, i) => (
        <div key={i} className={styles.altBoxStep}>
          {s.title && (
            <div className={styles.altBoxStepTitle}>
              <span className={styles.altBoxDot}>{i + 1}</span>
              <MathText text={s.title} as="span" />
            </div>
          )}
          {s.content && (
            <MathText text={s.content} as="p" className={styles.altBoxText} />
          )}
          {s.math && (
            <div className={styles.altBoxMath}>
              <MathText text={`\\[${s.math}\\]`} as="div" />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

/* ── Alternative Approach fallback (plain string) ────────────── */
function AltApproachFallback({ text }) {
  return (
    <div className={styles.altBox}>
      <MathText text={text} as="p" className={styles.altBoxText} />
    </div>
  )
}
