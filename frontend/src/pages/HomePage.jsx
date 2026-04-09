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

function getDomainsForSection(section) {
  if (section === 'math')            return MATH_DOMAINS
  if (section === 'reading_writing') return RW_DOMAINS
  return [...MATH_DOMAINS, ...RW_DOMAINS]
}

/* ── Difficulty bands ───────────────────────────────────────────── */
const BANDS = [
  { key: 'easy',   label: 'Easy',   color: '#16a34a' },
  { key: 'medium', label: 'Medium', color: '#d97706' },
  { key: 'hard',   label: 'Hard',   color: '#dc2626' },
]

/* ── Build default band counts for a set of domains ────────────── */
function defaultBandCounts(domains) {
  // Start all at 0
  return Object.fromEntries(
    domains.map(d => [d.key, { easy: 0, medium: 0, hard: 0 }])
  )
}

export default function HomePage({ onStart }) {
  const [section,    setSection]    = useState('math')
  const [bandCounts, setBandCounts] = useState(() => defaultBandCounts(MATH_DOMAINS))
  const [counts,     setCounts]     = useState({})   // API: { domain: { easy, medium, hard, total } }
  const [loading,    setLoading]    = useState(false)

  /* Fetch available counts when section changes */
  const fetchCounts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getQuestionCounts(section || null)
      setCounts(data.byDomain || {})
    } catch { setCounts({}) }
    finally { setLoading(false) }
  }, [section])

  useEffect(() => { fetchCounts() }, [fetchCounts])

  /* Reset counts when section changes */
  function handleSectionChange(val) {
    setSection(val)
    setBandCounts(defaultBandCounts(getDomainsForSection(val)))
  }

  /* Adjust a single domain+band count */
  function adjust(domain, band, delta) {
    setBandCounts(prev => {
      const current = prev[domain]?.[band] ?? 0
      const avail   = counts[domain]?.[band] ?? 0
      const next    = Math.max(0, Math.min(avail, current + delta))
      return {
        ...prev,
        [domain]: { ...prev[domain], [band]: next },
      }
    })
  }

  /* Domain total */
  function domainTotal(domain) {
    const dc = bandCounts[domain]
    if (!dc) return 0
    return (dc.easy || 0) + (dc.medium || 0) + (dc.hard || 0)
  }

  /* Grand total across all domains */
  const grandTotal = Object.keys(bandCounts).reduce((s, d) => s + domainTotal(d), 0)

  const visibleDomains = getDomainsForSection(section)
  const canStart = grandTotal > 0

  function handleStart() {
    // Build domainBandCounts — only include domains/bands with count > 0
    const domainBandCounts = {}
    for (const [domain, bands] of Object.entries(bandCounts)) {
      const filtered = Object.fromEntries(
        Object.entries(bands).filter(([, v]) => v > 0)
      )
      if (Object.keys(filtered).length > 0) {
        domainBandCounts[domain] = filtered
      }
    }
    onStart({ section: section || null, domainBandCounts })
  }

  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <div className={styles.badge}>SAT Practice</div>
        <h1 className={styles.title}>Build Your Session</h1>
        <p className={styles.sub}>Set exactly how many questions you want from each topic and difficulty.</p>
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

      {/* ── Topics ──────────────────────────────────────────────── */}
      <div className={styles.card}>
        <div className={styles.cardLabelRow}>
          <span className={styles.cardLabel}>Topics & Difficulty</span>
          <button className={styles.resetBtn} onClick={() => setBandCounts(defaultBandCounts(visibleDomains))}>
            Reset all
          </button>
        </div>

        <div className={styles.domainList}>
          {visibleDomains.map(d => {
            const dTotal = domainTotal(d.key)
            const hasAny = dTotal > 0
            return (
              <div key={d.key} className={`${styles.domainBlock} ${hasAny ? styles.domainBlockActive : ''}`}>
                {/* ── Domain header ── */}
                <div className={styles.domainHeader}>
                  <span className={styles.domainIcon}>{d.icon}</span>
                  <span className={styles.domainLabel}>{d.label}</span>
                  {dTotal > 0 && (
                    <span className={styles.domainTotal}>{dTotal} selected</span>
                  )}
                </div>

                {/* ── Per-band stepper rows ── */}
                <div className={styles.bandRows}>
                  {BANDS.map(b => {
                    const avail   = counts[d.key]?.[b.key] ?? 0
                    const current = bandCounts[d.key]?.[b.key] ?? 0
                    return (
                      <div key={b.key} className={`${styles.bandRow} ${current > 0 ? styles.bandRowActive : ''}`}>
                        <div className={styles.bandLabel}>
                          <span className={styles.bandDot} style={{ background: b.color }} />
                          <span className={styles.bandName} style={{ color: current > 0 ? b.color : undefined }}>
                            {b.label}
                          </span>
                        </div>
                        <div className={styles.stepperWrap}>
                          <button
                            className={styles.stepBtn}
                            onClick={() => adjust(d.key, b.key, -1)}
                            disabled={current === 0}
                          >−</button>
                          <span className={`${styles.stepVal} ${current > 0 ? styles.stepValActive : ''}`}>
                            {current}
                          </span>
                          <button
                            className={styles.stepBtn}
                            onClick={() => adjust(d.key, b.key, +1)}
                            disabled={current >= avail}
                          >+</button>
                        </div>
                        <span className={`${styles.availLabel} ${loading ? styles.dimmed : ''} ${avail === 0 && !loading ? styles.availZero : ''}`}>
                          {loading ? '…' : `${avail} available`}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Total + Start ────────────────────────────────────────── */}
      <div className={styles.startCard}>
        <div className={styles.totalRow}>
          <span className={styles.totalLabel}>Total questions</span>
          <span className={`${styles.totalVal} ${grandTotal === 0 ? styles.totalZero : ''}`}>
            {grandTotal}
          </span>
        </div>
        <button className={styles.startBtn} onClick={handleStart} disabled={!canStart}>
          Start Practice →
        </button>
        {!canStart && (
          <p className={styles.noQMsg}>Add at least 1 question to start.</p>
        )}
      </div>
    </div>
  )
}
