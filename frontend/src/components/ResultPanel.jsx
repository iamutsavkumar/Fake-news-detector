import React from 'react'
import LoadingState from './LoadingState'
import ErrorState from './ErrorState'
import VerdictCard from './VerdictCard'
import ConfidenceBar from './ConfidenceBar'
import ExplanationCard from './ExplanationCard'
import HighlightedText from './HighlightedText'
import DomainBadge from './DomainBadge'
import styles from './ResultPanel.module.css'

export default function ResultPanel({ result, loading, error }) {
  if (loading) return <LoadingState />
  if (error)   return <ErrorState message={error} />
  if (!result) return null

  const {
    label, confidence, explanation,
    sentences, domain_info, source_url, article_title,
  } = result

  return (
    <section className={styles.container} aria-live="polite">
      {/* Article meta (when URL mode) */}
      {article_title && (
        <div className={`${styles.articleMeta} fade-up`}>
          <span className={styles.metaLabel}>Article</span>
          <span className={styles.metaTitle}>{article_title}</span>
          {source_url && (
            <a href={source_url} target="_blank" rel="noopener noreferrer"
               className={styles.metaLink}>
              ↗ Source
            </a>
          )}
        </div>
      )}

      {/* Top row: verdict + confidence */}
      <div className={`${styles.topRow} fade-up fade-up-delay-1`}>
        <VerdictCard label={label} confidence={confidence} />
        <div className={styles.rightCol}>
          <ConfidenceBar confidence={confidence} label={label} />
          {domain_info && <DomainBadge info={domain_info} />}
        </div>
      </div>

      {/* Explanation */}
      <div className={`fade-up fade-up-delay-2`}>
        <ExplanationCard explanation={explanation} />
      </div>

      {/* Sentence-level highlight */}
      {sentences && sentences.length > 0 && (
        <div className={`fade-up fade-up-delay-3`}>
          <HighlightedText sentences={sentences} />
        </div>
      )}
    </section>
  )
}
