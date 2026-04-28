import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import styles from './AnalyticsPage.module.css'

/* ── Constants ─────────────────────────────────────────────────── */
const DOMAIN_META = {
  // Math
  algebra:               { label: 'Algebra',                  section: 'math',            color: '#111', bg: '#f0f0f0' },
  advanced_math:         { label: 'Advanced Math',            section: 'math',            color: '#111', bg: '#e8e8e8' },
  problem_solving_data:  { label: 'Problem Solving & Data',   section: 'math',            color: '#111', bg: '#f0f0f0' },
  geometry_trigonometry: { label: 'Geometry & Trig',          section: 'math',            color: '#111', bg: '#e8e8e8' },
  // Reading & Writing
  information_ideas:     { label: 'Information & Ideas',      section: 'reading_writing', color: '#111', bg: '#f0f0f0' },
  craft_structure:       { label: 'Craft & Structure',        section: 'reading_writing', color: '#111', bg: '#e8e8e8' },
  expression_ideas:      { label: 'Expression of Ideas',      section: 'reading_writing', color: '#111', bg: '#f0f0f0' },
  standard_english:      { label: 'Standard English',         section: 'reading_writing', color: '#111', bg: '#e8e8e8' },
}

const MATH_ORDER = ['algebra', 'advanced_math', 'problem_solving_data', 'geometry_trigonometry']
const RW_ORDER   = ['information_ideas', 'craft_structure', 'expression_ideas', 'standard_english']

function timeStr(s) {
  if (s == null) return '—'
  if (s < 60) return `${s}s`
  return `${Math.floor(s / 60)}m ${s % 60}s`
}

function diffLabel(pct) {
  if (pct == null) return '—'
  if (pct < 34) return 'Easy'
  if (pct < 67) return 'Medium'
  return 'Hard'
}

/* ── Bar chart helpers ──────────────────────────────────────────── */
const BAR_H   = 120   // fixed pixel height of bar area
const DAYS    = 30    // always show 30 days

function niceMax(val) {
  if (val <= 5)  return 5
  if (val <= 10) return 10
  const mag = Math.pow(10, Math.floor(Math.log10(val)))
  return Math.ceil(val / mag) * mag
}

/** Build a full 30-day series, filling missing days with 0 */
function buildSeries(apiData) {
  const map = {}
  ;(apiData ?? []).forEach(d => { map[d.date] = d.questions })
  const result = []
  for (let i = DAYS - 1; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    result.push({ date: key, questions: map[key] ?? 0 })
  }
  return result
}

function BarChart({ data }) {
  const series  = buildSeries(data)
  const maxQ    = Math.max(...series.map(d => d.questions), 1)
  const yMax    = niceMax(maxQ)
  const yTicks  = [yMax, Math.round(yMax * 0.5), 0]
  // Label every 7th day (weekly tick)
  const step    = 7

  return (
    <div className={styles.chartWrap}>
      <div className={styles.chartInner}>

        {/* Y-axis */}
        <div className={styles.yAxis} style={{ height: BAR_H }}>
          {yTicks.map(t => (
            <span key={t} className={styles.yTick}>{t}</span>
          ))}
        </div>

        {/* Bars + x-labels */}
        <div className={styles.chartBody}>
          <div className={styles.bars} style={{ height: BAR_H }}>
            {series.map((d) => {
              const px = d.questions > 0
                ? Math.max(3, Math.round(d.questions / yMax * BAR_H))
                : 0
              return (
                <div key={d.date} className={styles.barCol}>
                  {px > 0 && (
                    <div
                      className={styles.bar}
                      style={{ height: px }}
                      title={`${d.questions} on ${d.date}`}
                    />
                  )}
                </div>
              )
            })}
          </div>

          {/* X-axis — label every 7 days */}
          <div className={styles.xAxis}>
            {series.map((d, i) => (
              <div key={d.date} className={styles.xTick}>
                {i % step === 0 ? d.date.slice(5).replace('-', '/') : ''}
              </div>
            ))}
          </div>
        </div>
      </div>
      <p className={styles.chartCaption}>Number of answered questions.</p>
    </div>
  )
}

