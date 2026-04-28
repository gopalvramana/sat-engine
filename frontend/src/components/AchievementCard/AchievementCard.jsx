import styles from './AchievementCard.module.css'

/**
 * Gamification achievement card.
 * variant: 'indigo' | 'amber'
 */
export default function AchievementCard({ icon, count, name, sticker, stickerVariant = 'green', tailIcon, variant = 'indigo' }) {
  return (
    <div className={`${styles.card} ${styles[variant]}`}>
      <div className={`${styles.sticker} ${styles[`sticker_${stickerVariant}`]}`}>
        {sticker}
      </div>
      <div className={`${styles.iconBox} ${styles[`iconBox_${variant}`]}`}>
        {icon}
      </div>
      <div className={styles.body}>
        <div className={styles.meta}>Achievement Unlocked</div>
        <div className={styles.countRow}>
          <span className={styles.count}>{count}</span>
          <span className={styles.name}>{name}</span>
        </div>
      </div>
      {tailIcon && <div className={styles.tail}>{tailIcon}</div>}
    </div>
  )
}
