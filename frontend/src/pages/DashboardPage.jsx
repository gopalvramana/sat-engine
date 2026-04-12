import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import styles from './DashboardPage.module.css'

export default function DashboardPage() {
  const { user } = useAuth()

  const firstName = user?.name?.split(' ')[0] || 'Student'

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Welcome back, {firstName}</h1>
          <p className={styles.subtitle}>Ready to practice? Pick up where you left off.</p>
        </div>
      </div>

      {/* Quick stats */}
      <div className={styles.statsRow}>
        <div className={styles.statCard}>
          <span className={styles.statVal}>—</span>
          <span className={styles.statLabel}>Sessions</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>—</span>
          <span className={styles.statLabel}>Questions Practiced</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>—</span>
          <span className={styles.statLabel}>Accuracy</span>
        </div>
        <div className={styles.statCard}>
          <span className={styles.statVal}>—</span>
          <span className={styles.statLabel}>Avg. Time / Question</span>
        </div>
      </div>

      {/* CTA */}
      <div className={styles.ctaCard}>
        <div className={styles.ctaLeft}>
          <div className={styles.ctaIcon}>✏</div>
          <div>
            <div className={styles.ctaTitle}>Practice Exams</div>
            <div className={styles.ctaSub}>
              Choose your topics and difficulty, then start a focused session.
            </div>
          </div>
        </div>
        <Link to="/practice" className={styles.ctaBtn}>Start Practice →</Link>
      </div>

      {/* Recent sessions placeholder */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Recent Sessions</h2>
        <div className={styles.emptyState}>
          No sessions yet. Start your first practice session above.
        </div>
      </div>
    </div>
  )
}
