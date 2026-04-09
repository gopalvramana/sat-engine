import { useState, useEffect, useCallback } from 'react'
import { getQuestionCounts } from '../api/client'
import styles from './HomePage.module.css'

/* ── Domain definitions ─────────────────────────────────────────── */
const MATH_DOMAINS = [
  { key: 'algebra',               label: 'Algebra',               icon: '𝑥' },
  { key: 'advanced_math',         label: 'Advanced Math',          icon: '∫' },
  { key: 'problem_solving_data',  label: 'Problem Solving & Data', icon: '📊' },
  { key: 'geometry_trigonometry', label: 'Geometry & Trig',        icon: '△' },
]
const RW_DOMAINS = [
  { key: 'information_ideas', label: 'Information & Ideas', icon: '💡' },
  { key: 'craft_structure',   label: 'Craft & Structure',   icon: '🔧' },
  { key: 'expression_ideas',  label: 'Expression of Ideas', icon: '✏️' },
  { key: 'standard_english',  label: 'Standard English',    icon: '📝' },
]
const ALL_DOMAINS = [...MATH_DOMAINS, ...RW_DOMAINS]

function getDomainsForSection(section) {
  if (section === 'math')            return MATH_DOMAINS
  if (section === 'reading_writing') return RW_DOMAINS
  return ALL_DOMAINS
}

/* ── Difficulty bands ───────────────────────────────────────────── */
const DIFFICULTIES = [
  { key: 'easy',   label: 'Easy',   min: 1, max: 2, color: '#16a34a' },
  { key: 'medium', label: 'Medium', min: 3, max: 5, color: '#d97706' },
  { key: 'hard',   label: 'Hard',   min: 6, max: 7, color: '#dc2626' },
]

/* ── Compute min/max difficulty from selected bands ─────────────── */
function difficultyRange(selectedBands) {
  const active = DIFFICULTIES.filter(d => selectedBands.has(d.key))
  if (!active.length) return { min: 1, max: 7 }
  return {
    min: Math.min(...active.map(d => d.min)),
    max: Math.max(...active.map(d => d.max)),
  }
}

/* ── Distribute N questions evenly across selected domains ──────── */
function buildDomainCounts(domains, total) {
  if (!domains.length) return {}
  const base = Math.floor(total / domains.length)
  const extra = total % domains.length
  return Object.fromEntries(domains.map((d, i) => [d.key, base + (i < extra ? 1 : 0)]))
}

