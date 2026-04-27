"""
routes/predict.py
FINAL version:
- Confidence (percent + raw)
- UNCERTAIN fallback for scraping failures
- Clean responses
"""

import logging
from fastapi import APIRouter, HTTPException

from models.schemas import (
    TextPredictRequest,
    UrlPredictRequest,
    PredictionResponse,
)
from services.analysis_service import AnalysisService
from services.scraper_service import ScraperService

logger = logging.getLogger(__name__)
router = APIRouter()

_analysis = AnalysisService()
_scraper = ScraperService()


# ── Helpers ─────────────────────────────────────────────

def _format_response(label, confidence, explanation, sentences, domain_info, **extra):
    """
    Standardized response formatting.
    """

    confidence_percent = round(confidence * 100, 1)
    confidence_raw = round(confidence, 3)

    if label == "UNCERTAIN":
        interpretation = "⚠️ The model is not confident. This content may require verification."
    elif label == "FAKE":
        interpretation = "🚨 This content appears suspicious or misleading."
    else:
        interpretation = "✅ This content appears reliable."

    return PredictionResponse(
        label=label,
        confidence=confidence_percent,
        confidence_raw=confidence_raw,
        explanation=explanation or "No detailed explanation available.",
        sentences=sentences or [],
        domain_info=domain_info,
        interpretation=interpretation,
        **extra
    )


# ── TEXT PREDICTION ─────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse)
async def predict_text(body: TextPredictRequest):
    try:
        label, confidence, explanation, sentences, domain_info = _analysis.analyse(
            text=body.text,
            source_url=None,
        )

        logger.info(f"[TEXT] {label} ({confidence:.3f})")

        return _format_response(
            label,
            confidence,
            explanation,
            sentences,
            domain_info
        )

    except Exception as exc:
        logger.exception("Text prediction failed")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")


# ── URL ANALYSIS ────────────────────────────────────────

@router.post("/analyze-url", response_model=PredictionResponse)
async def analyze_url(body: UrlPredictRequest):

    # Step 1: Fetch article
    try:
        article_text, article_title = await _scraper.fetch_article(body.url)

        # Safety check
        if not article_text or len(article_text.strip()) < 50:
            raise ValueError("Insufficient article content")

    except (ValueError, RuntimeError) as exc:
        logger.warning(f"[URL FAIL] {body.url} → {exc}")

        # 🔥 IMPORTANT: fallback instead of error
        return _format_response(
            label="UNCERTAIN",
            confidence=0.5,
            explanation="Could not extract article. This website may block scraping. Try pasting text instead.",
            sentences=[],
            domain_info=None,
            source_url=body.url,
            article_title=None,
        )

    # Step 2: Analyse
    try:
        label, confidence, explanation, sentences, domain_info = _analysis.analyse(
            text=article_text,
            source_url=body.url,
        )

        logger.info(f"[URL] {label} ({confidence:.3f}) → {body.url}")

        return _format_response(
            label,
            confidence,
            explanation,
            sentences,
            domain_info,
            source_url=body.url,
            article_title=article_title,
        )

    except Exception as exc:
        logger.exception("URL analysis failed")

        return _format_response(
            label="UNCERTAIN",
            confidence=0.5,
            explanation="Analysis failed. Try pasting the article text manually.",
            sentences=[],
            domain_info=None,
            source_url=body.url,
            article_title=None,
        )