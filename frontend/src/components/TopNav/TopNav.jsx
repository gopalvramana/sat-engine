import { NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import styles from './TopNav.module.css'

const NAV_ITEMS = [
  { path: '/study-plan', label: 'Study Plan' },
  { path: '/analytics',  label: 'Analytics'  },
  { path: '/error-log',  label: 'Error Log'  },
  { path: '/history',    label: 'History'    },
]

export default function TopNav() {
  const { user, logout } = useAuth()
  const initials = user?.name
    ? user.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
    : (user?.email?.[0] ?? '?').toUpperCase()

  return (
    <header className={styles.nav}>
      <div className={styles.inner}>
        {/* Logo */}
        <NavLink to="/study-plan" className={styles.logo}>
          <svg className={styles.logoMark} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Background */}
            <rect width="36" height="36" rx="9" fill="#0a0a0a"/>

            {/* Ambient star field — subtle depth */}
            <circle cx="6.5"  cy="10"   r="0.9" fill="white" fillOpacity="0.18"/>
            <circle cx="29.5" cy="14"   r="0.75" fill="white" fillOpacity="0.15"/>
            <circle cx="25"   cy="7.5"  r="0.7" fill="white" fillOpacity="0.14"/>
            <circle cx="7.5"  cy="24"   r="0.65" fill="white" fillOpacity="0.12"/>
            <circle cx="30"   cy="27"   r="0.8" fill="white" fillOpacity="0.13"/>

            {/* Constellation lines (A shape) */}
            <line x1="18" y1="8.5"  x2="10"   y2="27" stroke="white" strokeWidth="1.1" strokeLinecap="round" opacity="0.35"/>
            <line x1="18" y1="8.5"  x2="26"   y2="27" stroke="white" strokeWidth="1.1" strokeLinecap="round" opacity="0.35"/>
            <line x1="13" y1="21"   x2="23"   y2="21" stroke="white" strokeWidth="1.1" strokeLinecap="round" opacity="0.35"/>

            {/* Constellation nodes — apex brightest */}
            <circle cx="18" cy="8.5" r="2.8" fill="white"/>
            <circle cx="10" cy="27"  r="1.9" fill="white" fillOpacity="0.55"/>
            <circle cx="26" cy="27"  r="1.9" fill="white" fillOpacity="0.55"/>
          </svg>

          <span className={styles.logoText}>
            <span className={styles.logoApt}>Apt</span><span className={styles.logoIfy}>ify</span>
          </span>
        </NavLink>

        {/* Nav links */}
        <nav className={styles.links}>
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `${styles.link} ${isActive ? styles.linkActive : ''}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Right: user avatar + sign out */}
        <div className={styles.right}>
          <div className={styles.userMenu}>
            {user?.picture
              ? <img src={user.picture} alt={user.name} className={styles.avatar} />
              : <div className={styles.avatarFallback}>{initials}</div>
            }
            <button onClick={logout} className={styles.logoutBtn}>Sign out</button>
          </div>
        </div>
      </div>
    </header>
  )
}
