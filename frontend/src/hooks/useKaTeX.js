import { useEffect } from 'react'

/**
 * Runs KaTeX auto-render on a ref after content changes.
 * Mirrors the scheduleKaTeX / renderKaTeXIn pattern from practice.js.
 */
export function useKaTeX(ref, deps = []) {
  useEffect(() => {
    if (!ref.current) return
    const el = ref.current

    function render() {
      if (window.renderMathInElement) {
        window.renderMathInElement(el, {
          delimiters: [
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true  },
          ],
          throwOnError: false,
        })
      } else {
        // KaTeX not loaded yet — queue for when it arrives
        window._pendingKatex = window._pendingKatex || []
        window._pendingKatex.push(el)
      }
    }

    // Small delay so DOM is fully painted before render
    const t = setTimeout(render, 30)
    return () => clearTimeout(t)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
