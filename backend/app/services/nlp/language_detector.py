"""
LanguageDetector — Agent 2 submodule.
Detects document language (fr / ar / en) using langdetect with a fallback
to heuristic keyword matching for short texts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)

# French-specific keywords for heuristic fallback
_FR_KEYWORDS = {"le", "la", "les", "de", "du", "des", "et", "en", "un", "une",
                "est", "sont", "pour", "dans", "avec", "par", "sur", "contrat",
                "article", "partie", "accord"}

# Arabic-specific characters range
_AR_CHAR_PATTERN = re.compile(r"[\u0600-\u06FF]")


@dataclass
class LanguageResult:
    language: str        # "fr" | "ar" | "en" | "unknown"
    confidence: float    # 0.0 – 1.0
    method: str          # "langdetect" | "heuristic" | "arabic_chars"


class LanguageDetector:
    """Detect the primary language of a text document."""

    def detect(self, text: str) -> LanguageResult:
        """
        Detect language from text.
        Returns LanguageResult with language code and confidence.
        """
        if not text or not text.strip():
            return LanguageResult(language="unknown", confidence=0.0, method="empty")

        sample = text[:3000]  # Use first 3000 chars for speed

        # Fast Arabic character check
        ar_chars = len(_AR_CHAR_PATTERN.findall(sample))
        if ar_chars / max(len(sample), 1) > 0.15:
            return LanguageResult(language="ar", confidence=0.95, method="arabic_chars")

        # Try langdetect
        try:
            from langdetect import detect_langs  # type: ignore
            results = detect_langs(sample)
            if results:
                top = results[0]
                lang = top.lang
                conf = round(float(top.prob), 3)
                # Normalize to our supported languages
                if lang in ("fr", "ar", "en"):
                    return LanguageResult(language=lang, confidence=conf, method="langdetect")
                # French variant codes
                if lang in ("fr-ca", "fr-be", "fr-ch"):
                    return LanguageResult(language="fr", confidence=conf, method="langdetect")
                # Arabic variant codes
                if lang.startswith("ar"):
                    return LanguageResult(language="ar", confidence=conf, method="langdetect")
                # Unsupported language — still return it
                return LanguageResult(language=lang, confidence=conf, method="langdetect")
        except Exception as exc:
            logger.warning("langdetect_failed", extra={"extra": {"error": str(exc)}})

        # Heuristic fallback: count French keywords
        words = set(re.findall(r"\b\w+\b", sample.lower()))
        fr_hits = len(words & _FR_KEYWORDS)
        if fr_hits >= 3:
            return LanguageResult(language="fr", confidence=0.6, method="heuristic")

        return LanguageResult(language="unknown", confidence=0.0, method="heuristic")
