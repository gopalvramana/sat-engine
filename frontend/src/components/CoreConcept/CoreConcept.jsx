import MathText from '../MathText/MathText'
import styles from './CoreConcept.module.css'

export default function CoreConcept({ coreConceptJson }) {
  let cc = null
  try {
    cc = typeof coreConceptJson === 'string' ? JSON.parse(coreConceptJson) : coreConceptJson
  } catch { return null }
  if (!cc) return null

  return (
    <div className={styles.wrap}>
      <h4 className={styles.heading}>Core Concept</h4>
      <div className={styles.card}>
        {cc.title && <div className={styles.title}>{cc.title}</div>}
        {cc.summary && <MathText text={cc.summary} as="p" className={styles.summary} />}
        {cc.keyFormula && (
          <div className={styles.formula}>
            <MathText text={`\\[${cc.keyFormula}\\]`} as="div" />
          </div>
        )}
      </div>
    </div>
  )
}
