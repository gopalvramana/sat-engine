import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

/**
 * Route guard — wraps protected routes.
 *
 * States:
 *   user === undefined  → still loading /api/auth/me; show nothing (avoids flicker)
 *   user === null       → not logged in; redirect to /login
 *   user is an object   → authenticated; render children via <Outlet />
 */
export default function RequireAuth() {
  const { user } = useAuth()

  if (user === undefined) {
    // Auth check in flight — render nothing to avoid redirect flicker
    return null
  }

  if (user === null) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
