import { useState } from 'react'
import styles from './HomePage.module.css'

const SECTIONS = [
  { value: null,              label: 'Both',             icon: '📚', desc: 'Math + Reading & Writing' },
  { value: 'math',            label: 'Math',             icon: '📐', desc: 'Algebra, Geometry, Problem Solving' },
  { value: 'reading_writing', label: 'Reading & Writing', icon: '📖', desc: 'Comprehension, Grammar, Expression' },
]

const MATH_DOMAINS = [
  { key: 'algebra',                  label: 'Algebra',              icon: '𝑥' },
  { key: 'advanced_math',            label: 'Advanced Math',        icon: '∫' },
  { key: 'problem_solving_data',     label: 'Problem Solving & Data', icon: '📊' },
  { key: 'geometry_trigonometry',    label: 'Geometry & Trig',      icon: '△' },
]

const RW_DOMAINS = [
  { key: 'information_ideas',  label: 'Information & Ideas',       icon: '💡' },
  { key: 'craft_structure',    label: 'Craft & Structure',         icon: '🔧' },
  { key: 'expression_ideas',   label: 'Expression of Ideas',       icon: '✏️' },
  { key: 'standard_english',   label: 'Standard English',          icon: '📝' },
]

const TARGET = 10

function getDomainsForSection(section) {
  if (section === 'math') return MATH_DOMAINS
  if (section === 'reading_writing') return RW_DOMAINS
  return [...MATH_DOMAINS, ...RW_DOMAINS]
}

function makeDefaultCounts(domains) {
  const perDomain = Math.floor(TARGET / domains.length)
  const remainder = TARGET % domains.length
  return Object.fromEntries(
    domains.map((d, i) => [d.key, perDomain + (i < remainder ? 1 : 0)])
  )
}

/**
 * Landing page — 2 steps:
 *   1. Pick section
 *   2. Configure domain counts
 * onStart({ section, domainCounts }) — called when student clicks Start
 */
export default function HomePage({ onStart }) {
  const [step, setStep] = useState(1)
  const [section, setSection] = useState(null)  // null | 'math' | 'reading_writing'
  const [counts, setCounts] = useState({})

  function handleSectionSelect(val) {
    setSection(val)
    // Reset counts to default for the new section
    const domains = getDomainsForSection(val)
    setCounts(makeDefaultCounts(domains))
  }

  function handleContinue() {
    setStep(2)
  }

  function handleBack() {
    setStep(1)
  }

  function adjust(domainKey, delta) {
    setCounts(prev => ({
      ...prev,
      [domainKey]: Math.max(0, (prev[domainKey] ?? 0) + delta),
    }))
  }

  const total = Object.values(counts).reduce((s, v) => s + v, 0)

  if (step === 2) {
    const domains = getDomainsForSection(section)
    const sectionLabel = SECTIONS.find(s => s.value === section)?.label ?? 'Both'
    return (
      <div className={styles.page}>
        <div className={styles.hero}>
          <div className={styles.badge}>Build Your Practice Set</div>
          <h1 className={styles.title}>Choose your topics</h1>
          <p className={styles.sub}>
            Set how many questions you want from each topic.
            Aim for <strong>{TARGET}</strong> questions total.
          </p>
        </div>

        <div className={styles.sectionTag}>
          <span className={styles.sectionTagIcon}>
            {SECTIONS.find(s => s.value === section)?.icon}
          </span>
          {sectionLabel}
          <button className={styles.changeBtn} onClick={handleBack}>change</button>
        </div>

        <div className={styles.domainList}>
          {domains.map(d => (
            <div key={d.key} className={styles.domainRow}>
              <span className={styles.domainIcon}>{d.icon}</span>
              <span className={styles.domainLabel}>{d.label}</span>
              <div className={styles.stepper}>
                <button
                  className={styles.stepperBtn}
                  onClick={() => adjust(d.key, -1)}
                  disabled={(counts[d.key] ?? 0) === 0}
                >−</button>
                <span className={styles.stepperVal}>{counts[d.key] ?? 0}</span>
                <button
                  className={styles.stepperBtn}
                  onClick={() => adjust(d.key, +1)}
                >+</button>
              </div>
            </div>
          ))}
        </div>

        <div className={styles.totalRow}>
          <span className={`${styles.totalBadge} ${total === TARGET ? styles.totalOk : total > TARGET ? styles.totalOver : ''}`}>
            {total} / {TARGET} questions
          </span>
        </div>

        <div className={styles.startRow}>
          <button
            className={styles.startBtn}
            onClick={() => onStart({ section, domainCounts: counts })}
            disabled={total === 0}
          >
            Start Practice →
          </button>
        </div>
      </div>
    )
  }

  // Step 1 — Section picker
  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <div className={styles.badge}>SAT Practice</div>
        <h1 className={styles.title}>Ready to practice?</h1>
        <p className={styles.sub}>Choose a section and work through a set of real SAT-style questions.</p>
      </div>

      <div className={styles.cards}>
        {SECTIONS.map(s => (
          <button
            key={String(s.value)}
            className={`${styles.sectionCard} ${section === s.value ? styles.sectionSelected : ''}`}
            onClick={() => handleSectionSelect(s.value)}
          >
            <span className={styles.sectionIcon}>{s.icon}</span>
            <span className={styles.sectionLabel}>{s.label}</span>
            <span className={styles.sectionDesc}>{s.desc}</span>
          </button>
        ))}
      </div>

      <div className={styles.startRow}>
        <button
          className={styles.startBtn}
          onClick={handleContinue}
          disabled={section === undefined}
        >
          Continue →
        </button>
      </div>
    </div>
  )
}
