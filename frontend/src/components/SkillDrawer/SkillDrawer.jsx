import { useState, useEffect, useCallback } from 'react'
import MathText from '../MathText/MathText'
import { getSkillContent } from '../../api/client'
import styles from './SkillDrawer.module.css'

/* ── Main export ─────────────────────────────────────────────────── */
export default function SkillDrawer({ skillKey, onClose }) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    setData(null)
    getSkillContent(skillKey)
      .then(setData)
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [skillKey])

  // Close on Escape
  const handleKey = useCallback(
    (e) => { if (e.key === 'Escape') onClose() },
    [onClose]
  )
  useEffect(() => {
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [handleKey])

  // Prevent body scroll while open
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  function handleBackdrop(e) {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div className={styles.backdrop} onClick={handleBackdrop} role="dialog" aria-modal="true">
      <div className={styles.panel}>
        {/* Header is always visible */}
        <div className={styles.header}>
          <div className={styles.headerLeft}>
            <span className={styles.headerIcon}>📚</span>
            <div>
              <div className={styles.headerSuper}>Skill Study</div>
              <div className={styles.headerTitle}>
                {data?.label ?? skillKey.replace(/_/g, ' ')}
              </div>
            </div>
          </div>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className={styles.body}>
          {loading && (
            <div className={styles.center}>
              <div className={styles.spinner} />
              <span className={styles.loadingText}>Loading…</span>
            </div>
          )}

          {error && !loading && (
            <div className={styles.center}>
              <p className={styles.errorText}>Content not available for this skill yet.</p>
            </div>
          )}

          {data && !loading && <DrawerContent data={data} />}
        </div>
      </div>
    </div>
  )
}

/* ── Drawer content ─────────────────────────────────────────────── */
function DrawerContent({ data }) {
  const firstExample = data.workedExamples?.[0] ?? null

  return (
    <div className={styles.content}>

      {/* ── Section 1: Concept ─────────────────────────────── */}
      <Section label="Concept" icon="💡">
        {data.overview && (
          <p className={styles.overview}>{data.overview}</p>
        )}
        {data.conceptDiagram?.svg && (
          <figure className={styles.diagramWrap}>
            <div
              className={styles.diagramSvg}
              dangerouslySetInnerHTML={{ __html: data.conceptDiagram.svg }}
            />
            {data.conceptDiagram.caption && (
              <figcaption className={styles.diagramCaption}>
                {data.conceptDiagram.caption}
              </figcaption>
            )}
          </figure>
        )}
      </Section>

      {/* ── Section 2: Key Formulas ─────────────────────────── */}
      {data.keyFormulas?.length > 0 && (
        <Section label="Key Formulas" icon="📐">
          <div className={styles.formulaGrid}>
            {data.keyFormulas.map((f, i) => (
              <div key={i} className={styles.formulaCard}>
                <div className={styles.formulaName}>{f.name}</div>
                <div className={styles.formulaMath}>
                  <MathText text={`\\[${f.latex}\\]`} as="div" />
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Section 3: Quick Example ────────────────────────── */}
      {firstExample && (
        <Section label="Quick Example" icon="✏️">
          <p className={styles.exampleProblem}>{firstExample.problem}</p>
          <div className={styles.exampleSteps}>
            {firstExample.steps.map((s, i) => (
              <div key={i} className={styles.exampleStep}>
                <div className={styles.exampleStepNum}>{i + 1}</div>
                <div className={styles.exampleStepBody}>
                  <div className={styles.exampleStepTitle}>
                    <MathText text={s.title} />
                  </div>
                  {s.content && (
                    <MathText text={s.content} as="p" className={styles.exampleStepContent} />
                  )}
                  {s.math && (
                    <div className={styles.exampleStepMath}>
                      <MathText text={`\\[${s.math}\\]`} as="div" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Common Mistakes ─────────────────────────────────── */}
      {data.commonMistakes?.length > 0 && (
        <Section label="Common Mistakes" icon="⚠️">
          <div className={styles.mistakeList}>
            {data.commonMistakes.map((m, i) => (
              <div key={i} className={styles.mistakeRow}>
                <div className={styles.mistakeLabel}>✗ {m.mistake}</div>
                <div className={styles.mistakeFix}>→ {m.fix}</div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── Quick Tip ───────────────────────────────────────── */}
      {data.quickTip && (
        <div className={styles.quickTip}>
          <span className={styles.quickTipIcon}>💬</span>
          <p className={styles.quickTipText}>{data.quickTip}</p>
        </div>
      )}

    </div>
  )
}

/* ── Reusable section block ─────────────────────────────────────── */
function Section({ label, icon, children }) {
  return (
    <div className={styles.section}>
      <div className={styles.sectionHeader}>
        <span className={styles.sectionIcon}>{icon}</span>
        <span className={styles.sectionLabel}>{label}</span>
      </div>
      <div className={styles.sectionBody}>{children}</div>
    </div>
  )
}
