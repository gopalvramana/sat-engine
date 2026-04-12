import * as Sentry from '@sentry/react'

/**
 * Initialize Sentry for frontend error tracking.
 *
 * Only activates when VITE_SENTRY_DSN is set — safe to import in dev without a DSN.
 * Call this ONCE, before React renders, in main.jsx.
 *
 * Environment variables needed on Railway:
 *   VITE_SENTRY_DSN       — the DSN from your Sentry project Settings → Client Keys
 *   VITE_APP_ENV          — "production" | "staging" (defaults to "development")
 */
export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn) return   // no DSN → Sentry is a silent no-op; safe in local dev

  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_APP_ENV || 'development',

    // Error capture is free on every Sentry plan.
    // Performance tracing (traces-sample-rate > 0) costs quota — enable when needed.
    tracesSampleRate: 0,

    // Attach console logs as breadcrumbs so you see what the user was doing before a crash.
    integrations: [
      Sentry.breadcrumbsIntegration({ console: true, fetch: true, xhr: true }),
    ],

    // Don't send errors that come from browser extensions or unrelated third-party scripts.
    ignoreErrors: [
      'ResizeObserver loop limit exceeded',
      'Non-Error promise rejection captured',
    ],
  })
}

// Re-export so callers don't need to import Sentry directly.
export { Sentry }
