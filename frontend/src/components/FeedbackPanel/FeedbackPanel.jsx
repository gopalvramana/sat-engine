import { useState } from 'react'
import MathText from '../MathText/MathText'
import AnimationPanel from '../AnimationPanel/AnimationPanel'
import FindMyGap from '../FindMyGap/FindMyGap'
import SkillDrawer from '../SkillDrawer/SkillDrawer'
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

/* ── Step Navigator — one step at a time, synced with animation ─ */
function StepNavigator({ steps, animUid, animFrames }) {
  const [current, setCurrent] = useState(0)

  // Total = max(steps, animation frames) so Prev/Next covers both
  const total = Math.max(steps.length, animFrames ? animFrames.length : 0)
  if (!total) return null

  function goTo(idx) {
    setCurrent(idx)
    // Always sync animation to the same index
    if (animUid && typeof window.animGoTo === 'function') {
      window.animGoTo(animUid, idx)
    }
  }

  const step = steps[current]          // may be undefined for anim-only frames
  const frame = animFrames ? animFrames[current] : null

  return (
    <div className={styles.stepNavigator}>
      <div className={styles.stepCard}>
        {step ? (
          /* Real calculation step */
          <>
            <div className={styles.stepNumber}>Step {current + 1} of {total}</div>
            <div className={styles.stepTitle}><MathText text={step.title || ''} /></div>
            {step.math && (
              <div className={styles.stepMath}>
                <MathText text={`\\[${step.math}\\]`} as="div" />
              </div>
            )}
            {step.content && (
              <MathText text={step.content} as="p" className={styles.stepContent} />
            )}
          </>
        ) : (
          /* Animation-only frame — no matching calc step */
          <>
            <div className={styles.stepNumber}>
              Figure {current + 1} of {animFrames ? animFrames.length : total}
            </div>
            {frame?.caption && (
              <div className={`${styles.stepTitle} ${styles.stepTitleAnim}`}>
                {frame.caption}
              </div>
            )}
            <p className={`${styles.stepContent} ${styles.stepContentAnim}`}>
              See the diagram on the left.
            </p>
          </>
        )}
      </div>
      {total > 1 && (
        <div className={styles.stepNavFooter}>
          <button
            className={styles.stepNavBtn}
            onClick={() => goTo(current - 1)}
            disabled={current === 0}
          >← Prev</button>
          <div className={styles.stepNavCenter}>
            <div className={styles.stepDots}>
              {Array.from({ length: total }, (_, i) => (
                <span
                  key={i}
                  className={`${styles.stepDot} ${i === current ? styles.stepDotActive : ''}`}
                  onClick={() => goTo(i)}
                />
              ))}
            </div>
            <span className={styles.stepCounter}>{current + 1} of {total}</span>
          </div>
          <button
            className={styles.stepNavBtn}
            onClick={() => goTo(current + 1)}
            disabled={current === total - 1}
          >Next →</button>
        </div>
      )}
    </div>
  )
}

