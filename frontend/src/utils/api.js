/**
 * api.js — Thin Axios client for the FastAPI backend.
 * All API calls live here; components never import axios directly.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''  // empty = proxy via Vite

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor (e.g. auth tokens) ────────────────────────────────────
client.interceptors.request.use((config) => config)

// ── Response error normaliser ────────────────────────────────────────────────
client.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail =
      err?.response?.data?.detail ??
      err?.message ??
      'An unknown error occurred'
    return Promise.reject(new Error(String(detail)))
  }
)

// ── API methods ───────────────────────────────────────────────────────────────

/**
 * POST /api/v1/predict
 * @param {string} text - Raw news article text
 * @returns {Promise<PredictionResult>}
 */
export async function predictText(text) {
  const { data } = await client.post('/api/v1/predict', { text })
  return data
}

/**
 * POST /api/v1/analyze-url
 * @param {string} url - URL to scrape and analyse
 * @returns {Promise<PredictionResult>}
 */
export async function analyzeUrl(url) {
  const { data } = await client.post('/api/v1/analyze-url', { url })
  return data
}

/**
 * GET /health
 * @returns {Promise<{ status: string, model_loaded: boolean }>}
 */
export async function checkHealth() {
  const { data } = await client.get('/health')
  return data
}
