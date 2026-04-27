import React, { useState, useRef } from 'react'
import styles from './AnalyserPanel.module.css'

const MIN_TEXT_LENGTH = 40

export default function AnalyserPanel({ onAnalyse, onReset, loading, hasResult }) {
  const [mode, setMode] = useState('text')   // 'text' | 'url'
  const [text, setText] = useState('')
  const [url, setUrl]   = useState('')
  const textRef = useRef(null)

  const isValid =
    mode === 'url'
      ? url.trim().startsWith('http')
      : text.trim().length >= MIN_TEXT_LENGTH

  function handleSubmit(e) {
    e.preventDefault()
    if (!isValid || loading) return
    onAnalyse({ mode, text: text.trim(), url: url.trim() })
  }

  function handleReset() {
    setText('')
    setUrl('')
    onReset()
    textRef.current?.focus()
  }

  const charCount = text.length

  return (
    <section className={`${styles.panel} fade-up`}>
      {/* ── Mode Tabs ─────────────────────────────────────────── */}
      <div className={styles.tabs} role="tablist" aria-label="Input mode">
        <button
          role="tab"
          aria-selected={mode === 'text'}
          className={`${styles.tab} ${mode === 'text' ? styles.tabActive : ''}`}
          onClick={() => setMode('text')}
          type="button"
        >
          <span className={styles.tabIcon}>⌨</span> Paste Text
        </button>
        <button
          role="tab"
          aria-selected={mode === 'url'}
          className={`${styles.tab} ${mode === 'url' ? styles.tabActive : ''}`}
          onClick={() => setMode('url')}
          type="button"
        >
          <span className={styles.tabIcon}>⊕</span> Analyse URL
        </button>
      </div>

      {/* ── Form ─────────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className={styles.form} noValidate>
        {mode === 'text' ? (
          <div className={styles.textareaWrapper}>
            <textarea
              ref={textRef}
              className={styles.textarea}
              placeholder="Paste a news article here…&#10;&#10;Minimum 40 characters. More text = better accuracy."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              maxLength={50000}
              aria-label="News article text"
              disabled={loading}
              spellCheck={false}
            />
            <div className={styles.charCount}>
              <span className={charCount < MIN_TEXT_LENGTH ? styles.charWarn : styles.charOk}>
                {charCount}
              </span>
              {' '}/ 50,000
            </div>
          </div>
        ) : (
          <div className={styles.urlWrapper}>
            <span className={styles.urlPrefix}>https://</span>
            <input
              type="url"
              className={styles.urlInput}
              placeholder="www.example.com/article-title"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              aria-label="Article URL"
              disabled={loading}
              autoFocus
            />
          </div>
        )}

        {/* ── Actions ───────────────────────────────────────── */}
        <div className={styles.actions}>
          <button
            type="submit"
            className={styles.btnAnalyse}
            disabled={!isValid || loading}
          >
            {loading ? (
              <span className={styles.loadingLabel}>
                <span className={styles.spinner} aria-hidden="true" />
                Analysing…
              </span>
            ) : (
              <>◈ Analyse</>
            )}
          </button>

          {(hasResult || text || url) && !loading && (
            <button
              type="button"
              className={styles.btnReset}
              onClick={handleReset}
            >
              ↺ Reset
            </button>
          )}
        </div>

        {mode === 'text' && text.length > 0 && text.length < MIN_TEXT_LENGTH && (
          <p className={styles.hint}>
            {MIN_TEXT_LENGTH - text.length} more characters needed for analysis.
          </p>
        )}
      </form>
    </section>
  )
}
