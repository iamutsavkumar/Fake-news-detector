"""
AnalysisService — orchestrates the full analysis pipeline:
  1. Text cleaning
  2. Sentence segmentation
  3. Per-sentence suspicion scoring
  4. Explanation generation
  5. Domain credibility check
"""

import re
import logging
from typing import List, Tuple, Optional

from models.schemas import SentenceAnalysis, DomainInfo
from services.model_service import ModelService
from utils.text_utils import clean_text, split_sentences
from utils.domain_checker import DomainChecker

logger = logging.getLogger(__name__)

# Patterns that trigger specific explanation flags
_RULE_PATTERNS: List[Tuple[str, str, str]] = [
    # (pattern, flag_key, human label)
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
    (r"\b(muslims?|jews?|immigrants?|liberals?|conservatives?)\b.*\b(all|always|never|hate|evil)\b",
     "generalisation", "Harmful generalisation"),
]


class AnalysisService:
    """
    Stateless service; call analyse() for the full pipeline.
    """

    def __init__(self):
        self._model = ModelService.get_instance()
        self._domain_checker = DomainChecker()

    # ── Public API ────────────────────────────────────────────────────────────

    def analyse(
        self,
        text: str,
        source_url: Optional[str] = None,
    ) -> Tuple[str, float, str, List[SentenceAnalysis], Optional[DomainInfo]]:
        """
        Full analysis pipeline.

        Returns:
            label        — "REAL" | "FAKE"
            confidence   — float [0, 1]
            explanation  — human-readable string
            sentences    — per-sentence breakdown
            domain_info  — optional domain credibility object
        """
        cleaned = clean_text(text)
        label, confidence = self._model.predict(cleaned)

        sentences = split_sentences(text)
        sentence_analyses = [self._analyse_sentence(s) for s in sentences]

        domain_info = None
        if source_url:
            domain_info = self._domain_checker.check(source_url)
            # Domain credibility adjusts final confidence slightly
            confidence = self._adjust_for_domain(confidence, label, domain_info)

        explanation = self._build_explanation(label, confidence, sentence_analyses, domain_info)

        return label, round(confidence, 3), explanation, sentence_analyses, domain_info

    # ── Private helpers ───────────────────────────────────────────────────────

    def _analyse_sentence(self, sentence: str) -> SentenceAnalysis:
        """Score a single sentence and collect triggered rule flags."""
        ml_score = self._model.predict_sentence(sentence)
        flags = self._get_flags(sentence)

        # Blend ML score (primary) with rule density (secondary signal)
        rule_density = min(len(flags) / max(len(_RULE_PATTERNS), 1), 1.0)
        blended_score = round(0.75 * ml_score + 0.25 * rule_density, 3)

        return SentenceAnalysis(
            text=sentence,
            score=blended_score,
            flags=flags,
        )

    def _get_flags(self, sentence: str) -> List[str]:
        """Return human-readable labels for triggered rules."""
        flags = []
        for pattern, _, label in _RULE_PATTERNS:
            if re.search(pattern, sentence, re.IGNORECASE):
                flags.append(label)
        return flags

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

    def _build_explanation(
        self,
        label: str,
        confidence: float,
        sentences: List[SentenceAnalysis],
        domain_info: Optional[DomainInfo],
    ) -> str:
        """
        Generate a concise, human-readable explanation for the prediction.
        Combines model confidence, triggered patterns, and domain signals.
        """
        pct = int(confidence * 100)
        parts: List[str] = []

        if label == "FAKE":
            parts.append(f"The article shows {pct}% likelihood of being fabricated or misleading.")
        else:
            parts.append(f"The article appears credible with {pct}% confidence.")

        # Summarise the most common flags
        all_flags: List[str] = []
        for s in sentences:
            all_flags.extend(s.flags)

        if all_flags:
            from collections import Counter
            top = Counter(all_flags).most_common(3)
            flag_summary = ", ".join(f[0] for f in top)
            parts.append(f"Detected signals include: {flag_summary}.")

        # High-suspicion sentence count
        suspicious_count = sum(1 for s in sentences if s.score >= 0.6)
        if suspicious_count:
            parts.append(
                f"{suspicious_count} sentence{'s' if suspicious_count > 1 else ''} "
                f"flagged as highly suspicious."
            )

        # Domain
        if domain_info:
            if domain_info.credibility == "trusted":
                parts.append(f"Source domain '{domain_info.domain}' is a recognised credible outlet.")
            elif domain_info.credibility == "untrusted":
                parts.append(
                    f"Source domain '{domain_info.domain}' is flagged as a low-credibility outlet."
                )

        return " ".join(parts)
