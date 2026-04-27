/**
 * useAnalysis.js
 * Encapsulates all prediction state and API calls.
 * Components stay clean — no API logic in JSX files.
 */

import { useState, useCallback } from 'react'
import { predictText, analyzeUrl } from '../utils/api'

const INITIAL_STATE = {
  result: null,
  loading: false,
  error: null,
}

export function useAnalysis() {
  const [state, setState] = useState(INITIAL_STATE)

  const analyse = useCallback(async ({ mode, text, url }) => {
    setState({ result: null, loading: true, error: null })
    try {
      const result =
        mode === 'url' ? await analyzeUrl(url) : await predictText(text)
      setState({ result, loading: false, error: null })
    } catch (err) {
      setState({ result: null, loading: false, error: err.message })
    }
  }, [])

  const reset = useCallback(() => setState(INITIAL_STATE), [])

  return { ...state, analyse, reset }
}
