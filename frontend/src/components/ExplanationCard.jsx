import React from 'react'
import styles from './ExplanationCard.module.css'

export default function ExplanationCard({ explanation }) {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.icon} aria-hidden="true">◎</span>
        <span className={styles.title}>Analysis Summary</span>
      </div>
      <p className={styles.text}>{explanation}</p>
    </div>
  )
}
