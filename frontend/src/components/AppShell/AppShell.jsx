import { Outlet } from 'react-router-dom'
import TopNav from '../TopNav/TopNav'
import GamificationPanel from '../GamificationPanel/GamificationPanel'
import RightPanel from '../RightPanel/RightPanel'
import styles from './AppShell.module.css'

/**
 * Three-column authenticated layout:
 *   GamificationPanel (220px, hidden <1280px)
 *   main content (flex:1)
 *   RightPanel (256px, hidden <1020px)
 */
export default function AppShell() {
  return (
    <div className={styles.shell}>
      <TopNav />
      <div className={styles.body}>
        <GamificationPanel />
        <main className={styles.main}>
          <Outlet />
        </main>
        <RightPanel />
      </div>
    </div>
  )
}
