import { createContext, useContext, useEffect, useState } from 'react'
import log from '../lib/logger'

const AuthContext = createContext(null)

/**
 * Wraps the app and makes the logged-in user available everywhere via useAuth().
 *
 * user states:
 *   undefined  → still loading (show spinner / nothing)
 *   null       → not logged in
 *   { id, email, name, picture } → logged in
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined)

  useEffect(() => {
    log.debug('auth check started')
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data) {
          log.info('auth check — logged in', { userId: data.id, email: data.email })
        } else {
          log.info('auth check — not logged in')
        }
        setUser(data)
      })
      .catch(error => {
        log.error('auth check failed', { error })
        setUser(null)
      })
  }, [])

  function logout() {
    log.info('logout initiated')
    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
      .finally(() => {
        setUser(null)
        window.location.href = '/login'
      })
  }

  return (
    <AuthContext.Provider value={{ user, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
