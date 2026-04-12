import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getQuestionCounts, createSession } from '../api/client'
import styles from './HomePage.module.css'
import log from '../lib/logger'

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

const BANDS = [
  { key: 'easy',   label: 'Easy',   color: '#16a34a' },
  { key: 'medium', label: 'Medium', color: '#d97706' },
  { key: 'hard',   label: 'Hard',   color: '#dc2626' },
]

function defaultBandCounts(domains) {
  return Object.fromEntries(domains.map(d => [d.key, { easy: 0, medium: 0, hard: 0 }]))
}

export default function PracticeSetupPage() {
  const navigate  = useNavigate()
  const { user }  = useAuth()

  const [section,    setSection]    = useState('math')
  const [bandCounts, setBandCounts] = useState(() => defaultBandCounts(MATH_DOMAINS))
  const [counts,     setCounts]     = useState({})
  const [loading,    setLoading]    = useState(false)
  const [starting,   setStarting]   = useState(false)
  const [authPrompt, setAuthPrompt] = useState(false)

  const fetchCounts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await getQuestionCounts(section || null)
      setCounts(data.byDomain || {})
    } catch { setCounts({}) }
    finally { setLoading(false) }
  }, [section])

  useEffect(() => { fetchCounts() }, [fetchCounts])

  function handleSectionChange(val) {
    log.debug('section changed', { section: val })
    setSection(val)
    setBandCounts(defaultBandCounts(getDomainsForSection(val)))
  }

  function adjust(domain, band, delta) {
    setBandCounts(prev => {
      const current = prev[domain]?.[band] ?? 0
      const avail   = counts[domain]?.[band] ?? 0
      const next    = Math.max(0, Math.min(avail, current + delta))
      return { ...prev, [domain]: { ...prev[domain], [band]: next } }
    })
  }

  function domainTotal(domain) {
    const dc = bandCounts[domain]
    if (!dc) return 0
    return (dc.easy || 0) + (dc.medium || 0) + (dc.hard || 0)
  }

  const grandTotal     = Object.keys(bandCounts).reduce((s, d) => s + domainTotal(d), 0)
  const visibleDomains = getDomainsForSection(section)
  const canStart       = grandTotal > 0

  async function handleStart() {
    // Soft auth gate: require login to start
    if (!user) {
      log.warn('start blocked — not logged in')
      setAuthPrompt(true)
      return
    }

    const domainBandCounts = {}
    for (const [domain, bands] of Object.entries(bandCounts)) {
      const filtered = Object.fromEntries(Object.entries(bands).filter(([, v]) => v > 0))
      if (Object.keys(filtered).length > 0) domainBandCounts[domain] = filtered
    }

    log.info('starting session', { section, grandTotal, domainBandCounts })
    setStarting(true)
    try {
      const session = await createSession('practice', section || null, domainBandCounts)
      log.info('session created', { sessionId: session.id })
      navigate(`/session/${session.id}`)
    } catch (e) {
      log.error('session create failed', { error: e.message })
      alert(`Failed to start session: ${e.message}`)
      setStarting(false)
    }
  }

  return (
    <div className={styles.page}>

      {/* ── Top header ──────────────────────────────────────────── */}
      <div className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.headerLeft}>
            <span className={styles.badge}>Aptify Practice</span>
            <h1 className={styles.title}>Build Your Session</h1>
          </div>

          {/* Section switcher in header */}
          <div className={styles.segmented}>
            {[
              { value: 'math',            label: '📐 Math' },
              { value: 'reading_writing', label: '📖 Reading & Writing' },
              { value: null,              label: '📚 Both' },
            ].map(s => (
              <button
                key={String(s.value)}
                className={`${styles.seg} ${section === s.value ? styles.segActive : ''}`}
                onClick={() => handleSectionChange(s.value)}
              >{s.label}</button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Topic grid ──────────────────────────────────────────── */}
      <div className={styles.topicGrid}>
        {visibleDomains.map(d => {
          const dTotal = domainTotal(d.key)
          return (
            <div key={d.key} className={`${styles.topicCard} ${dTotal > 0 ? styles.topicCardActive : ''}`}>

              {/* Card header */}
              <div className={styles.topicHeader}>
                <span className={styles.topicIcon}>{d.icon}</span>
                <span className={styles.topicLabel}>{d.label}</span>
                {dTotal > 0 && <span className={styles.topicTotal}>{dTotal}</span>}
              </div>

              {/* Band rows */}
              <div className={styles.bandRows}>
                {BANDS.map(b => {
                  const avail   = counts[d.key]?.[b.key] ?? 0
                  const current = bandCounts[d.key]?.[b.key] ?? 0
                  const active  = current > 0
                  return (
                    <div key={b.key} className={`${styles.bandRow} ${active ? styles.bandRowActive : ''} ${avail === 0 && !loading ? styles.bandRowEmpty : ''}`}>
                      <div className={styles.bandLabel}>
                        <span className={styles.bandDot} style={{ background: b.color }} />
                        <span className={styles.bandName} style={active ? { color: b.color, fontWeight: 700 } : {}}>
                          {b.label}
                        </span>
                      </div>

                      <div className={styles.stepper}>
                        <button
                          className={styles.stepBtn}
                          onClick={() => adjust(d.key, b.key, -1)}
                          disabled={current === 0}
                        >−</button>
                        <span className={`${styles.stepVal} ${active ? styles.stepValActive : ''}`}>
                          {current}
                        </span>
                        <button
                          className={styles.stepBtn}
                          onClick={() => adjust(d.key, b.key, +1)}
                          disabled={current >= avail}
                        >+</button>
                      </div>

                      <span className={`${styles.availLabel} ${loading ? styles.dimmed : ''} ${avail === 0 && !loading ? styles.availZero : ''}`}>
                        {loading ? '…' : `${avail} avail.`}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Sticky bottom bar ───────────────────────────────────── */}
      <div className={styles.bottomBar}>
        <div className={styles.bottomInner}>
          {authPrompt && (
            <span style={{ fontSize: 13, color: '#d97706', fontWeight: 600 }}>
              Please <a href="/login" style={{ color: '#d97706' }}>sign in</a> to start a session.
            </span>
          )}
          <div className={styles.totalBlock}>
            <span className={styles.totalLabel}>Total questions</span>
            <span className={`${styles.totalVal} ${grandTotal === 0 ? styles.totalZero : ''}`}>
              {grandTotal}
            </span>
          </div>
          <button
            className={styles.resetBtn}
            onClick={() => setBandCounts(defaultBandCounts(visibleDomains))}
          >Reset</button>
          <button className={styles.startBtn} onClick={handleStart} disabled={!canStart || starting}>
            {starting ? 'Starting…' : 'Start Practice →'}
          </button>
        </div>
      </div>

    </div>
  )
}
