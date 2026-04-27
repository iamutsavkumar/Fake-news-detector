import React from 'react'
import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p className={styles.text}>
        TruthLens uses ML + rule-based analysis · Not a substitute for professional fact-checking
      </p>
    </footer>
  )
}
