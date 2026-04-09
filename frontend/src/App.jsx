import { useState } from 'react'
import { useSession } from './hooks/useSession'
import HomePage     from './pages/HomePage'
import PracticePage from './pages/PracticePage'
import SummaryPage  from './pages/SummaryPage'
import './App.css'

export default function App() {
  const {
    phase, question, feedback, sessionInfo, history, error,
    startSession, submitAnswer, nextQuestion,
  } = useSession()

  // Track what the student answered so FeedbackPanel can highlight it
  const [studentAnswer, setStudentAnswer] = useState(null)

  function handleSubmit(answer) {
    setStudentAnswer(answer)
    submitAnswer(answer)
  }

  function handleRestart() {
    setStudentAnswer(null)
    window.location.reload()
  }

  if (error) {
    return (
      <div style={{ padding: 40, textAlign: 'center', fontFamily: 'Inter, system-ui' }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#ef4444', marginBottom: 8 }}>
          Something went wrong
        </div>
        <div style={{ fontSize: 14, color: '#64748b' }}>{error}</div>
        <button
          onClick={() => window.location.reload()}
          style={{ marginTop: 20, padding: '8px 24px', background: '#7c3aed', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer', fontSize: 14 }}
        >
          Reload
        </button>
      </div>
    )
  }

  if (phase === 'idle') {
    return (
      <HomePage
        onStart={({ section, domainBandCounts }) =>
          startSession('practice', section, domainBandCounts)
        }
      />
    )
  }

  if (phase === 'summary') {
    return (
      <SummaryPage
        sessionInfo={sessionInfo}
        history={history}
        onRestart={handleRestart}
      />
    )
  }

  return (
    <PracticePage
      phase={phase}
      question={question}
      feedback={feedback}
      sessionInfo={sessionInfo}
      submitAnswer={handleSubmit}
      nextQuestion={nextQuestion}
      studentAnswer={studentAnswer}
    />
  )
}
