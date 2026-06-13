"""
routes/predict.py

FINAL version:

* Lazy-loaded AnalysisService (prevents startup OOM)
* Thread-safe singleton via lru_cache
* Confidence (percent + raw)
* UNCERTAIN fallback for scraping failures
* Clean responses
"""

import logging
from functools import lru_cache

from fastapi import APIRouter, HTTPException

# FIXED IMPORTS
from ..models.schemas import (
    TextPredictRequest,
    UrlPredictRequest,
    PredictionResponse,
)

from ..services.analysis_service import AnalysisService
from ..services.scraper_service import ScraperService

logger = logging.getLogger(__name__)
router = APIRouter()
# ── Services ────────────────────────────────────────────

_scraper = ScraperService()


@lru_cache(maxsize=1)
def get_analysis_service() -> AnalysisService:
    """
    Lazily create AnalysisService only when needed.
    Prevents loading large ML models during app startup.
    """
    logger.info("Creating AnalysisService...")
    return AnalysisService()


# ── Helpers ─────────────────────────────────────────────

def _format_response(
    label: str,
    confidence: float,
    explanation: str | None,
    sentences: list | None,
    domain_info,
    **extra,
) -> PredictionResponse:
    """
    Standardized response formatting.
    """

    confidence = max(0.0, min(1.0, float(confidence)))

    confidence_percent = round(confidence * 100, 1)
    confidence_raw = round(confidence, 3)

    if label == "UNCERTAIN":
        interpretation = (
            "⚠️ The model is not confident. "
            "This content may require verification."
        )
    elif label == "FAKE":
        interpretation = (
            "🚨 This content appears suspicious or misleading."
        )
    else:
        interpretation = (
            "✅ This content appears reliable."
        )

    return PredictionResponse(
        label=label,
        confidence=confidence_percent,
        confidence_raw=confidence_raw,
        explanation=explanation or "No detailed explanation available.",
        sentences=sentences or [],
        domain_info=domain_info,
        interpretation=interpretation,
        **extra,
    )


# ── TEXT PREDICTION ─────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse)
async def predict_text(body: TextPredictRequest):
    """
    Analyze raw text submitted by the user.
    """

    try:
        analysis = get_analysis_service()

        (
            label,
            confidence,
            explanation,
            sentences,
            domain_info,
        ) = analysis.analyse(
            text=body.text,
            source_url=None,
        )

        logger.info(
            "[TEXT] %s (%.3f)",
            label,
            confidence,
        )

        return _format_response(
            label=label,
            confidence=confidence,
            explanation=explanation,
            sentences=sentences,
            domain_info=domain_info,
        )

    except Exception as exc:
        logger.exception("Text prediction failed")

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {exc}",
        )


# ── URL ANALYSIS ────────────────────────────────────────

@router.post("/analyze-url", response_model=PredictionResponse)
async def analyze_url(body: UrlPredictRequest):
    """
    Fetch article from URL and analyze its content.
    """

    # Step 1: Fetch article
    try:
        article_text, article_title = await _scraper.fetch_article(
            body.url
        )

        if not article_text or len(article_text.strip()) < 50:
            raise ValueError("Insufficient article content")

    except (ValueError, RuntimeError) as exc:
        logger.warning(
            "[URL FAIL] %s → %s",
            body.url,
            exc,
        )

        return _format_response(
            label="UNCERTAIN",
            confidence=0.5,
            explanation=(
                "Could not extract article. "
                "This website may block scraping. "
                "Try pasting the article text instead."
            ),
            sentences=[],
            domain_info=None,
            source_url=body.url,
            article_title=None,
        )

    # Step 2: Analyze content
    try:
        analysis = get_analysis_service()

        (
            label,
            confidence,
            explanation,
            sentences,
            domain_info,
        ) = analysis.analyse(
            text=article_text,
            source_url=body.url,
        )

        logger.info(
            "[URL] %s (%.3f) → %s",
            label,
            confidence,
            body.url,
        )

        return _format_response(
            label=label,
            confidence=confidence,
            explanation=explanation,
            sentences=sentences,
            domain_info=domain_info,
            source_url=body.url,
            article_title=article_title,
        )

    except Exception:
        logger.exception("URL analysis failed")

        return _format_response(
            label="UNCERTAIN",
            confidence=0.5,
            explanation=(
                "Analysis failed. "
                "Try pasting the article text manually."
            ),
            sentences=[],
            domain_info=None,
            source_url=body.url,
            article_title=article_title,
        )