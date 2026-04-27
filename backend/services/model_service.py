"""
ModelService — improved version with:
- Better preprocessing (matches training)
- Confidence-based decision (UNCERTAIN handling)
- Cleaner ML + heuristic integration
"""

import logging
import threading
import re
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from config import get_settings

logger = logging.getLogger(__name__)
_lock = threading.Lock()


class ModelService:
    _instance: Optional["ModelService"] = None

    def __init__(self):
        settings = get_settings()
        self.model_path = settings.abs_model_path
        self.vectorizer_path = settings.abs_vectorizer_path
        self._pipeline: Optional[Pipeline] = None
        self._load()

    # ── Singleton ─────────────────────────────────────────

    @classmethod
    def get_instance(cls) -> "ModelService":
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── Model loading ─────────────────────────────────────

    def _load(self):
        if self.model_path.exists() and self.vectorizer_path.exists():
            logger.info("Loading model from %s", self.model_path)

            vectorizer = joblib.load(self.vectorizer_path)
            classifier = joblib.load(self.model_path)

            self._pipeline = Pipeline([
                ("tfidf", vectorizer),
                ("clf", classifier),
            ])

            logger.info("Model loaded successfully.")
        else:
            logger.warning(
                "Model not found — using heuristic fallback."
            )
            self._pipeline = None

    @property
    def is_loaded(self) -> bool:
        return self._pipeline is not None

    # ── 🔥 NEW: CLEANING (must match training) ─────────────

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"www\S+", "", text)
        text = re.sub(r"\S+@\S+", "", text)
        text = re.sub(r"[^a-zA-Z ]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.lower().strip()

    # ── Inference ─────────────────────────────────────────

    def predict(self, text: str) -> Tuple[str, float]:
        text = self._clean_text(text)

        if self._pipeline is not None:
            return self._predict_ml(text)

        return self._predict_heuristic(text)

    def predict_sentence(self, sentence: str) -> float:
        sentence = self._clean_text(sentence)

        if self._pipeline is not None:
            try:
                proba = self._pipeline.predict_proba([sentence])[0]
                fake_idx = list(self._pipeline.classes_).index("FAKE")
                return float(proba[fake_idx])
            except Exception:
                pass

        return self._heuristic_suspicion(sentence)

    # ── ML Prediction ─────────────────────────────────────

    def _predict_ml(self, text: str) -> Tuple[str, float]:
        proba = self._pipeline.predict_proba([text])[0]
        classes = list(self._pipeline.classes_)

        predicted_class = classes[np.argmax(proba)]
        confidence = float(np.max(proba))

        # 🔥 NEW: smarter decision logic
        if confidence < 0.6:
            label = "UNCERTAIN"
        else:
            label = predicted_class

        return label, round(confidence, 3)

    # ── Heuristic fallback ────────────────────────────────

    def _predict_heuristic(self, text: str) -> Tuple[str, float]:
        score = self._heuristic_suspicion(text)

        if score < 0.4:
            label = "REAL"
        elif score < 0.6:
            label = "UNCERTAIN"
        else:
            label = "FAKE"

        confidence = score if label == "FAKE" else 1.0 - score
        return label, round(confidence, 3)

    # ── Heuristic scoring ─────────────────────────────────

    @staticmethod
    def _heuristic_suspicion(text: str) -> float:
        lower = text.lower()

        score = 0.0
        total = 0.0

        checks = [
            (r"\b(breaking|exclusive|shocking|bombshell)\b", 0.25),
            (r"\b(hoax|conspiracy|fake media)\b", 0.30),
            (r"\b(miracle|secret|they don'?t want you to know)\b", 0.20),
            (r"[A-Z]{4,}", 0.15),
            (r"!{2,}", 0.10),
            (r"\b(100%|guaranteed|proven)\b", 0.15),
            (r"\b(share this|wake up|sheeple)\b", 0.20),
        ]

        for pattern, weight in checks:
            if re.search(pattern, text, re.IGNORECASE):
                score += weight
            total += weight

        return round(min(max(score / total if total else 0.0, 0.0), 1.0), 3)