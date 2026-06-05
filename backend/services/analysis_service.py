"""
AnalysisService — FINAL version (TRUE UNCERTAIN SUPPORT)
"""

import re
import logging
from typing import List, Tuple, Optional

from models.schemas import SentenceAnalysis, DomainInfo
from services.model_service import ModelService
from utils.text_utils import clean_text, split_sentences
from utils.domain_checker import DomainChecker

logger = logging.getLogger(__name__)


_RULE_PATTERNS: List[Tuple[str, str, str]] = [
    (r"\b(breaking|exclusive|shocking|bombshell|exposed)\b",
     "sensational_language", "Sensational language"),
    (r"\b(hoax|conspiracy|deep state|fake media)\b",
     "conspiracy_terms", "Conspiracy terminology"),
    (r"\b(miracle|secret|they don'?t want you to know)\b",
     "clickbait_phrases", "Clickbait phrasing"),
    (r"[A-Z]{5,}",
     "excessive_caps", "Excessive capitalisation"),
    (r"!{2,}",
     "excessive_punctuation", "Excessive punctuation"),
    (r"\b(100%|guaranteed|proven cure|scientifically proven)\b",
     "false_certainty", "False certainty claims"),
    (r"\b(share this|spread the word|wake up|sheeple)\b",
     "call_to_action", "Emotional call-to-action"),
    (r"\b(allegedly|reportedly|anonymous sources?|unverified)\b",
     "unverified_sourcing", "Unverified sourcing language"),
]


class AnalysisService:

    def __init__(self):
        self._model = None
        self._domain_checker = DomainChecker()

    @property
    def model(self):
        """
        Lazy-load ModelService only when a prediction
        is actually requested.
        """
        if self._model is None:
            logger.info("Creating ModelService...")
            self._model = ModelService.get_instance()

        return self._model
    
    def analyse(
        self,
        text: str,
        source_url: Optional[str] = None,
    ) -> Tuple[str, float, str, List[SentenceAnalysis], Optional[DomainInfo]]:

        cleaned = clean_text(text)

        # 🔥 1. SHORT TEXT
        if len(cleaned.split()) < 8:
            return (
                "UNCERTAIN",
                0.5,
                "Text too short for reliable classification.",
                [],
                None,
            )

        # 🔥 2. MODEL PREDICTION
        pred_label, confidence = self.model.predict(cleaned)
        label = "REAL" if pred_label == 1 else "FAKE"

        # 🔥 3. FAKE SIGNAL BOOST
        suspicious_words = ["breaking", "shocking", "unbelievable", "secret", "exposed"]
        boost = sum(0.05 for w in suspicious_words if w in cleaned.lower())
        confidence = min(confidence + boost, 0.95)

        # 🔥 4. REAL UNCERTAIN LOGIC (IMPORTANT PART)

        try:
            proba = self.model._pipeline.predict_proba([cleaned])[0]
            sorted_proba = sorted(proba, reverse=True)
            gap = sorted_proba[0] - sorted_proba[1]
        except Exception:
            gap = 1.0  # fallback (no uncertainty)

        # CASE 1 — low confidence
        if confidence < 0.55:
            label = "UNCERTAIN"

        # CASE 2 — model confused (KEY FIX)
        elif gap < 0.15:
            label = "UNCERTAIN"

        # CASE 3 — weak fake prediction
        elif confidence < 0.65 and label == "FAKE":
            label = "UNCERTAIN"

        # CASE 4 — cap overconfidence
        elif confidence > 0.9:
            confidence = 0.9

        # ─────────────────────────────────────────────
        # SENTENCE ANALYSIS
        # ─────────────────────────────────────────────

        sentences = split_sentences(text)
        sentence_analyses = [self._analyse_sentence(s) for s in sentences]

        # ─────────────────────────────────────────────
        # DOMAIN CHECK
        # ─────────────────────────────────────────────

        domain_info = None
        if source_url:
            domain_info = self._domain_checker.check(source_url)
            confidence = self._adjust_for_domain(confidence, label, domain_info)

        # ─────────────────────────────────────────────
        # EXPLANATION
        # ─────────────────────────────────────────────

        explanation = self._build_explanation(
            label,
            confidence,
            sentence_analyses,
            domain_info
        )

        return label, round(confidence, 3), explanation, sentence_analyses, domain_info

    # ─────────────────────────────────────────────

    def _analyse_sentence(self, sentence: str) -> SentenceAnalysis:
        ml_score = self.model.predict_sentence(sentence)
        flags = self._get_flags(sentence)

        rule_density = min(len(flags) / max(len(_RULE_PATTERNS), 1), 1.0)
        blended_score = round(0.75 * ml_score + 0.25 * rule_density, 3)

        return SentenceAnalysis(
            text=sentence,
            score=blended_score,
            flags=flags,
        )

    def _get_flags(self, sentence: str) -> List[str]:
        flags = []
        for pattern, _, label in _RULE_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                flags.append(label)
        return flags

    # ─────────────────────────────────────────────

    def _adjust_for_domain(
        self,
        confidence: float,
        label: str,
        domain_info: Optional[DomainInfo],
    ) -> float:
        if domain_info is None:
            return confidence

        adjustment = 0.0

        if domain_info.credibility == "trusted" and label == "REAL":
            adjustment = +0.05
        elif domain_info.credibility == "untrusted" and label == "FAKE":
            adjustment = +0.05
        elif domain_info.credibility == "trusted" and label == "FAKE":
            adjustment = -0.05
        elif domain_info.credibility == "untrusted" and label == "REAL":
            adjustment = -0.05

        return round(min(max(confidence + adjustment, 0.0), 1.0), 3)

    # ─────────────────────────────────────────────

    def _build_explanation(
        self,
        label: str,
        confidence: float,
        sentences: List[SentenceAnalysis],
        domain_info: Optional[DomainInfo],
    ) -> str:

        pct = int(confidence * 100)
        parts: List[str] = []

        if label == "FAKE":
            parts.append(f"The article shows {pct}% likelihood of being misleading.")
        elif label == "REAL":
            parts.append(f"The article appears credible with {pct}% confidence.")
        else:
            parts.append("The model is uncertain about this content.")

        all_flags: List[str] = []
        for s in sentences:
            all_flags.extend(s.flags)

        if all_flags:
            from collections import Counter
            top = Counter(all_flags).most_common(3)
            parts.append(
                "Detected signals include: " +
                ", ".join(f[0] for f in top)
            )

        suspicious_count = sum(1 for s in sentences if s.score >= 0.6)
        if suspicious_count:
            parts.append(
                f"{suspicious_count} sentence(s) flagged as suspicious."
            )

        if domain_info:
            if domain_info.credibility == "trusted":
                parts.append(f"Source '{domain_info.domain}' is credible.")
            elif domain_info.credibility == "untrusted":
                parts.append(f"Source '{domain_info.domain}' is low credibility.")

        return " ".join(parts)