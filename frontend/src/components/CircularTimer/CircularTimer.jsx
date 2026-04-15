import styles from './CircularTimer.module.css'

/**
 * CircularTimer — SVG arc that depletes over `total` seconds.
 * Color shifts: teal → amber → rose as urgency rises.
 *
 * Props:
 *   elapsed  – seconds elapsed
 *   total    – total seconds allowed
 *   size     – px diameter (default 52)
 */
export default function CircularTimer({ elapsed = 0, total = 120, size = 52 }) {
  const R    = (size / 2) - 5
  const circ = 2 * Math.PI * R
  const pct  = Math.min(elapsed / total, 1)
  const dash = circ * (1 - pct)

  // Color: teal → amber → rose
  const color = pct < 0.5 ? '#0d9488'
              : pct < 0.8 ? '#d97706'
              : '#f43f5e'

  const mins = Math.floor(elapsed / 60)
  const secs = elapsed % 60

  return (
    <div className={styles.wrap} style={{ width: size, height: size }}>
      <svg width={size} height={size} className={styles.svg}>
        {/* Track */}
        <circle
          cx={size / 2} cy={size / 2} r={R}
          fill="none" stroke="#1e293b" strokeWidth={3}
        />
        {/* Arc */}
        <circle
          cx={size / 2} cy={size / 2} r={R}
          fill="none"
          stroke={color}
          strokeWidth={3}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={dash}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 1s linear, stroke 0.5s ease' }}
        />
      </svg>
      <div className={styles.label} style={{ color }}>
        {mins > 0 ? `${mins}:${String(secs).padStart(2, '0')}` : `${secs}s`}
      </div>
    </div>
  )
}
