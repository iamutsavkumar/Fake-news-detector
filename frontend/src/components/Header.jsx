import React from 'react'
import styles from './Header.module.css'

export default function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>◈</span>
          <span className={styles.logoText}>TruthLens</span>
        </div>
        <p className={styles.tagline}>
          AI-powered misinformation analysis
        </p>
      </div>

      {/* Decorative scan line */}
      <div className={styles.scanLine} aria-hidden="true" />
    </header>
  )
}
