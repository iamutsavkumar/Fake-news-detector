"""
text_utils.py
Shared text preprocessing utilities used by both the API and the ML training script.
"""

import re
import string
from typing import List

# Optional NLTK — downloaded lazily on first use
_STOPWORDS = None
_LEMMATIZER = None


def _get_stopwords():
    global _STOPWORDS
    if _STOPWORDS is None:
        try:
            from nltk.corpus import stopwords
            import nltk
            try:
                _STOPWORDS = set(stopwords.words("english"))
            except LookupError:
                nltk.download("stopwords", quiet=True)
                _STOPWORDS = set(stopwords.words("english"))
        except ImportError:
            _STOPWORDS = set()
    return _STOPWORDS


def _get_lemmatizer():
    global _LEMMATIZER
    if _LEMMATIZER is None:
        try:
            from nltk.stem import WordNetLemmatizer
            import nltk
            try:
                _LEMMATIZER = WordNetLemmatizer()
                _LEMMATIZER.lemmatize("test")  # trigger corpus load
            except LookupError:
                nltk.download("wordnet", quiet=True)
                nltk.download("omw-1.4", quiet=True)
                _LEMMATIZER = WordNetLemmatizer()
        except ImportError:
            _LEMMATIZER = None
    return _LEMMATIZER


# ── Public functions ──────────────────────────────────────────────────────────

def clean_text(text: str, lemmatize: bool = False) -> str:
    """
    Full preprocessing pipeline:
      1. Lowercase
      2. Remove URLs, emails, mentions
      3. Remove punctuation & digits
      4. Collapse whitespace
      5. Remove stopwords (optional)
      6. Lemmatize (optional — off by default for speed in inference)
    """
    text = text.lower()
    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    # Remove emails
    text = re.sub(r"\S+@\S+", " ", text)
    # Remove social-media mentions / hashtags
    text = re.sub(r"[@#]\w+", " ", text)
    # Remove punctuation
    text = text.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    # Remove digits
    text = re.sub(r"\d+", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    if lemmatize:
        lemmatizer = _get_lemmatizer()
        stopwords = _get_stopwords()
        tokens = text.split()
        if lemmatizer:
            tokens = [lemmatizer.lemmatize(t) for t in tokens]
        tokens = [t for t in tokens if t not in stopwords and len(t) > 1]
        text = " ".join(tokens)

    return text


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences using a simple regex heuristic.
    Falls back to NLTK sent_tokenize when available.
    Only returns sentences with at least 5 words.
    """
    try:
        import nltk
        try:
            sentences = nltk.sent_tokenize(text)
        except LookupError:
            nltk.download("punkt", quiet=True)
            nltk.download("punkt_tab", quiet=True)
            sentences = nltk.sent_tokenize(text)
    except (ImportError, Exception):
        # Regex fallback
        sentences = re.split(r"(?<=[.!?])\s+", text)

    return [s.strip() for s in sentences if s.strip() and len(s.split()) >= 5]


def tokenize(text: str) -> List[str]:
    """Simple whitespace tokenizer after cleaning."""
    return clean_text(text).split()
