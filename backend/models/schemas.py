"""
Pydantic schemas for API request and response validation.
Updated for:
- confidence (percent + raw)
- UNCERTAIN label
- interpretation field
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Requests ────────────────────────────────────────────

class TextPredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=20,
        max_length=50_000,
        description="Raw news article text to classify."
    )

    model_config = {
        "json_schema_extra": {
            "example": {"text": "Scientists discover new vaccine..."}
        }
    }


class UrlPredictRequest(BaseModel):
    url: str = Field(
        ...,
        description="URL of the news article to fetch and classify."
    )


# ── Sub-models ──────────────────────────────────────────

class SentenceAnalysis(BaseModel):
    text: str
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Suspicion score: 1.0 = very suspicious."
    )
    flags: List[str] = Field(
        default_factory=list,
        description="Triggered rule labels."
    )


class DomainInfo(BaseModel):
    domain: str
    credibility: str  # "trusted" | "untrusted" | "unknown"
    note: Optional[str] = None


# ── Responses ───────────────────────────────────────────

class PredictionResponse(BaseModel):
    # 🔥 Updated label types
    label: str = Field(
        ...,
        description="Prediction label: REAL | FAKE | UNCERTAIN"
    )

    # 🔥 UI-friendly confidence (percentage)
    confidence: float = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence percentage (0–100)"
    )

    # 🔥 Raw model confidence
    confidence_raw: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Raw model confidence (0–1)"
    )

    # 🔥 New interpretation field
    interpretation: Optional[str] = Field(
        None,
        description="Human-readable interpretation of result"
    )

    explanation: str
    sentences: List[SentenceAnalysis]

    domain_info: Optional[DomainInfo] = None
    source_url: Optional[str] = None
    article_title: Optional[str] = None


# ── Health ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str = "1.0.0"