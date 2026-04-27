"""
ScraperService — robust multi-strategy scraper (FINAL FIXED VERSION)

Handles:
- Reuters blocking
- Empty extraction issues
- Multiple fallback layers
"""

import logging
import re
from typing import Optional, Tuple
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from newspaper import Article
import trafilatura

from config import get_settings

logger = logging.getLogger(__name__)


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/",
}


class ScraperService:
    def __init__(self):
        self._timeout = get_settings().scrape_timeout

    async def fetch_article(self, url: str) -> Tuple[str, Optional[str]]:
        self._validate_url(url)

        # ───────────── STEP 1: newspaper ─────────────
        try:
            article = Article(url)
            article.download()
            article.parse()

            text = article.text
            title = article.title

            if text and len(text.strip()) > 100:
                logger.info("✅ newspaper3k success")
                return self._clean(text), title

        except Exception as e:
            logger.warning(f"Newspaper failed: {e}")

        # ───────────── STEP 2: httpx fetch ─────────────
        html = None

        try:
            async with httpx.AsyncClient(
                headers=_HEADERS,
                timeout=self._timeout,
                follow_redirects=True,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

        except Exception as e:
            logger.warning(f"HTTP fetch failed: {e}")

        # ───────────── STEP 3: BeautifulSoup ─────────────
        if html:
            text, title = self._parse_html(html)

            if text and len(text.strip()) > 80:
                logger.info("✅ BeautifulSoup success")
                return self._clean(text), title

        # ───────────── STEP 4: trafilatura (FIXED) ─────────────
        try:
            downloaded = trafilatura.fetch_url(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://www.google.com/"
                }
            )

            text = trafilatura.extract(downloaded)

            if text and len(text.strip()) > 80:
                logger.info("✅ trafilatura success")
                return self._clean(text), None

        except Exception as e:
            logger.warning(f"Trafilatura failed: {e}")

        # ───────────── STEP 5: FORCE PARAGRAPH EXTRACTION (NEW) ─────────────
        try:
            logger.warning("⚠️ Using forced paragraph extraction")

            async with httpx.AsyncClient(headers=_HEADERS) as client:
                response = await client.get(url)
                html = response.text

            soup = BeautifulSoup(html, "lxml")
            paragraphs = soup.find_all("p")

            text = " ".join(p.get_text(strip=True) for p in paragraphs)

            if text and len(text.strip()) > 50:
                logger.info("✅ Forced extraction success")
                return self._clean(text), None

        except Exception as e:
            logger.warning(f"Forced extraction failed: {e}")

        # ───────────── FINAL FAIL ─────────────
        raise ValueError(
            "Could not extract article. This site may block scraping or require login."
        )

    # ───────────── HELPERS ─────────────

    @staticmethod
    def _validate_url(url: str):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must begin with http:// or https://")
        if not parsed.netloc:
            raise ValueError("Invalid URL — missing host.")

    @staticmethod
    def _clean(text: str) -> str:
        text = re.sub(r"\s{2,}", " ", text)
        text = text.strip()
        return text[:3000]

    @staticmethod
    def _parse_html(html: str) -> Tuple[str, Optional[str]]:
        soup = BeautifulSoup(html, "lxml")

        title = None
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title:
            title = soup.title.get_text(strip=True)

        for tag in soup([
            "script", "style", "nav", "header", "footer",
            "aside", "noscript", "iframe"
        ]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text(strip=True) for p in paragraphs)

        text = re.sub(r"\s{2,}", " ", text).strip()

        return text, title