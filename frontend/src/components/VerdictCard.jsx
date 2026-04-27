import React from 'react'
import styles from './VerdictCard.module.css'

export default function VerdictCard({ label, confidence }) {
  // ✅ confidence already in percent (no multiply)
  const pct = Math.round(confidence)

  let typeClass = styles.real
  let icon = '✓'

  if (label === 'FAKE') {
    typeClass = styles.fake
    icon = '✗'
  } else if (label === 'UNCERTAIN') {
    typeClass = styles.uncertain
    icon = '⚠'
  }

  return (
    <div className={`${styles.card} ${typeClass}`}>
      <div className={styles.icon} aria-hidden="true">
        {icon}
      </div>
      <div className={styles.label}>{label}</div>
      <div className={styles.pct}>{pct}%</div>
    </div>
  )
}