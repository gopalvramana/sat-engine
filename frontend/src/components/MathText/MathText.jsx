import { useState, useEffect } from 'react'
import katex from 'katex'
import 'katex/dist/katex.min.css'

/**
 * Renders a string that may contain LaTeX math.
 * Supported delimiters: \(...\), \[...\], and $...$ (with currency filter).
 *
 * Uses window.katex.renderToString() to produce the final HTML string
 * synchronously — no DOM post-processing, so React re-renders can't wipe it.
 */

/** Returns true if the content between $ $ is math rather than currency/prose */
function isMathContent(inner) {
  // Has LaTeX commands like \frac, \sqrt, \cdot …
  if (/\\[a-zA-Z]/.test(inner)) return true
  // Has math operators / comparison symbols
  if (/[<>=+\-*/^_{}[\]|≤≥±∈∉∀∃→←↔~]/.test(inner)) return true
  // Single token with no spaces (variable like m, x, n) but NOT a plain number like 50
  if (!/\s/.test(inner) && !/^\d+$/.test(inner.trim())) return true
  return false
}

/** Parse `text` and replace math delimiters with KaTeX-rendered HTML */
function applyKatex(text) {
  if (!text) return ''

  // Combined pattern: \[...\] display | \(...\) inline | $...$ inline (with isMathContent guard)
  const re = /(\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$(?:[^$\\]|\\.)+?\$)/g
  let result = ''
  let lastIndex = 0
  let match

  while ((match = re.exec(text)) !== null) {
    // plain text before this math block
    result += escapeHtml(text.slice(lastIndex, match.index))

    const full = match[1]
    let isDisplay = false
    let inner

    if (full.startsWith('\\[')) {
      isDisplay = true
      inner = full.slice(2, -2)
    } else if (full.startsWith('\\(')) {
      isDisplay = false
      inner = full.slice(2, -2)
    } else {
      // $...$ — only treat as math if content looks mathematical
      inner = full.slice(1, -1)
      if (!isMathContent(inner)) {
        result += escapeHtml(full)
        lastIndex = match.index + full.length
        continue
      }
      isDisplay = false
    }

    try {
      result += katex.renderToString(inner.trim(), {
        displayMode: isDisplay,
        throwOnError: false,
        trust: false,
      })
    } catch {
      result += escapeHtml(full)
    }

    lastIndex = match.index + full.length
  }

  result += escapeHtml(text.slice(lastIndex))
  return result
}

/**
 * Escape HTML in plain-text segments, then re-allow safe structural tags
 * (table/thead/tbody/tr/th/td/br) so question stems with embedded tables render.
 * Also converts \n (literal backslash-n or newline) to <br>.
 */
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    // Un-escape safe structural tags
    .replace(/&lt;(\/?)(table|thead|tbody|tr|th|td|br)(\s[^&>]*)? *&gt;/gi,
      (_, slash, tag, attrs) => `<${slash}${tag}${attrs || ''}>`)
    // Literal \n or actual newline → <br>
    .replace(/\\n/g, '<br>')
    .replace(/\n/g, '<br>')
}

export default function MathText({ text, as: Tag = 'span', style, className }) {
  const [html, setHtml] = useState(() => applyKatex(text))

  useEffect(() => {
    setHtml(applyKatex(text))
  }, [text])

  if (!text) return null
  return (
    <Tag
      dangerouslySetInnerHTML={{ __html: html }}
      style={style}
      className={className}
    />
  )
}
