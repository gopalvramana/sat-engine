import { useState, useEffect, useCallback } from 'react'
import { getQuestionCounts } from '../api/client'
import styles from './HomePage.module.css'

/* ── Domain definitions ─────────────────────────────────────────── */
const MATH_DOMAINS = [
  { key: 'algebra',               label: 'Algebra',                icon: '𝑥' },
  { key: 'advanced_math',         label: 'Advanced Math',           icon: '∫' },
  { key: 'problem_solving_data',  label: 'Problem Solving & Data',  icon: '📊' },
  { key: 'geometry_trigonometry', label: 'Geometry & Trig',         icon: '△' },
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
const BANDS = [
  { key: 'easy',   label: 'Easy',   color: '#16a34a', min: 1, max: 2 },
  { key: 'medium', label: 'Medium', color: '#d97706', min: 3, max: 5 },
  { key: 'hard',   label: 'Hard',   color: '#dc2626', min: 6, max: 7 },
]

/* ── Build default per-domain difficulty state ──────────────────── */
function defaultDiffState(domains) {
  return Object.fromEntries(domains.map(d => [d.key, new Set(['easy', 'medium', 'hard'])]))
}

/* ── Count available questions for a domain given selected bands ── */
function availableForDomain(counts, domain, selectedBands) {
  const dc = counts[domain]
  if (!dc) return 0
  return [...selectedBands].reduce((s, b) => s + (dc[b] || 0), 0)
}

/* ── Compute domainDifficulties for the API from per-domain bands ─ */
function buildDomainDifficulties(diffState) {
  const result = {}
  for (const [domain, bands] of Object.entries(diffState)) {
    const active = BANDS.filter(b => bands.has(b.key))
    if (!active.length) continue
    result[domain] = {
      min: Math.min(...active.map(b => b.min)),
      max: Math.max(...active.map(b => b.max)),
    }
  }
  return result
}

/* ── Distribute N questions evenly across selected domains ──────── */
function buildDomainCounts(domains, total) {
  if (!domains.length) return {}
  const base  = Math.floor(total / domains.length)
  const extra = total % domains.length
  return Object.fromEntries(domains.map((d, i) => [d.key, base + (i < extra ? 1 : 0)]))
}

export default function HomePage({ onStart }) {
  const [section,    setSection]    = useState('math')
  const [diffState,  setDiffState]  = useState(() => defaultDiffState(MATH_DOMAINS))
  const [domains,    setDomains]    = useState(() => new Set(MATH_DOMAINS.map(d => d.key)))
  const [sessionLen, setSessionLen] = useState(10)
  const [counts,     setCounts]     = useState({})   // { domain: { easy, medium, hard, total } }
  const [loading,    setLoading]    = useState(false)

  /* Fetch counts when section changes */
  const fetchCounts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getQuestionCounts(section || null)
      setCounts(data.byDomain || {})
    } catch { setCounts({}) }
    finally { setLoading(false) }
  }, [section])

  useEffect(() => { fetchCounts() }, [fetchCounts])

  /* Reset domains + diff when section changes */
  function handleSectionChange(val) {
    const doms = getDomainsForSection(val)
    setSection(val)
    setDomains(new Set(doms.map(d => d.key)))
    setDiffState(defaultDiffState(doms))
  }

  function toggleDomain(key) {
    setDomains(prev => {
      const next = new Set(prev)
      if (next.has(key)) { if (next.size > 1) next.delete(key) }
      else next.add(key)
      return next
    })
  }

  function toggleBand(domainKey, bandKey) {
    setDiffState(prev => {
      const cur  = new Set(prev[domainKey] || BANDS.map(b => b.key))
      const next = new Set(cur)
      if (next.has(bandKey)) { if (next.size > 1) next.delete(bandKey) }
      else next.add(bandKey)
      return { ...prev, [domainKey]: next }
    })
  }

  /* Derived */
  const visibleDomains  = getDomainsForSection(section)
  const selectedDomains = visibleDomains.filter(d => domains.has(d.key))
  const totalAvailable  = selectedDomains.reduce(
    (s, d) => s + availableForDomain(counts, d.key, diffState[d.key] || new Set(['easy','medium','hard'])), 0
  )
  const cappedLen = Math.min(sessionLen, totalAvailable)
  const canStart  = totalAvailable > 0 && cappedLen > 0

  function handleStart() {
    const domainCounts       = buildDomainCounts(selectedDomains, cappedLen)
    const domainDifficulties = buildDomainDifficulties(
      Object.fromEntries(selectedDomains.map(d => [d.key, diffState[d.key] || new Set(['easy','medium','hard'])]))
    )
    onStart({ section: section || null, domainCounts, domainDifficulties })
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

      {/* ── Topics with per-topic difficulty ────────────────────── */}
      <div className={styles.card}>
        <div className={styles.cardLabelRow}>
          <span className={styles.cardLabel}>Topics & Difficulty</span>
          <button
            className={styles.selectAll}
            onClick={() => setDomains(new Set(visibleDomains.map(d => d.key)))}
          >Select all</button>
        </div>
        <div className={styles.domainList}>
          {visibleDomains.map(d => {
            const checked  = domains.has(d.key)
            const bands    = diffState[d.key] || new Set(['easy','medium','hard'])
            const avail    = availableForDomain(counts, d.key, bands)
            return (
              <div key={d.key} className={`${styles.domainBlock} ${checked ? styles.domainBlockChecked : ''}`}>
                {/* ── Topic header row ── */}
                <button
                  className={styles.domainRow}
                  onClick={() => toggleDomain(d.key)}
                >
                  <span className={`${styles.checkbox} ${checked ? styles.checkboxOn : ''}`}>
                    {checked && '✓'}
                  </span>
                  <span className={styles.domainIcon}>{d.icon}</span>
                  <span className={styles.domainLabel}>{d.label}</span>
                  <span className={`${styles.domainCount} ${loading ? styles.dimmed : ''} ${avail === 0 && !loading ? styles.domainCountZero : ''}`}>
                    {loading ? '…' : avail}
                  </span>
                </button>

                {/* ── Per-topic difficulty chips (always visible) ── */}
                <div className={styles.bandRow}>
                  {BANDS.map(b => {
                    const cnt     = counts[d.key]?.[b.key] || 0
                    const active  = bands.has(b.key)
                    return (
                      <button
                        key={b.key}
                        className={`${styles.bandChip} ${active ? styles.bandChipActive : ''}`}
                        style={active ? { '--chip-color': b.color } : {}}
                        onClick={() => toggleBand(d.key, b.key)}
                        disabled={!checked}
                      >
                        <span className={styles.bandDot} style={{ background: b.color }} />
                        {b.label}
                        <span className={`${styles.bandCount} ${loading ? styles.dimmed : ''}`}>
                          {loading ? '…' : cnt}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
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
        <button className={styles.startBtn} onClick={handleStart} disabled={!canStart}>
          Start Practice →
        </button>
        {!canStart && totalAvailable === 0 && (
          <p className={styles.noQMsg}>No questions match your filters. Try adjusting difficulty or topics.</p>
        )}
      </div>
    </div>
  )
}
