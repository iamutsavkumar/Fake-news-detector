import React from 'react'
import styles from './VerdictCard.module.css'

export default function VerdictCard({ label, confidence }) {
  const isFake = label === 'FAKE'

  // ✅ FIX: do NOT multiply again
  const pct = Math.round(confidence)

  return (
    <div className={`${styles.card} ${isFake ? styles.fake : styles.real}`}>
      <div className={styles.icon} aria-hidden="true">
        {isFake ? '✗' : '✓'}
      </div>
      <div className={styles.label}>{label}</div>
      <div className={styles.pct}>{pct}%</div>
    </div>
  )
}