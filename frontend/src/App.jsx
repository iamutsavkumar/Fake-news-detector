import React from 'react'
import Header from './components/Header'
import AnalyserPanel from './components/AnalyserPanel'
import ResultPanel from './components/ResultPanel'
import Footer from './components/Footer'
import { useAnalysis } from './hooks/useAnalysis'
import styles from './App.module.css'

export default function App() {
  const { result, loading, error, analyse, reset } = useAnalysis()

  return (
    <div className={styles.layout}>
      <Header />

      <main className={styles.main}>
        <AnalyserPanel
          onAnalyse={analyse}
          onReset={reset}
          loading={loading}
          hasResult={!!result}
        />

        {(loading || result || error) && (
          <ResultPanel
            result={result}
            loading={loading}
            error={error}
          />
        )}
      </main>

      <Footer />
    </div>
  )
}