/* ── Main component ─────────────────────────────────────────── */
export default function FeedbackPanel({ feedback, question, studentAnswer, onNext, isReviewing }) {
  const isCorrect = feedback.isCorrect
  const isMath    = MATH_DOMAINS.has(question.domain)

  // Find My Gap only fetches when student opens the accordion
  const [gapTriggered, setGapTriggered] = useState(false)

  // Skill drawer — open when student taps "Study this skill"
  const [skillDrawerOpen, setSkillDrawerOpen] = useState(false)

  // Animation uid — set by AnimationPanel once renderer mounts; used by StepNavigator to sync
  const [animUid, setAnimUid] = useState(null)

  // Parse enrichment data
  const steps    = parseJson(feedback.explanationSteps, [])
  const cc       = parseJson(question.coreConceptJson, null)
  const alt      = parseJson(question.alternativeApproach, null)
  const choiceEx = parseJson(question.choiceExplanations, null)

  const hasAnimation = (() => {
    try {
      const a = parseJson(question.animationJson, null)
      return a?.frames?.length > 0
    } catch { return false }
  })()

  const hasChoiceEx = choiceEx && typeof choiceEx === 'object' &&
    ['A','B','C','D'].some(l => choiceEx[l])

  const hasAlt = isMath && alt?.title && Array.isArray(alt.steps) && alt.steps.length > 0

  /* ── Solution body: split layout when animation exists ─────── */
  function renderSolutionBody() {
    // Parse animation frames for step count sync
    const animCfg = hasAnimation ? parseJson(question.animationJson, null) : null
    const animFrames = animCfg?.frames || null

    const stepsEl = steps.length > 0
      ? <StepNavigator steps={steps} animUid={animUid} animFrames={animFrames} />
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
      {/* ── Result banner ────────────────────────────────────── */}
      <div className={`${styles.banner} ${isCorrect ? styles.bannerCorrect : styles.bannerWrong}`}>
        <div className={`${styles.bannerIcon} ${isCorrect ? styles.bannerIconCorrect : styles.bannerIconWrong}`}>
          {isCorrect ? '✓' : '✗'}
        </div>
        <div>
          <div className={styles.bannerTitle}>{isCorrect ? 'Correct!' : 'Not quite'}</div>
          {!isCorrect && (
            <div className={styles.bannerSub}>
              Correct answer: <strong>{feedback.correctAnswer}</strong>
            </div>
          )}
        </div>
      </div>

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

        {/* 2 — Why each option (MCQ only) */}
        {hasChoiceEx && (
          <AccordionItem icon="💬" label="Why each option?">
            <ChoiceWhyBody
              expl={choiceEx}
              options={{ A: question.optionA, B: question.optionB, C: question.optionC, D: question.optionD }}
              correctAnswer={feedback.correctAnswer}
              studentAnswer={studentAnswer}
            />
          </AccordionItem>
        )}

        {/* 3 — Core Concept (Math only) */}
        {isMath && cc?.title && (
          <AccordionItem icon="💡" label="Core Concept" badge={cc.title} badgeVariant="concept">
            <CoreConceptBody cc={cc} />
          </AccordionItem>
        )}

        {/* 4 — Alternative Approach (Math only) */}
        {hasAlt && (
          <AccordionItem icon="⇄" label="Alternative Approach" badge={alt.title} badgeVariant="alt">
            <AltApproachBody alt={alt} />
          </AccordionItem>
        )}

        {/* 5 — Find My Gap (wrong answers only, lazy) */}
        {!isCorrect && (
          <AccordionItem
            icon="🔍"
            label="Find My Gap"
            onOpen={() => setGapTriggered(true)}
          >
            {gapTriggered
              ? <FindMyGap questionId={question.id} studentAnswer={studentAnswer} />
              : <p className={styles.accordionEmpty}>Open to identify the gap in your reasoning.</p>
            }
          </AccordionItem>
        )}

      </div>

      {/* ── Next question button ──────────────────────────────── */}
      <div className={styles.nextRow}>
        <button className={styles.nextBtn} onClick={onNext}>
          {isReviewing ? 'Next →' : 'Next Question →'}
        </button>
      </div>
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

/* ── Alternative Approach body ──────────────────────────────── */
function AltApproachBody({ alt }) {
  return (
    <div className={styles.altSteps}>
      {alt.steps.map((s, i) => (
        <div key={i} className={styles.altStep}>
          <div className={styles.altStepHeader}>
            <span className={styles.altStepNum}>{i + 1}</span>
            <MathText text={s.title || ''} as="span" className={styles.altStepTitle} />
          </div>
          {s.content && <MathText text={s.content} as="p" className={styles.altStepContent} />}
          {s.math && (
            <div className={styles.altStepMath}>
              <MathText text={`\\[${s.math}\\]`} as="div" />
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
