import { Outlet } from 'react-router-dom'
import Sidebar from '../Sidebar/Sidebar'
import styles from './AppShell.module.css'

/**
 * Persistent layout wrapper for authenticated pages.
 * Renders the left sidebar + main content area via <Outlet />.
 * PracticePage and SummaryPage are rendered outside this shell
 * so they get the full screen without the sidebar.
 */
export default function AppShell() {
  return (
    <div className={styles.shell}>
      <Sidebar />
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
