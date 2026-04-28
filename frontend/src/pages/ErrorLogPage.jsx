import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import MathText from '../components/MathText/MathText'
import styles from './ErrorLogPage.module.css'

const DOMAIN_LABELS = {
  algebra:               'Algebra',
  advanced_math:         'Advanced Math',
  problem_solving_data:  'Problem Solving & Data',
  geometry_trigonometry: 'Geometry & Trig',
  information_ideas:     'Information & Ideas',
  craft_structure:       'Craft & Structure',
  expression_ideas:      'Expression of Ideas',
  standard_english:      'Standard English',
}

const DIFF_LABELS = { 1: 'Easy', 2: 'Medium', 3: 'Hard' }

function fmtDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function timeStr(s) {
  if (s == null) return null
  return s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60}s`
}

export default function ErrorLogPage() {
  const [items,   setItems]   = useState([])
  const [loading, setLoading] = useState(true)
  const [filter,  setFilter]  = useState({ domain: '', difficulty: '' })

  useEffect(() => {
    fetch('/api/error-log')
      .then(r => r.ok ? r.json() : [])
      .then(data => { setItems(data ?? []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const domains = [...new Set(items.map(i => i.domain).filter(Boolean))].sort()

  const filtered = items.filter(item => {
    if (filter.domain     && item.domain !== filter.domain)             return false
    if (filter.difficulty && String(item.difficulty) !== filter.difficulty) return false
    return true
  })

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Error Log</h1>
        <p className={styles.sub}>Every mistake you make is future you getting smarter.</p>
      </div>

      {/* ── Filter bar ── */}
      <div className={styles.filterBar}>
        <select
          className={styles.filterSelect}
          value={filter.domain}
          onChange={e => setFilter(f => ({ ...f, domain: e.target.value }))}
        >
          <option value="">All Domains</option>
          {domains.map(d => (
            <option key={d} value={d}>{DOMAIN_LABELS[d] ?? d}</option>
          ))}
        </select>

        <select
          className={styles.filterSelect}
          value={filter.difficulty}
          onChange={e => setFilter(f => ({ ...f, difficulty: e.target.value }))}
        >
          <option value="">All Difficulties</option>
          <option value="1">Easy</option>
          <option value="2">Medium</option>
          <option value="3">Hard</option>
        </select>

        {(filter.domain || filter.difficulty) && (
          <button
            className={styles.clearBtn}
            onClick={() => setFilter({ domain: '', difficulty: '' })}
          >
            Clear filters
          </button>
        )}

        <span className={styles.resultCount}>
          {loading ? '…' : `${filtered.length} question${filtered.length !== 1 ? 's' : ''}`}
        </span>
      </div>

      {/* ── List ── */}
      {loading ? (
        <div className={styles.skeletonList}>
          {[1,2,3,4,5].map(i => <div key={i} className={styles.skeletonCard} />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className={styles.empty}>
          {items.length === 0
            ? 'No wrong answers yet. Keep practicing!'
            : 'No results match the selected filters.'
          }
        </div>
      ) : (
        <div className={styles.list}>
          {filtered.map((item, idx) => {
            const diffLabel   = DIFF_LABELS[item.difficulty] ?? 'Unknown'
            const domainLabel = DOMAIN_LABELS[item.domain] ?? item.domain
            const ts          = timeStr(item.timeSpentSeconds)
            return (
              <div key={`${item.questionId}-${idx}`} className={styles.card}>
                {/* Meta row */}
                <div className={styles.cardMeta}>
                  <span className={`${styles.diffBadge} ${styles[`diff_${diffLabel.toLowerCase()}`]}`}>
                    {diffLabel}
                  </span>
                  {ts && <span className={styles.metaItem}>{ts}</span>}
                  <span className={styles.metaSep}>·</span>
                  <span className={styles.metaItem}>{domainLabel}</span>
                  <span className={styles.metaSep}>·</span>
                  <span className={styles.metaItem}>{fmtDate(item.answeredAt)}</span>
                </div>

                {/* Question stem */}
                <div className={styles.cardStem}>
                  <MathText text={item.questionStem ?? ''} as="div" />
                </div>

                {/* Answer row */}
                <div className={styles.cardFooter}>
                  <div className={styles.cardAnswers}>
                    <span className={styles.wrongAnswer}>
                      Your answer: <strong>{item.studentAnswer ?? '—'}</strong>
                    </span>
                    <span className={styles.arrow}>→</span>
                    <span className={styles.correctAnswer}>
                      Correct: <strong>{item.correctAnswer ?? '—'}</strong>
                    </span>
                  </div>
                  <Link
                    to={`/session/${item.sessionId}/review/0`}
                    className={styles.sessionLink}
                  >
                    View session →
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
