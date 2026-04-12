import { createContext, useContext, useEffect, useState } from 'react'

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
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => setUser(data))
      .catch(() => setUser(null))
  }, [])

  function logout() {
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
