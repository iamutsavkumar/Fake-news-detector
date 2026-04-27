import React, { useEffect, useRef } from 'react'
import styles from './ConfidenceBar.module.css'

export default function ConfidenceBar({ confidence, label }) {
  const barRef = useRef(null)
  const isFake = label === 'FAKE'

  // ✅ FIX: use confidence directly (already %)
  const pct = Math.round(confidence)

  // Animate the bar width
  useEffect(() => {
    if (!barRef.current) return
    const bar = barRef.current
    bar.style.width = '0%'
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        bar.style.width = `${pct}%`
      })
    })
  }, [pct])

  // Color logic
  const getColor = () => {
    if (isFake) {
      if (pct >= 80) return 'var(--fake)'
      if (pct >= 60) return 'var(--warn)'
      return 'var(--warn)'
    }
    if (pct >= 80) return 'var(--real)'
    if (pct >= 60) return 'var(--real)'
    return 'var(--warn)'
  }

  // ✅ FIXED label logic (more realistic)
  const confidenceLabel =
    pct >= 80 ? 'High' :
    pct >= 60 ? 'Medium' :
    pct >= 40 ? 'Low' : 'Very Low'

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <span className={styles.title}>Confidence</span>
        <span className={styles.meta}>
          <span className={styles.label} style={{ color: getColor() }}>
            {confidenceLabel}
          </span>
          <span className={styles.pct}>{pct}%</span>
        </span>
      </div>

      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          ref={barRef}
          className={styles.fill}
          style={{ backgroundColor: getColor() }}
        />
      </div>
    </div>
  )
}