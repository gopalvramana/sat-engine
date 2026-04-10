import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Count-up timer for per-question timing.
 *
 * Returns:
 *   seconds   – elapsed seconds (live, updates every second while running)
 *   start()   – begin / restart the timer
 *   stop()    – freeze the timer, returns elapsed seconds at that moment
 *   reset()   – stop + zero
 */
export function useTimer() {
  const [seconds, setSeconds] = useState(0)
  const [running, setRunning] = useState(false)
  const startRef = useRef(null)    // timestamp when current run began
  const baseRef  = useRef(0)       // accumulated seconds from previous runs

  useEffect(() => {
    if (!running) return
    const id = setInterval(() => {
      setSeconds(baseRef.current + Math.floor((Date.now() - startRef.current) / 1000))
    }, 500) // 500ms interval is plenty smooth for a seconds display
    return () => clearInterval(id)
  }, [running])

  const start = useCallback(() => {
    baseRef.current  = 0
    startRef.current = Date.now()
    setSeconds(0)
    setRunning(true)
  }, [])

  const stop = useCallback(() => {
    const elapsed = baseRef.current + Math.floor((Date.now() - (startRef.current ?? Date.now())) / 1000)
    setRunning(false)
    baseRef.current = elapsed
    setSeconds(elapsed)
    return elapsed
  }, [])

  const reset = useCallback(() => {
    setRunning(false)
    baseRef.current = 0
    setSeconds(0)
  }, [])

  return { seconds, running, start, stop, reset }
}

/** Format seconds → "0:42" or "1:05" */
export function formatTime(secs) {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}
