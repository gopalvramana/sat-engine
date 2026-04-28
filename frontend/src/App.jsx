import { Navigate, Routes, Route } from 'react-router-dom'
import AppShell from './components/AppShell/AppShell'
import RequireAuth from './components/RequireAuth/RequireAuth'
import LoginPage from './pages/LoginPage'
import StudyPlanPage from './pages/StudyPlanPage'
import AnalyticsPage from './pages/AnalyticsPage'
import ErrorLogPage from './pages/ErrorLogPage'
import PracticeSetupPage from './pages/PracticeSetupPage'
import PracticePage from './pages/PracticePage'
import SummaryPage from './pages/SummaryPage'
import SessionHistoryPage from './pages/SessionHistoryPage'
import SessionReviewPage from './pages/SessionReviewPage'
import UIDemo         from './pages/UIDemo'
import FocusArenaDemo from './pages/FocusArenaDemo'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="login"      element={<LoginPage />} />
      <Route path="demo"       element={<UIDemo />} />
      <Route path="focus-demo" element={<FocusArenaDemo />} />

      {/* Authenticated — all routes below require a valid session */}
      <Route element={<RequireAuth />}>
        {/* Shell-wrapped pages (top nav visible) */}
        <Route element={<AppShell />}>
          {/* Root redirects to Study Plan */}
          <Route index element={<Navigate to="study-plan" replace />} />
          {/* Primary nav pages */}
          <Route path="study-plan" element={<StudyPlanPage />} />
          <Route path="analytics"  element={<AnalyticsPage />} />
          <Route path="error-log"  element={<ErrorLogPage />} />

          {/* Practice setup & history (accessible via TopNav + Practice button) */}
          <Route path="practice" element={<PracticeSetupPage />} />
          <Route path="history"  element={<SessionHistoryPage />} />
        </Route>

        {/* Full-screen pages (no top nav — focused practice mode) */}
        <Route path="session/:sessionId" element={<PracticePage />} />
        <Route path="session/:sessionId/summary" element={<SummaryPage />} />
        <Route path="session/:sessionId/review/:index" element={<SessionReviewPage />} />
      </Route>
    </Routes>
  )
}
