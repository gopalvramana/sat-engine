import styles from './SessionSummaryPanel.module.css'

/**
 * SessionSummaryPanel — right-side analytics overlay.
 *
 * Props:
 *   domains   – [{ name, correct, total, avgTime }]  accuracy + timing by domain
 *   byDiff    – [{ label, correct, total, avgTime }]  accuracy + timing by difficulty (d1-d7)
 *   timeline  – [{ q, seconds }]                     per-question timing for line chart
 *   tooSlowThreshold  – seconds (default 90)
 *   tooFastThreshold  – seconds (default 15)
 *   onClose   – dismiss handler
 */
export default function SessionSummaryPanel({
  domains = [],
  byDiff  = [],
  timeline = [],
  tooSlowThreshold = 90,
  tooFastThreshold = 15,
  onClose,
}) {
  const maxTime = Math.max(...timeline.map(t => t.seconds), tooSlowThreshold, 1)

  return (
    <div className={styles.panel}>

      {/* Header */}
      <div className={styles.header}>
        <span className={styles.title}>Session Analytics</span>
        {onClose && (
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close">✕</button>
        )}
      </div>

      {/* ── Accuracy + timing by domain ───────────────────── */}
      {domains.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionLabel}>By Domain</div>
          <div className={styles.domainGrid}>
            {domains.map((d, i) => {
              const pct   = d.total > 0 ? Math.round((d.correct / d.total) * 100) : 0
              const fast  = d.avgTime < tooFastThreshold
              const slow  = d.avgTime > tooSlowThreshold
              return (
                <div key={i} className={styles.domainRow}>
                  <div className={styles.domainName}>{d.name}</div>
                  <div className={styles.barTrack}>
                    <div
                      className={styles.barFill}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className={styles.barMeta}>
                    <span className={styles.pctLabel}>{pct}%</span>
                    {fast && <span className={styles.tooFastLabel}>Too fast!</span>}
                    {slow && <span className={styles.tooSlowLabel}>Too slow</span>}
                    <span className={styles.timeLabel}>{fmtTime(d.avgTime)} avg</span>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* ── Accuracy by difficulty ─────────────────────────── */}
      {byDiff.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionLabel}>By Difficulty</div>
          <div className={styles.diffGrid}>
            {byDiff.map((d, i) => {
              const pct  = d.total > 0 ? Math.round((d.correct / d.total) * 100) : 0
              const fast = d.avgTime < tooFastThreshold
              return (
                <div key={i} className={styles.diffRow}>
                  <span className={styles.diffLabel}>{d.label}</span>
                  <div className={styles.barTrack}>
                    <div className={styles.barFill} style={{ width: `${pct}%` }} />
                  </div>
                  <div className={styles.barMeta}>
                    <span className={styles.pctLabel}>{pct}%</span>
                    {fast && <span className={styles.tooFastLabel}>Too fast!</span>}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* ── Timing per question chart ──────────────────────── */}
      {timeline.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionLabel}>Time per Question</div>
          <div className={styles.chart}>
            {/* Dashed "Too slow" reference line */}
            <div
              className={styles.refLine}
              style={{ bottom: `${(tooSlowThreshold / maxTime) * 100}%` }}
            >
              <span className={styles.refLineLabel}>Too slow</span>
            </div>

            <div className={styles.bars}>
              {timeline.map((t, i) => {
                const heightPct = Math.min((t.seconds / maxTime) * 100, 100)
                const slow      = t.seconds > tooSlowThreshold
                const fast      = t.seconds < tooFastThreshold
                return (
                  <div key={i} className={styles.chartBarWrap} title={`Q${t.q}: ${fmtTime(t.seconds)}`}>
                    <div
                      className={`${styles.chartBar} ${slow ? styles.chartBarSlow : fast ? styles.chartBarFast : ''}`}
                      style={{ height: `${heightPct}%` }}
                    />
                    <span className={styles.chartQLabel}>Q{t.q}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </section>
      )}

    </div>
  )
}

function fmtTime(seconds) {
  if (!seconds && seconds !== 0) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}
