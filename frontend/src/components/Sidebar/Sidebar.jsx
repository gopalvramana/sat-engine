import { NavLink } from 'react-router-dom'
import { LayoutDashboard, PenLine, BookMarked, TrendingUp, ClipboardList, History } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import styles from './Sidebar.module.css'

const NAV_ITEMS = [
  { path: '/',         label: 'Dashboard',       Icon: LayoutDashboard, exact: true },
  { path: '/practice', label: 'Practice Exams',  Icon: PenLine,         exact: false },
  { path: '/history',  label: 'History',         Icon: History,         exact: false },
  { path: null,        label: 'Question Bank',   Icon: BookMarked,      soon: true },
  { path: null,        label: 'Score Predictor', Icon: TrendingUp,      soon: true },
  { path: null,        label: 'Full Tests',      Icon: ClipboardList,   soon: true },
]

// Only the active nav items shown in bottom bar (no "soon" items — too cramped)
const BOTTOM_NAV_ITEMS = NAV_ITEMS.filter(i => !i.soon)

export default function Sidebar({ drawerOpen = false, onClose }) {
  const { user, logout } = useAuth()

  return (
    <>
    <aside className={`${styles.sidebar} ${drawerOpen ? styles.drawerOpen : ''}`}>
      {/* Logo */}
      <div className={styles.logo}>
        <svg className={styles.logoMark} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="ag" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
              <stop stopColor="#fbbf24"/>
              <stop offset="1" stopColor="#92400e"/>
            </linearGradient>
          </defs>
          <rect width="36" height="36" rx="10" fill="url(#ag)"/>
          {/* A — left leg */}
          <path d="M18 8L8 28" stroke="white" strokeWidth="3.5" strokeLinecap="round"/>
          {/* A — right leg */}
          <path d="M18 8L28 28" stroke="white" strokeWidth="3.5" strokeLinecap="round"/>
          {/* A — crossbar */}
          <path d="M12.5 21H23.5" stroke="white" strokeWidth="3" strokeLinecap="round"/>
          {/* spark dot above peak */}
          <circle cx="18" cy="6" r="2" fill="#fcd34d"/>
        </svg>
        <span className={styles.logoText}><strong>Aptify</strong></span>
      </div>

      {/* Nav */}
      <nav className={styles.nav}>
        {NAV_ITEMS.map(item => {
          if (item.soon) {
            return (
              <div key={item.label} className={styles.itemDisabled}>
                <item.Icon size={16} className={styles.itemIcon} />
                <span className={styles.itemLabel}>{item.label}</span>
                <span className={styles.soon}>Soon</span>
              </div>
            )
          }
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              onClick={onClose}
              className={({ isActive }) =>
                `${styles.item} ${isActive ? styles.itemActive : ''}`
              }
            >
              <item.Icon size={16} className={styles.itemIcon} />
              <span className={styles.itemLabel}>{item.label}</span>
            </NavLink>
          )
        })}
      </nav>

      {/* User widget at bottom */}
      <div className={styles.userWidget}>
        {user ? (
          <>
            <div className={styles.userInfo}>
              {user.picture
                ? <img src={user.picture} alt={user.name} className={styles.avatar} />
                : <div className={styles.avatarFallback}>{(user.name || user.email)[0].toUpperCase()}</div>
              }
              <div className={styles.userText}>
                <span className={styles.userName}>{user.name || user.email}</span>
                <span className={styles.userEmail}>{user.email}</span>
              </div>
            </div>
            <button onClick={logout} className={styles.logoutBtn}>Sign out</button>
          </>
        ) : (
          <a href="/login" className={styles.signInBtn}>Sign In</a>
        )}
      </div>
    </aside>

    {/* Bottom navigation — visible only on mobile (CSS handles show/hide) */}
    <nav className={styles.bottomNav}>
      {BOTTOM_NAV_ITEMS.map(item => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.exact}
          className={({ isActive }) =>
            `${styles.bottomNavItem} ${isActive ? styles.bottomNavItemActive : ''}`
          }
        >
          <item.Icon size={20} />
          <span>{item.label === 'Practice Exams' ? 'Practice' : item.label}</span>
        </NavLink>
      ))}
    </nav>
    </>
  )
}
