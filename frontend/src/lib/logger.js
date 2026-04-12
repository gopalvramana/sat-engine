/**
 * Centralised frontend logger.
 *
 * In production (import.meta.env.PROD) debug logs are suppressed.
 * Every log line is prefixed with [Aptify] and a timestamp.
 *
 * Usage:
 *   import log from '../lib/logger'
 *   log.info('session started', { sessionId })
 *   log.debug('phase transition', { from: 'loading', to: 'question' })
 *   log.warn('retrying request', { url, attempt })
 *   log.error('api failed', { url, status, error })
 */

const isProd = typeof import.meta !== 'undefined' && import.meta.env?.PROD

function ts() {
  return new Date().toISOString().slice(11, 23) // HH:mm:ss.mmm
}

function fmt(level, msg, data) {
  const prefix = `[Aptify ${ts()}] ${level.toUpperCase().padEnd(5)}`
  return data !== undefined ? [prefix, msg, data] : [prefix, msg]
}

const log = {
  debug: (msg, data) => { if (!isProd) console.debug(...fmt('debug', msg, data)) },
  info:  (msg, data) => { console.info(...fmt('info',  msg, data)) },
  warn:  (msg, data) => { console.warn(...fmt('warn',  msg, data)) },
  error: (msg, data) => { console.error(...fmt('error', msg, data)) },
}

export default log
