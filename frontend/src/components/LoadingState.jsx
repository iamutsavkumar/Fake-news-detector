import React from 'react'
import styles from './LoadingState.module.css'

const STEPS = [
  'Tokenising text…',
  'Extracting features…',
  'Running classifier…',
  'Scoring sentences…',
  'Building explanation…',
]

export default function LoadingState() {
  const [step, setStep] = React.useState(0)

  React.useEffect(() => {
    const id = setInterval(() => {
      setStep(s => (s + 1) % STEPS.length)
    }, 900)
    return () => clearInterval(id)
  }, [])

  return (
    <div className={styles.wrapper} role="status" aria-label="Analysing…">
      <div className={styles.scanBox} aria-hidden="true">
        <div className={styles.scanLine} />
        <div className={styles.grid}>
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} className={styles.cell} style={{ animationDelay: `${i * 0.06}s` }} />
          ))}
        </div>
      </div>
      <p className={styles.step}>{STEPS[step]}</p>
      <p className={styles.hint}>This usually takes 1–3 seconds</p>
    </div>
  )
}
