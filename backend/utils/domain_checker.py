"""
domain_checker.py
Checks the credibility of a news source domain against curated lists.
Lists are intentionally conservative — when in doubt, return "unknown".
"""

from typing import Optional
from urllib.parse import urlparse

from models.schemas import DomainInfo

# ── Curated domain lists ──────────────────────────────────────────────────────
# Sources: Media Bias / Fact Check, NewsGuard, academic literature on fake news.
# These are indicative examples — extend with a fuller dataset in production.

TRUSTED_DOMAINS = {
    "reuters.com": "International news agency with strict editorial standards.",
    "apnews.com": "Associated Press — gold-standard wire service.",
    "bbc.com": "BBC News — publicly-funded, rigorous editorial policy.",
    "bbc.co.uk": "BBC News — publicly-funded, rigorous editorial policy.",
    "theguardian.com": "Major UK broadsheet with transparent corrections policy.",
    "nytimes.com": "The New York Times — established US newspaper of record.",
    "washingtonpost.com": "The Washington Post — major investigative outlet.",
    "economist.com": "The Economist — rigorous fact-checked journalism.",
    "nature.com": "Nature — peer-reviewed scientific publishing.",
    "science.org": "Science — peer-reviewed scientific publishing.",
    "who.int": "World Health Organization — official UN health body.",
    "cdc.gov": "Centers for Disease Control and Prevention.",
    "nih.gov": "National Institutes of Health.",
    "gov.uk": "UK Government official publications.",
    "nasa.gov": "NASA official communications.",
    "npr.org": "National Public Radio — US public broadcaster.",
    "pbs.org": "Public Broadcasting Service.",
    "politifact.com": "Dedicated fact-checking organisation.",
    "snopes.com": "Long-established fact-checking website.",
    "factcheck.org": "Non-partisan fact-checking by Annenberg Public Policy Center.",
}

UNTRUSTED_DOMAINS = {
    "infowars.com": "Conspiracy-oriented outlet with documented misinformation history.",
    "naturalnews.com": "Health misinformation and conspiracy theories.",
    "beforeitsnews.com": "Aggregator of unverified, often fabricated stories.",
    "yournewswire.com": "Known producer of viral fake news (now newspunch.com).",
    "newspunch.com": "Formerly YourNewsWire — repeated fake news publication.",
    "dcgazette.com": "Satirical / fake news aggregator.",
    "theonion.com": "Satire — not real news (explicitly satirical).",
    "thebabylonbee.com": "Christian satire site — not factual reporting.",
    "worldnewsdailyreport.com": "Documented fake news site.",
    "empirenews.net": "Satirical / fake news site.",
    "abcnews.com.co": "Impersonation of ABC News — fake news domain.",
    "cnn.com.de": "Impersonation of CNN — fake news domain.",
}


class DomainChecker:
    """Checks a URL's domain against curated credibility lists."""

    def check(self, url: str) -> Optional[DomainInfo]:
        """
        Return a DomainInfo object or None if domain cannot be extracted.
        """
        domain = self._extract_domain(url)
        if not domain:
            return None

        # Check exact match first, then check if any listed domain is a suffix
        credibility, note = self._lookup(domain)
        return DomainInfo(domain=domain, credibility=credibility, note=note)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        try:
            parsed = urlparse(url)
            host = parsed.netloc or parsed.path
            # Strip port and www. prefix
            host = host.split(":")[0].lower()
            if host.startswith("www."):
                host = host[4:]
            return host if host else None
        except Exception:
            return None

    @staticmethod
    def _lookup(domain: str):
        """Returns (credibility, note)."""
        # Exact match
        if domain in TRUSTED_DOMAINS:
            return "trusted", TRUSTED_DOMAINS[domain]
        if domain in UNTRUSTED_DOMAINS:
            return "untrusted", UNTRUSTED_DOMAINS[domain]

        # Suffix match (e.g. "uk.reuters.com" → "reuters.com")
        for trusted in TRUSTED_DOMAINS:
            if domain.endswith("." + trusted) or domain == trusted:
                return "trusted", TRUSTED_DOMAINS[trusted]
        for untrusted in UNTRUSTED_DOMAINS:
            if domain.endswith("." + untrusted) or domain == untrusted:
                return "untrusted", UNTRUSTED_DOMAINS[untrusted]

        return "unknown", None