/* ── Domain row ─────────────────────────────────────────────────── */
function DomainRow({ domain, stat }) {
  const meta = DOMAIN_META[domain] ?? { label: domain, color: '#6366f1', bg: '#eef2ff' }
  const tooFast = stat && stat.avgTimeSeconds != null && stat.avgTimeSeconds < 30

  if (!stat) {
    return (
      <div className={styles.domainRow}>
        <div className={styles.domainPill} style={{ background: meta.bg, color: meta.color }}>
          {meta.label}
        </div>
        <span className={styles.noData}>No data yet</span>
        <Link to="/practice" state={{ prefillDomain: domain }} className={styles.noDataLink}>↗</Link>
      </div>
    )
  }

  return (
    <div className={styles.domainRow}>
      {/* Domain pill */}
      <div className={styles.domainPill} style={{ background: meta.bg, color: meta.color }}>
        {meta.label}
      </div>

      {/* Stats line */}
      <div className={styles.domainStats}>
        <span className={styles.statChip}>Questions: <strong>{stat.total}</strong></span>
        <span className={styles.statSep}>·</span>
        <span className={styles.statChip}>
          Avg time: <strong>{timeStr(stat.avgTimeSeconds)}</strong>
          {tooFast && <span className={styles.tooFast}>Too fast!</span>}
        </span>
      </div>

      {/* Mini progress blocks */}
      <div className={styles.miniBlocks}>
        {Array.from({ length: Math.min(stat.total, 10) }).map((_, i) => {
          const isCorrect = i < Math.round(stat.total * stat.accuracyPct / 100)
          return (
            <span
              key={i}
              className={styles.miniBlock}
              style={{ background: isCorrect ? meta.color : '#e2e8f0' }}
            />
          )
        })}
      </div>

      {/* Mastery */}
      <div className={styles.masteryRow}>
        <div className={styles.masteryTrack}>
          <div
            className={styles.masteryFill}
            style={{ width: `${stat.accuracyPct}%`, background: meta.color }}
          />
        </div>
        <span className={styles.masteryPct} style={{ color: meta.color }}>
          Mastery: {stat.accuracyPct}%
        </span>
        <Link to="/practice" state={{ prefillDomain: domain }} className={styles.drillLink}>↗</Link>
      </div>
    </div>
  )
}

/* ── Section panel ─────────────────────────────────────────────── */
function SectionPanel({ title, domainOrder, statMap }) {
  return (
    <div className={styles.sectionPanel}>
      <h2 className={styles.sectionTitle}>{title}</h2>
      <div className={styles.domainList}>
        {domainOrder.map(domain => (
          <DomainRow key={domain} domain={domain} stat={statMap[domain] ?? null} />
        ))}
      </div>
    </div>
  )
}

/* ── Page ─────────────────────────────────────────────────────── */
export default function AnalyticsPage() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/analytics')
      .then(r => r.ok ? r.json() : null)
      .then(json => { setData(json); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  // Build domain → stat map
  const statMap = {}
  if (data?.domains) {
    data.domains.forEach(d => { statMap[d.domain] = d })
  }

  return (
    <div className={styles.page}>
      {/* ── Header ── */}
      <div className={styles.header}>
        <h1 className={styles.title}>Analytics</h1>
        <p className={styles.sub}>The only curves you should be worried about.</p>
      </div>

      {/* ── 3 stat cards ── */}
      <div className={styles.statsRow}>
        {[
          { label: 'Questions',  value: loading ? '…' : (data?.totalQuestions ?? 0) },
          { label: 'Accuracy',   value: loading ? '…' : data?.accuracyPct   != null ? `${data.accuracyPct}%`   : '—' },
          { label: 'Difficulty', value: loading ? '…' : data?.difficultyPct != null ? `${data.difficultyPct}%` : '—',
            sub: loading ? null : data?.difficultyPct != null ? diffLabel(data.difficultyPct) : null },
        ].map(c => (
          <div key={c.label} className={styles.statCard}>
            <div className={styles.statLabel}>{c.label}</div>
            <div className={styles.statVal}>{c.value}</div>
            {c.sub && <div className={styles.statSub}>{c.sub}</div>}
          </div>
        ))}
      </div>

      {/* ── Bar chart ── */}
      <div className={styles.chartCard}>
        {loading
          ? <div className={styles.skeleton} />
          : <BarChart data={data?.dailyActivity} />
        }
      </div>

      {/* ── Domain breakdown ── */}
      <div className={styles.domainGrid}>
        {loading ? (
          <>
            <div className={styles.sectionSkeleton} />
            <div className={styles.sectionSkeleton} />
          </>
        ) : (
          <>
            <SectionPanel title="Reading & Writing" domainOrder={RW_ORDER}   statMap={statMap} />
            <SectionPanel title="Math"              domainOrder={MATH_ORDER} statMap={statMap} />
          </>
        )}
      </div>
    </div>
  )
}
