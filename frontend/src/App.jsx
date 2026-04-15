import { Routes, Route } from 'react-router-dom'
import AppShell from './components/AppShell/AppShell'
import RequireAuth from './components/RequireAuth/RequireAuth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PracticeSetupPage from './pages/PracticeSetupPage'
import PracticePage from './pages/PracticePage'
import SummaryPage from './pages/SummaryPage'
import SessionHistoryPage from './pages/SessionHistoryPage'
import SessionReviewPage from './pages/SessionReviewPage'
import UIDemo        from './pages/UIDemo'
import FocusArenaDemo from './pages/FocusArenaDemo'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="login" element={<LoginPage />} />
      <Route path="demo"        element={<UIDemo />} />
      <Route path="focus-demo"  element={<FocusArenaDemo />} />

      {/* Authenticated — all routes below require a valid session */}
      <Route element={<RequireAuth />}>
        {/* Shell-wrapped pages (sidebar visible) */}
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="practice" element={<PracticeSetupPage />} />
          <Route path="history" element={<SessionHistoryPage />} />
        </Route>

        {/* Full-screen pages (no sidebar — focused practice mode) */}
        <Route path="session/:sessionId" element={<PracticePage />} />
        <Route path="session/:sessionId/summary" element={<SummaryPage />} />
        <Route path="session/:sessionId/review/:index" element={<SessionReviewPage />} />
      </Route>
    </Routes>
  )
}
