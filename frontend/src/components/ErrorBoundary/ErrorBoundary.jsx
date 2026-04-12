import { Component } from 'react'
import log from '../../lib/logger'
import { Sentry } from '../../lib/sentry.js'

/**
 * Catches unhandled React render errors and logs them.
 * Wrap around top-level app or individual risky components.
 *
 * Usage:
 *   <ErrorBoundary fallback={<div>Something went wrong</div>}>
 *     <YourComponent />
 *   </ErrorBoundary>
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    log.error('React render error caught by ErrorBoundary', {
      error: error.message,
      stack: error.stack?.split('\n').slice(0, 5).join(' | '),
      componentStack: info.componentStack?.split('\n').slice(0, 5).join(' | '),
    })
    // Forward to Sentry with full React component stack — safe no-op if Sentry not initialised
    Sentry.withScope(scope => {
      scope.setExtra('componentStack', info.componentStack)
      Sentry.captureException(error)
    })
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div style={{ padding: 40, textAlign: 'center', fontFamily: 'system-ui' }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#ef4444', marginBottom: 8 }}>
            Something went wrong
          </div>
          <div style={{ fontSize: 13, color: '#64748b', marginBottom: 16 }}>
            {this.state.error?.message}
          </div>
          <button
            onClick={() => window.location.href = '/app/'}
            style={{ padding: '8px 20px', background: '#d97706', color: '#fff', border: 'none', borderRadius: 8, cursor: 'pointer' }}
          >
            Back to Dashboard
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
