import logging
import threading
import re
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
        self._loaded = False

    # ----------------------------------------------------
    # Singleton
    # ----------------------------------------------------

    @classmethod
    def get_instance(cls) -> "ModelService":
        if cls._instance is None:
            with _lock:
                if cls._instance is None:
                    cls._instance = cls()

        return cls._instance

    # ----------------------------------------------------
    # Lazy loading
    # ----------------------------------------------------

    def _ensure_loaded(self):
        if self._loaded:
            return

        with _lock:

            if self._loaded:
                return

            if (
                self.model_path.exists()
                and self.vectorizer_path.exists()
            ):

                logger.info(
                    "Loading vectorizer from %s",
                    self.vectorizer_path,
                )

                vectorizer = joblib.load(
                    self.vectorizer_path
                )

                logger.info(
                    "Loading classifier from %s",
                    self.model_path,
                )

                classifier = joblib.load(
                    self.model_path
                )

                self._pipeline = Pipeline(
                    [
                        ("tfidf", vectorizer),
                        ("clf", classifier),
                    ]
                )

                logger.info("Model loaded successfully")

            else:

                logger.warning(
                    "Model files missing. Using heuristic mode."
                )

                self._pipeline = None

            self._loaded = True

    # ----------------------------------------------------
    # Status
    # ----------------------------------------------------

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ----------------------------------------------------
    # Text cleaning
    # ----------------------------------------------------

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"www\S+", "", text)
        text = re.sub(r"\S+@\S+", "", text)
        text = re.sub(r"[^a-zA-Z ]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.lower().strip()

    # ----------------------------------------------------
    # Public prediction
    # ----------------------------------------------------

    def predict(self, text: str) -> Tuple[int, float]:

        self._ensure_loaded()

        text = self._clean_text(text)

        if self._pipeline is not None:
            return self._predict_ml(text)

        return self._predict_heuristic(text)

    def predict_sentence(self, sentence: str) -> float:

        self._ensure_loaded()

        sentence = self._clean_text(sentence)

        if self._pipeline is not None:
            try:
                proba = self._pipeline.predict_proba(
                    [sentence]
                )[0]

                fake_idx = list(
                    self._pipeline.classes_
                ).index(0)

                return float(proba[fake_idx])

            except Exception:
                pass

        return self._heuristic_suspicion(sentence)

    # ----------------------------------------------------
    # ML prediction
    # ----------------------------------------------------

    def _predict_ml(self, text: str) -> Tuple[int, float]:

        proba = self._pipeline.predict_proba(
            [text]
        )[0]

        confidence = float(np.max(proba))

        pred = int(
            self._pipeline.predict([text])[0]
        )

        return pred, round(confidence, 3)

    # ----------------------------------------------------
    # Heuristic fallback
    # ----------------------------------------------------

    def _predict_heuristic(
        self,
        text: str,
    ) -> Tuple[int, float]:

        score = self._heuristic_suspicion(text)

        if score < 0.4:
            return 1, 1.0 - score

        elif score < 0.6:
            return 1, 0.5

        else:
            return 0, score

    # ----------------------------------------------------
    # Heuristic scoring
    # ----------------------------------------------------

    @staticmethod
    def _heuristic_suspicion(text: str) -> float:

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

            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                score += weight

            total += weight

        return round(
            min(
                max(
                    score / total if total else 0.0,
                    0.0,
                ),
                1.0,
            ),
            3,
        )