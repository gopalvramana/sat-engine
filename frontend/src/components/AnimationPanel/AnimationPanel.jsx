import { useEffect, useRef } from 'react'
import styles from './AnimationPanel.module.css'

/**
 * Renders the animated step-by-step diagram walkthrough.
 *
 * Delegates entirely to window.renderAnimation(cfg, containerEl, opts) from renderer.js.
 * The renderer injects its own SVG, controls, caption, and CSS.
 *
 * Props:
 *   animationJson — raw JSON string / object from question.animationJson
 *   synced        — true = synced mode (no prev/next on player; controlled by StepNavigator)
 *   onReady(uid)  — called with the player uid after render (for external animGoTo calls)
 */
export default function AnimationPanel({ animationJson, synced, onReady }) {
  const containerRef = useRef(null)

  useEffect(() => {
    const el = containerRef.current
    if (!animationJson || !el) return

    let cfg
    try {
      cfg = typeof animationJson === 'string' ? JSON.parse(animationJson) : animationJson
    } catch { return }

    if (!cfg?.frames?.length) return

    function mount() {
      if (typeof window.renderAnimation === 'function') {
        el.innerHTML = ''
        const uid = window.renderAnimation(cfg, el, { synced: !!synced })
        if (uid && onReady) onReady(uid)
      }
    }

    if (window.renderAnimation) {
      mount()
    } else {
      // renderer.js loads with defer — retry until available
      const t = setInterval(() => {
        if (window.renderAnimation) { clearInterval(t); mount() }
      }, 100)
      return () => clearInterval(t)
    }

    return () => { if (el) el.innerHTML = '' }
  }, [animationJson])

  return (
    <div className={`${styles.wrap} ${synced ? styles.synced : ''}`}>
      {!synced && <div className={styles.label}>ANIMATION</div>}
      <div ref={containerRef} />
    </div>
  )
}