export default function HomePage({ onStart }) {
  // ── Filter state ──────────────────────────────────────────────
  const [section, setSection]         = useState('math')
  const [diffBands, setDiffBands]     = useState(new Set(['easy', 'medium', 'hard']))
  const [domains, setDomains]         = useState(new Set(MATH_DOMAINS.map(d => d.key)))
  const [sessionLen, setSessionLen]   = useState(10)

  // ── Available counts from API ─────────────────────────────────
  const [counts, setCounts]   = useState({})   // { domain: count }
  const [loading, setLoading] = useState(false)

  // ── Fetch counts whenever filters change ─────────────────────
  const fetchCounts = useCallback(async () => {
    setLoading(true)
    try {
      const { min, max } = difficultyRange(diffBands)
      const data = await getQuestionCounts(section || null, min, max)
      setCounts(data.byDomain || {})
    } catch {
      setCounts({})
    } finally {
      setLoading(false)
    }
  }, [section, diffBands])

  useEffect(() => { fetchCounts() }, [fetchCounts])

  // ── When section changes, reset domain selection ──────────────
  function handleSectionChange(val) {
    setSection(val)
    setDomains(new Set(getDomainsForSection(val).map(d => d.key)))
  }

  function toggleDiff(key) {
    setDiffBands(prev => {
      const next = new Set(prev)
      if (next.has(key)) { if (next.size > 1) next.delete(key) } // keep at least one
      else next.add(key)
      return next
    })
  }

  function toggleDomain(key) {
    setDomains(prev => {
      const next = new Set(prev)
      if (next.has(key)) { if (next.size > 1) next.delete(key) } // keep at least one
      else next.add(key)
      return next
    })
  }

  // ── Derived values ────────────────────────────────────────────
  const visibleDomains    = getDomainsForSection(section)
  const selectedDomains   = visibleDomains.filter(d => domains.has(d.key))
  const totalAvailable    = selectedDomains.reduce((s, d) => s + (counts[d.key] || 0), 0)
  const cappedLen         = Math.min(sessionLen, totalAvailable)
  const canStart          = totalAvailable > 0 && cappedLen > 0

  function handleStart() {
    const { min, max } = difficultyRange(diffBands)
    const domainCounts = buildDomainCounts(selectedDomains, cappedLen)
    onStart({ section: section || null, domainCounts, minDifficulty: min, maxDifficulty: max })
  }

  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <div className={styles.badge}>SAT Practice</div>
        <h1 className={styles.title}>Build Your Session</h1>
        <p className={styles.sub}>Choose your section, topics, and difficulty to get started.</p>
      </div>

      {/* ── Section ─────────────────────────────────────────────── */}
      <div className={styles.card}>
        <div className={styles.cardLabel}>Section</div>
        <div className={styles.segmented}>
          {[
            { value: 'math',            label: 'Math' },
            { value: 'reading_writing', label: 'Reading & Writing' },
            { value: null,              label: 'Both' },
          ].map(s => (
            <button
              key={String(s.value)}
              className={`${styles.seg} ${section === s.value ? styles.segActive : ''}`}
              onClick={() => handleSectionChange(s.value)}
            >{s.label}</button>
          ))}
        </div>
      </div>

      {/* ── Difficulty ──────────────────────────────────────────── */}
      <div className={styles.card}>
        <div className={styles.cardLabel}>Difficulty</div>
        <div className={styles.diffRow}>
          {DIFFICULTIES.map(d => (
            <button
              key={d.key}
              className={`${styles.diffChip} ${diffBands.has(d.key) ? styles.diffChipActive : ''}`}
              style={diffBands.has(d.key) ? { '--chip-color': d.color } : {}}
              onClick={() => toggleDiff(d.key)}
            >
              <span className={styles.diffDot} style={{ background: d.color }} />
              {d.label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Topics ──────────────────────────────────────────────── */}
      <div className={styles.card}>
        <div className={styles.cardLabelRow}>
          <span className={styles.cardLabel}>Topics</span>
          <button
            className={styles.selectAll}
            onClick={() => setDomains(new Set(visibleDomains.map(d => d.key)))}
          >Select all</button>
        </div>
        <div className={styles.domainList}>
          {visibleDomains.map(d => {
            const avail   = counts[d.key] || 0
            const checked = domains.has(d.key)
            return (
              <button
                key={d.key}
                className={`${styles.domainRow} ${checked ? styles.domainChecked : ''}`}
                onClick={() => toggleDomain(d.key)}
              >
                <span className={`${styles.checkbox} ${checked ? styles.checkboxOn : ''}`}>
                  {checked && '✓'}
                </span>
                <span className={styles.domainIcon}>{d.icon}</span>
                <span className={styles.domainLabel}>{d.label}</span>
                <span className={`${styles.domainCount} ${loading ? styles.dimmed : ''}`}>
                  {loading ? '…' : avail}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* ── Session length ──────────────────────────────────────── */}
      <div className={styles.card}>
        <div className={styles.cardLabelRow}>
          <span className={styles.cardLabel}>Questions</span>
          <span className={styles.lenValue}>{cappedLen}</span>
        </div>
        <input
          type="range"
          className={styles.slider}
          min={5}
          max={Math.max(20, totalAvailable)}
          step={1}
          value={sessionLen}
          onChange={e => setSessionLen(Number(e.target.value))}
        />
        <div className={styles.sliderLabels}>
          <span>5</span>
          <span className={`${styles.availBadge} ${totalAvailable === 0 ? styles.availNone : ''}`}>
            {totalAvailable} available
          </span>
          <span>{Math.max(20, totalAvailable)}</span>
        </div>
      </div>

      {/* ── Start ───────────────────────────────────────────────── */}
      <div className={styles.startRow}>
        <button
          className={styles.startBtn}
          onClick={handleStart}
          disabled={!canStart}
        >
          Start Practice →
        </button>
        {!canStart && totalAvailable === 0 && (
          <p className={styles.noQMsg}>No questions match your filters. Try adjusting difficulty or topics.</p>
        )}
      </div>
    </div>
  )
}
