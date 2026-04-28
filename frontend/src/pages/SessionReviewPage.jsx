import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import QuestionCard from '../components/QuestionCard/QuestionCard'
import FeedbackPanel from '../components/FeedbackPanel/FeedbackPanel'
import ChoiceExplanations from '../components/ChoiceExplanations/ChoiceExplanations'
import SessionSidebar from '../components/SessionSidebar/SessionSidebar'
import ReviewToolbar from '../components/ReviewToolbar/ReviewToolbar'
import ReviewBottomBar from '../components/ReviewBottomBar/ReviewBottomBar'
import styles from './SessionReviewPage.module.css'

export default function SessionReviewPage() {
  const { sessionId, index: indexStr } = useParams()
  const navigate = useNavigate()
  const index = parseInt(indexStr, 10) || 0

  const [answers, setAnswers] = useState(null) // SessionAnswerDetail[]
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(false)

  useEffect(() => {
    fetch(`/api/sessions/${sessionId}/answers`)
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) { setError(true); return }
        setAnswers(data)
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [sessionId])

  const goTo = useCallback((i) => {
    navigate(`/session/${sessionId}/review/${i}`, { replace: true })
  }, [navigate, sessionId])

  const goNext = useCallback(() => {
    if (!answers) return
    if (index < answers.length - 1) goTo(index + 1)
    else navigate(`/session/${sessionId}/summary`)
  }, [answers, index, goTo, navigate, sessionId])

  const goPrev = useCallback(() => {
    if (index > 0) goTo(index - 1)
  }, [index, goTo])

  if (loading) return <div className={styles.centred}>Loading…</div>
  if (error || !answers) return <div className={styles.centred}>Could not load session.</div>

  const a     = answers[index]
  const total = answers.length
  const isLast = index === total - 1

  if (!a) {
    navigate(`/session/${sessionId}/summary`)
    return null
  }

  // Build question object for QuestionCard (matches QuestionResponse shape)
  const question = {
    id:                  a.questionId,
    questionStem:        a.questionStem,
    domain:              a.domain,
    skill:               a.skill,
    difficulty:          a.difficulty,
    questionType:        a.questionType,
    optionA:             a.optionA,
    optionB:             a.optionB,
    optionC:             a.optionC,
    optionD:             a.optionD,
    passageText:         a.passageText,
    passageSource:       a.passageSource,
    diagramJson:         a.diagramJson,
    animationJson:       a.animationJson,
    coreConceptJson:     a.coreConceptJson,
    choiceExplanations:  a.choiceExplanations,
    alternativeApproach: a.alternativeApproach,
    skillKey:            a.skillKey,
    calculatorOk:        true,
  }

  // Build feedback object for FeedbackPanel (matches AnswerFeedback shape)
  const feedback = {
    isCorrect:        a.isCorrect,
    correctAnswer:    a.correctAnswer,
    explanationShort: a.explanationShort,
    explanationSteps: a.explanationSteps,
  }

  // Friendly domain label for toolbar breadcrumb
  const domainLabel = {
    algebra: 'Algebra',
    advanced_math: 'Advanced Math',
    problem_solving_data: 'Problem Solving & Data',
    geometry_trigonometry: 'Geometry & Trig',
    information_ideas: 'Information & Ideas',
    craft_structure: 'Craft & Structure',
    expression_ideas: 'Expression of Ideas',
    standard_english: 'Standard English',
  }[a.domain] ?? a.domain ?? 'Math'

  return (
    <div className={styles.page}>

      {/* ── Left sidebar ─────────────────────────────────────── */}
      <SessionSidebar answers={answers} />

      {/* ── Right panel ──────────────────────────────────────── */}
      <div className={styles.rightPanel}>

        {/* Sticky toolbar: progress + breadcrumb */}
        <ReviewToolbar
          index={index}
          total={total}
          sessionName="Session Review"
          domain={domainLabel}
          difficulty={a.difficulty}
          onClose={() => navigate(-1)}
        />

        {/* Two-column content */}
        <div className={styles.contentWrap}>

          {/* Q-col: question card + distractor rationale */}
          <div className={styles.qCol}>
            <QuestionCard
              question={question}
              feedback={feedback}
              studentAnswer={a.studentAnswer}
              timeTaken={a.timeSpentSeconds}
              disabled
              reviewMode
            />
            {/* Collapsible distractor rationale (MCQ only) */}
            <ChoiceExplanations
              choiceExplanations={question.choiceExplanations}
              correctAnswer={feedback.correctAnswer}
              studentAnswer={a.studentAnswer}
              options={{
                A: question.optionA,
                B: question.optionB,
                C: question.optionC,
                D: question.optionD,
              }}
            />
          </div>

          {/* Exp-col: step-by-step solution + alternative approach */}
          <div className={styles.expCol}>
            <FeedbackPanel
              feedback={feedback}
              question={question}
              studentAnswer={a.studentAnswer}
              onNext={goNext}
              isReviewing
              isLastQuestion={isLast}
              hideChoiceExpl   /* distractor rationale already shown in q-col */
            />
          </div>

        </div>

        {/* Sticky bottom bar */}
        <ReviewBottomBar
          index={index}
          total={total}
          onPrev={goPrev}
          onNext={goNext}
          onResults={() => navigate(`/session/${sessionId}/summary`)}
          isLast={isLast}
        />

      </div>
    </div>
  )
}
