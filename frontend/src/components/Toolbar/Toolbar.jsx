import { useState } from 'react'
import MathText from '../MathText/MathText'
import styles from './Toolbar.module.css'

/**
 * Toolbar — Calculator + Reference sheet buttons.
 *
 * Props:
 *   phase           — 'question' | 'feedback' | other
 *   calculatorOk    — boolean; false = Calculator button greyed out
 */
export default function Toolbar({ phase, calculatorOk = true }) {
  const [calcOpen, setCalcOpen] = useState(false)
  const [refOpen, setRefOpen] = useState(false)

  if (phase !== 'question' && phase !== 'feedback') return null

  return (
    <>
      {/* ── Toolbar strip ─────────────────────────────────────── */}
      <div className={styles.toolbar}>
        {/* Calculator button */}
        <div className={styles.btnWrap}>
          <button
            className={`${styles.toolBtn} ${!calculatorOk ? styles.toolBtnDisabled : ''}`}
            onClick={() => calculatorOk && setCalcOpen(true)}
            disabled={!calculatorOk}
            title={calculatorOk ? 'Open Calculator' : 'Calculator not allowed'}
            aria-label="Calculator"
          >
            <span className={styles.toolIcon} aria-hidden="true">🖩</span>
            <span className={styles.toolLabel}>Calculator</span>
          </button>
          {!calculatorOk && (
            <span className={styles.tooltip}>Calculator not allowed</span>
          )}
        </div>

        {/* Reference button */}
        <button
          className={styles.toolBtn}
          onClick={() => setRefOpen(true)}
          title="Open Reference Sheet"
          aria-label="Reference Sheet"
        >
          <span className={styles.toolIcon} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <text x="0" y="13" fontSize="13" fontFamily="serif" fontStyle="italic" fill="currentColor">x²</text>
            </svg>
          </span>
          <span className={styles.toolLabel}>Reference</span>
        </button>
      </div>

      {/* ── Calculator Overlay ────────────────────────────────── */}
      {calcOpen && (
        <div className={styles.overlay} onClick={() => setCalcOpen(false)}>
          <div className={styles.calcContainer} onClick={e => e.stopPropagation()}>
            <button
              className={styles.closeBtn}
              onClick={() => setCalcOpen(false)}
              aria-label="Close calculator"
            >
              ×
            </button>
            <iframe
              src="https://www.desmos.com/scientific"
              title="Desmos Scientific Calculator"
              className={styles.calcFrame}
              allow="fullscreen"
            />
          </div>
        </div>
      )}

      {/* ── Reference Modal ───────────────────────────────────── */}
      {refOpen && (
        <div className={styles.overlay} onClick={() => setRefOpen(false)}>
          <div className={styles.refModal} onClick={e => e.stopPropagation()}>
            <div className={styles.refHeader}>
              <h2 className={styles.refTitle}>SAT Math Reference</h2>
              <button
                className={styles.closeBtn}
                onClick={() => setRefOpen(false)}
                aria-label="Close reference sheet"
              >
                ×
              </button>
            </div>
            <div className={styles.refBody}>
              <ReferenceSheet />
            </div>
          </div>
        </div>
      )}
    </>
  )
}

/* ── Reference sheet content ──────────────────────────────────── */
function ReferenceSheet() {
  return (
    <div className={styles.refContent}>

      <section className={styles.refSection}>
        <h3 className={styles.refSectionTitle}>Area &amp; Circumference</h3>
        <div className={styles.formulaList}>
          <FormulaRow label="Circle">
            <MathText text="\(A = \pi r^2\)" />{' '}
            &nbsp;&nbsp;
            <MathText text="\(C = 2\pi r\)" />
          </FormulaRow>
          <FormulaRow label="Rectangle">
            <MathText text="\(A = lw\)" />
          </FormulaRow>
          <FormulaRow label="Triangle">
            <MathText text="\(A = \dfrac{1}{2}bh\)" />
          </FormulaRow>
        </div>
      </section>

      <section className={styles.refSection}>
        <h3 className={styles.refSectionTitle}>Volume</h3>
        <div className={styles.formulaList}>
          <FormulaRow label="Rectangular solid">
            <MathText text="\(V = lwh\)" />
          </FormulaRow>
          <FormulaRow label="Cylinder">
            <MathText text="\(V = \pi r^2 h\)" />
          </FormulaRow>
          <FormulaRow label="Sphere">
            <MathText text="\(V = \dfrac{4}{3}\pi r^3\)" />
          </FormulaRow>
          <FormulaRow label="Cone">
            <MathText text="\(V = \dfrac{1}{3}\pi r^2 h\)" />
          </FormulaRow>
          <FormulaRow label="Pyramid">
            <MathText text="\(V = \dfrac{1}{3}lwh\)" />
          </FormulaRow>
        </div>
      </section>

      <section className={styles.refSection}>
        <h3 className={styles.refSectionTitle}>Pythagorean Theorem</h3>
        <div className={styles.formulaList}>
          <FormulaRow label="">
            <MathText text="\(a^2 + b^2 = c^2\)" />
          </FormulaRow>
        </div>
      </section>

      <section className={styles.refSection}>
        <h3 className={styles.refSectionTitle}>Special Right Triangles</h3>
        <div className={styles.formulaList}>
          <FormulaRow label="30-60-90">
            <MathText text="sides in ratio \(1 : \sqrt{3} : 2\)" />
          </FormulaRow>
          <FormulaRow label="45-45-90">
            <MathText text="sides in ratio \(1 : 1 : \sqrt{2}\)" />
          </FormulaRow>
        </div>
      </section>

      <section className={styles.refSection}>
        <h3 className={styles.refSectionTitle}>Other Facts</h3>
        <ul className={styles.factList}>
          <li>A circle has <strong>360°</strong></li>
          <li>A circle has <MathText text="\(2\pi\)" /> radians</li>
          <li>The sum of angles in a triangle is <strong>180°</strong></li>
        </ul>
      </section>
    </div>
  )
}

function FormulaRow({ label, children }) {
  return (
    <div className={styles.formulaRow}>
      {label && <span className={styles.formulaLabel}>{label}</span>}
      <span className={styles.formulaValue}>{children}</span>
    </div>
  )
}
