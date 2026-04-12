import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './SessionHistoryPage.module.css'

export default function SessionHistoryPage() {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    fetch('/api/sessions')
      .then(r => r.ok ? r.json() : [])
      .then(data => { setSessions(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Session History</h1>
        <p className={styles.subtitle}>Review all your past practice sessions.</p>
      </div>

      {loading ? (
        <div className={styles.emptyState}>Loading…</div>
      ) : sessions.length === 0 ? (
        <div className={styles.emptyState}>No sessions yet.</div>
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>Date</th>
                <th className={styles.th}>Section</th>
                <th className={styles.th}>Questions</th>
                <th className={styles.th}>Accuracy</th>
                <th className={styles.th}>Status</th>
                <th className={styles.th}></th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => {
                const acc = s.questionsAnswered > 0
                  ? Math.round((s.correctCount / s.questionsAnswered) * 100)
                  : null
                const accClass = acc == null ? '' : acc >= 70 ? styles.good : acc >= 50 ? styles.mid : styles.bad
                return (
                  <tr key={s.id} className={styles.tr}>
                    <td className={styles.td}>
                      {s.startedAt
                        ? new Date(s.startedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                        : '—'}
                    </td>
                    <td className={styles.td}>
                      <span className={styles.section}>
                        {s.section ? s.section.replace('_', ' & ') : 'Mixed'}
                      </span>
                    </td>
                    <td className={styles.td}>{s.questionsAnswered}</td>
                    <td className={`${styles.td} ${accClass}`}>
                      {acc != null ? `${acc}%` : '—'}
                    </td>
                    <td className={styles.td}>
                      <span className={`${styles.statusBadge} ${s.status === 'completed' ? styles.statusDone : styles.statusActive}`}>
                        {s.status}
                      </span>
                    </td>
                    <td className={styles.td}>
                      <Link to={`/session/${s.id}/summary`} className={styles.reviewLink}>
                        Review →
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
