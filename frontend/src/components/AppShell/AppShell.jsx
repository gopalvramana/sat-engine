import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../Sidebar/Sidebar'
import styles from './AppShell.module.css'

/**
 * Persistent layout wrapper for authenticated pages.
 * On desktop: sidebar always visible on the left.
 * On mobile: sidebar hidden; bottom nav + hamburger drawer instead.
 */
export default function AppShell() {
  const [drawerOpen, setDrawerOpen] = useState(false)

  return (
    <div className={styles.shell}>
      <Sidebar drawerOpen={drawerOpen} onClose={() => setDrawerOpen(false)} />

      {/* Overlay — tap outside drawer to close */}
      {drawerOpen && (
        <div className={styles.overlay} onClick={() => setDrawerOpen(false)} />
      )}

      <main className={styles.main}>
        {/* Mobile-only top bar */}
        <div className={styles.mobileTopBar}>
          <button
            className={styles.hamburger}
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
          >
            <span /><span /><span />
          </button>
          <span className={styles.mobileTitle}>Aptify</span>
        </div>

        <Outlet />
      </main>
    </div>
  )
}
