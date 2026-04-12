import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import styles from './LoginPage.module.css'
import log from '../lib/logger'

const IS_LOCAL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'

export default function LoginPage() {
  const { user, setUser } = useAuth()
  const navigate = useNavigate()

  // Already logged in — skip to dashboard
  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  // Dev-only: call /dev/login, then update AuthContext and redirect
  async function handleDevLogin() {
    log.info('dev login initiated')
    try {
      const res = await fetch('/dev/login', { method: 'POST', credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        log.info('dev login success', { email: data.email })
        setUser(data)
        navigate('/', { replace: true })
      } else {
        log.warn('dev login failed', { status: res.status })
      }
    } catch (err) {
      log.error('dev login error', { error: err })
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        {/* Logo / brand */}
        <div className={styles.brand}>
          <svg className={styles.brandIcon} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="ag" x1="0" y1="0" x2="36" y2="36" gradientUnits="userSpaceOnUse">
                <stop stopColor="#fbbf24"/>
                <stop offset="1" stopColor="#92400e"/>
              </linearGradient>
            </defs>
            <rect width="36" height="36" rx="10" fill="url(#ag)"/>
            <path d="M18 8L8 28" stroke="white" strokeWidth="3.5" strokeLinecap="round"/>
            <path d="M18 8L28 28" stroke="white" strokeWidth="3.5" strokeLinecap="round"/>
            <path d="M12.5 21H23.5" stroke="white" strokeWidth="3" strokeLinecap="round"/>
            <circle cx="18" cy="6" r="2" fill="#fcd34d"/>
          </svg>
          <span className={styles.brandName}>Aptify</span>
        </div>

        <h1 className={styles.title}>Welcome back</h1>
        <p className={styles.subtitle}>Sign in to continue your SAT practice</p>

        {/* Google OAuth — Spring Security handles the flow */}
        <a
          href="/oauth2/authorization/google"
          className={styles.googleBtn}
        >
          <GoogleIcon />
          <span>Continue with Google</span>
        </a>

        {/* Dev login — only visible on localhost */}
        {IS_LOCAL && (
          <button className={styles.devBtn} onClick={handleDevLogin}>
            ⚡ Dev login (local only)
          </button>
        )}

        <p className={styles.legal}>
          By signing in you agree to practice hard and score well.
        </p>
      </div>
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg className={styles.googleIcon} viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
  )
}
