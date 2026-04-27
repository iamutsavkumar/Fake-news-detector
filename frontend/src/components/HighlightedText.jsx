import React, { useState } from 'react'
import styles from './HighlightedText.module.css'

/**
 * Renders the article text sentence-by-sentence.
 * Each sentence is colour-coded by suspicion score and
 * shows a tooltip with triggered flag labels on hover.
 */
export default function HighlightedText({ sentences }) {
  const [activeIdx, setActiveIdx] = useState(null)

  const highCount = sentences.filter(s => s.score >= 0.6).length
  const midCount  = sentences.filter(s => s.score >= 0.35 && s.score < 0.6).length

  return (
    <div className={styles.wrapper}>
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <span className={styles.icon} aria-hidden="true">⬡</span>
          <span className={styles.title}>Sentence Analysis</span>
        </div>
        <div className={styles.legend}>
          <span className={styles.legendItem}>
            <span className={`${styles.dot} ${styles.dotHigh}`} />
            High ({highCount})
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.dot} ${styles.dotMid}`} />
            Medium ({midCount})
          </span>
          <span className={styles.legendItem}>
            <span className={`${styles.dot} ${styles.dotLow}`} />
            Low
          </span>
        </div>
      </div>

      <div className={styles.textBody}>
        {sentences.map((sentence, idx) => (
          <SentenceChip
            key={idx}
            sentence={sentence}
            index={idx}
            isActive={activeIdx === idx}
            onActivate={() => setActiveIdx(activeIdx === idx ? null : idx)}
          />
        ))}
      </div>
    </div>
  )
}

function SentenceChip({ sentence, index, isActive, onActivate }) {
  const { text, score, flags } = sentence
  const level =
    score >= 0.6 ? 'high' :
    score >= 0.35 ? 'mid' : 'low'

  const hasFlags = flags && flags.length > 0

  return (
    <span className={styles.sentenceWrapper}>
      <span
        className={`${styles.sentence} ${styles[`score_${level}`]} ${isActive ? styles.active : ''}`}
        onClick={hasFlags ? onActivate : undefined}
        role={hasFlags ? 'button' : undefined}
        tabIndex={hasFlags ? 0 : undefined}
        onKeyDown={hasFlags ? (e) => e.key === 'Enter' && onActivate() : undefined}
        aria-expanded={hasFlags ? isActive : undefined}
        title={hasFlags ? `Score: ${Math.round(score * 100)}%` : undefined}
      >
        {text}
        {level !== 'low' && (
          <span className={styles.scorePill} aria-hidden="true">
            {Math.round(score * 100)}
          </span>
        )}
      </span>

      {/* Expanded flag tooltip */}
      {isActive && hasFlags && (
        <span className={styles.flagTooltip} role="status">
          {flags.map((flag, i) => (
            <span key={i} className={styles.flagBadge}>{flag}</span>
          ))}
        </span>
      )}
      {' '}
    </span>
  )
}
