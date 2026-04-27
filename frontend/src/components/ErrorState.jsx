import React from 'react'
import styles from './ErrorState.module.css'

export default function ErrorState({ message }) {
  return (
    <div className={styles.wrapper} role="alert">
      <span className={styles.icon} aria-hidden="true">⚠</span>
      <div>
        <p className={styles.title}>Analysis Failed</p>
        <p className={styles.message}>{message}</p>
      </div>
    </div>
  )
}
