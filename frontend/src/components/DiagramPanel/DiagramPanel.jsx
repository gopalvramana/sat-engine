import { useEffect, useRef } from 'react'

/**
 * Renders a programmatic SVG/Canvas diagram by calling window.renderDiagram()
 * from the shared renderer.js (loaded as a global script in index.html).
 *
 * Props:
 *   diagramJson — raw JSON string or object from the question's diagramJson field
 */
export default function DiagramPanel({ diagramJson }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!diagramJson || !containerRef.current) return

    let cfg
    try {
      cfg = typeof diagramJson === 'string' ? JSON.parse(diagramJson) : diagramJson
    } catch {
      return
    }

    const el = containerRef.current
    el.innerHTML = ''

    if (typeof window.renderDiagram === 'function') {
      window.renderDiagram(cfg, el)
    } else {
      // renderer.js not loaded yet — retry after a short delay
      const t = setTimeout(() => {
        if (typeof window.renderDiagram === 'function') {
          window.renderDiagram(cfg, el)
        }
      }, 200)
      return () => clearTimeout(t)
    }
  }, [diagramJson])

  if (!diagramJson) return null

  return (
    <div
      ref={containerRef}
      style={{
        display: 'flex',
        justifyContent: 'center',
        margin: '12px 0',
        padding: '12px',
        background: '#f8fafc',
        borderRadius: 8,
        border: '1px solid #e2e8f0',
      }}
    />
  )
}
