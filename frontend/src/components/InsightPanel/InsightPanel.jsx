import styles from './InsightPanel.module.css'

const CONFIDENCE_OPTIONS = [
  { id: 'guessing',  emoji: '🎲', label: 'Guessing' },
  { id: 'unsure',    emoji: '🤔', label: 'Unsure'   },
  { id: 'confident', emoji: '💡', label: 'Confident' },
]

/**
 * InsightPanel — metacognitive feedback sidebar shown after answering.
 *
 * Props:
 *   isCorrect            – boolean
 *   confidence           – effective confidence (explicit tap OR timing proxy)
 *   explicitConfidence   – null if student hasn't tapped yet (shows proxy label)
 *   onConfidenceChange   – (value) => void — post-answer optional tap
 *   timeTaken            – seconds student took
 *   avgTime              – student's rolling average
 *   domain               – e.g. 'Algebra'
 *   domainAccuracy       – 0-100
 *   difficulty           – 1-7
 *   targetScore          – e.g. 1350
 *   streakCorrect        – consecutive correct
 *   onNext               – handler
 *   isLastQuestion       – boolean
 */
export default function InsightPanel({
  isCorrect, confidence, explicitConfidence, onConfidenceChange,
  timeTaken, avgTime, domain, domainAccuracy, difficulty,
  targetScore = 1400, streakCorrect = 0,
  onNext, isLastQuestion,
}) {
  const timeDiff      = avgTime - timeTaken
  const fasterThanAvg = timeDiff > 5
  const slowerThanAvg = timeDiff < -5

  const overconfident  = confidence === 'confident' && !isCorrect
  const underconfident = confidence === 'guessing'  && isCorrect
  const domainLabel    = domainAccuracy >= 75 ? 'strong suit 💪'
                       : domainAccuracy >= 50 ? 'developing'
                       : 'needs focus 🎯'
  const onTrack = difficulty >= 4 && isCorrect

  return (
    <div className={`${styles.panel} ${isCorrect ? styles.panelCorrect : styles.panelWrong}`}>

      {/* ── Result badge ───────────────────────────────── */}
      <div className={`${styles.result} ${isCorrect ? styles.resultCorrect : styles.resultWrong}`}>
        <span className={styles.resultIcon}>{isCorrect ? '✓' : '✗'}</span>
        <span className={styles.resultText}>{isCorrect ? 'Correct!' : 'Not quite'}</span>
      </div>

      {/* ── Post-answer confidence tap ─────────────────── */}
      <div className={styles.confidenceWrap}>
        <div className={styles.confidenceHeader}>
          <span className={styles.confidenceLabel}>Were you sure?</span>
          {/* Show timing proxy hint when no explicit tap yet */}
          {!explicitConfidence && (
            <span className={styles.proxyHint}>
              ⏱ {timeTaken}s · looks like{' '}
              <em>{confidence === 'confident' ? 'confident' : confidence === 'unsure' ? 'unsure' : 'guessing'}</em>
            </span>
          )}
        </div>
        <div className={styles.confidenceOptions}>
          {CONFIDENCE_OPTIONS.map(o => (
            <button
              key={o.id}
              className={`${styles.confBtn} ${confidence === o.id ? styles.confBtnActive : ''}`}
              onClick={() => onConfidenceChange(o.id)}
              type="button"
            >
              <span>{o.emoji}</span>
              <span className={styles.confBtnLabel}>{o.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* ── Metacognitive callout ──────────────────────── */}
      {overconfident && (
        <div className={styles.metaAlert}>
          <span className={styles.metaIcon}>⚠️</span>
          <div>
            <div className={styles.metaTitle}>Confidence mismatch</div>
            <div className={styles.metaDesc}>Confident but wrong — prime candidate for deep review.</div>
          </div>
        </div>
      )}
      {underconfident && (
        <div className={styles.metaAlert} style={{ '--meta-color': '#0d9488' }}>
          <span className={styles.metaIcon}>🎯</span>
          <div>
            <div className={styles.metaTitle}>Hidden strength</div>
            <div className={styles.metaDesc}>You guessed but nailed it — you know more than you think!</div>
          </div>
        </div>
      )}

      {/* ── Insight chips ──────────────────────────────── */}
      <div className={styles.chips}>

        <div className={styles.chip}>
          <span className={styles.chipIcon}>⏱</span>
          <div className={styles.chipContent}>
            <span className={styles.chipLabel}>Time</span>
            <span className={`${styles.chipValue} ${fasterThanAvg ? styles.good : slowerThanAvg ? styles.warn : ''}`}>
              {fmtTime(timeTaken)}
              {fasterThanAvg && <span className={styles.chipTag}>⚡ {fmtTime(timeDiff)} faster</span>}
              {slowerThanAvg && <span className={styles.chipTag} style={{color:'#d97706'}}>🐌 {fmtTime(-timeDiff)} slower</span>}
              {!fasterThanAvg && !slowerThanAvg && <span className={styles.chipTag} style={{color:'#64748b'}}>on pace</span>}
            </span>
          </div>
        </div>

        <div className={styles.chip}>
          <span className={styles.chipIcon}>📊</span>
          <div className={styles.chipContent}>
            <span className={styles.chipLabel}>{domain}</span>
            <span className={styles.chipValue}>{domainAccuracy}% · {domainLabel}</span>
          </div>
          <div className={styles.miniBar}>
            <div
              className={`${styles.miniFill} ${domainAccuracy>=75?styles.fillGood:domainAccuracy>=50?styles.fillMid:styles.fillWeak}`}
              style={{ width:`${domainAccuracy}%` }}
            />
          </div>
        </div>

        <div className={styles.chip}>
          <span className={styles.chipIcon}>📈</span>
          <div className={styles.chipContent}>
            <span className={styles.chipLabel}>Target {targetScore}</span>
            <span className={`${styles.chipValue} ${onTrack ? styles.good : ''}`}>
              {onTrack ? `d${difficulty} correct · on track` : `keep going at d${difficulty}`}
            </span>
          </div>
        </div>

        {streakCorrect >= 3 && (
          <div className={`${styles.chip} ${styles.chipStreak}`}>
            <span className={styles.chipIcon}>🔥</span>
            <div className={styles.chipContent}>
              <span className={styles.chipLabel}>Momentum</span>
              <span className={styles.chipValue}>{streakCorrect} in a row · great focus</span>
            </div>
          </div>
        )}
      </div>

      {/* ── Next button ────────────────────────────────── */}
      <button
        className={`${styles.nextBtn} ${isCorrect ? styles.nextBtnCorrect : styles.nextBtnWrong}`}
        onClick={onNext}
      >
        {isLastQuestion ? 'See Results →' : 'Next Question →'}
      </button>
      <div className={styles.keyHint}>Press Enter ↵</div>

    </div>
  )
}

function fmtTime(s) {
  if (s < 60) return `${s}s`
  return `${Math.floor(s/60)}m ${s%60}s`
}
