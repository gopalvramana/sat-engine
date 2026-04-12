import { Routes, Route } from 'react-router-dom'
import AppShell from './components/AppShell/AppShell'
import DashboardPage from './pages/DashboardPage'
import PracticeSetupPage from './pages/PracticeSetupPage'
import PracticePage from './pages/PracticePage'
import SummaryPage from './pages/SummaryPage'

export default function App() {
  return (
    <Routes>
      {/* Shell-wrapped pages (sidebar visible) */}
      <Route element={<AppShell />}>
        <Route index element={<DashboardPage />} />
        <Route path="practice" element={<PracticeSetupPage />} />
      </Route>

      {/* Full-screen pages (no sidebar — focused practice mode) */}
      <Route path="session/:sessionId" element={<PracticePage />} />
      <Route path="session/:sessionId/summary" element={<SummaryPage />} />
    </Routes>
  )
}
