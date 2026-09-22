"""Language detection for triage messages."""

import re
from typing import Literal


def detect_language(text: str) -> Literal["en", "other"]:
    """Detect language as English or other.

    Uses two heuristics:
    1. If fewer than 80% of alphabetic characters are ASCII letters, return 'other'.
    2. If 4+ word tokens and none is in English stopword set, return 'other'.
    3. Otherwise return 'en'.

    Args:
        text: The text to analyze.

    Returns:
        'en' for English, 'other' for non-English.
    """
    # Heuristic 1: ASCII letter percentage
    letters = [c for c in text if c.isalpha()]
    if letters:
        ascii_letters = [c for c in letters if ord(c) < 128]
        if len(ascii_letters) / len(letters) < 0.80:
            return "other"

    # Heuristic 2: English stopword check
    stopwords = {
        "the",
        "and",
        "is",
        "are",
        "my",
        "i",
        "to",
        "of",
        "a",
        "in",
        "it",
        "you",
        "for",
        "have",
        "with",
        "that",
        "this",
        "me",
        "can",
        "not",
        "on",
        "was",
        "when",
        "what",
        "how",
        "please",
        "order",
        "been",
        "has",
        "do",
        "does",
    }

    # Split into word tokens
    tokens = re.findall(r"\b\w+\b", text.lower())
    if len(tokens) >= 4:
        # If none of the tokens are stopwords, it's probably non-English
        if not any(token in stopwords for token in tokens):
            return "other"

    return "en"
