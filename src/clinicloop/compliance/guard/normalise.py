"""Text normalisation for guard pattern matching."""

import html
import re
import unicodedata

# Confusable mapping: Cyrillic/Greek look-alikes to Latin
CONFUSABLES = {
    # Cyrillic to Latin
    "а": "a",  # а Cyrillic a
    "е": "e",  # е Cyrillic e
    "о": "o",  # о Cyrillic o
    "р": "p",  # р Cyrillic p
    "с": "c",  # с Cyrillic s
    "х": "x",  # х Cyrillic x
    "у": "y",  # у Cyrillic u
    "ѕ": "s",  # ѕ Cyrillic dz
    "і": "i",  # і Cyrillic i
    "и": "i",  # и Cyrillic i (looks like i)
    "ј": "j",  # ј Cyrillic short i
    "ԁ": "d",  # ԁ Cyrillic d with hook
    "л": "l",  # л Cyrillic el (looks like l)
    # Greek to Latin
    "ν": "v",  # ν Greek nu
    "ο": "o",  # ο Greek omicron
    "ι": "i",  # ι Greek iota
    # Uppercase versions
    "Α": "A",  # Α Greek Alpha
    "Β": "B",  # Β Greek Beta
    "Ε": "E",  # Ε Greek Epsilon
    "Ο": "O",  # Ο Greek Omicron
    "Τ": "T",  # Τ Greek Tau
    "Ι": "I",  # Ι Greek Iota
    "Ν": "N",  # Ν Greek Nu
    "Ζ": "Z",  # Ζ Greek Zeta
}


def normalise(text: str) -> str:
    """Normalise text for pattern matching.

    Applies normalisation steps in order:
    1. HTML entity decode
    2. NFKC normalization
    3. Strip zero-width and format characters
    4. Fold confusables (Cyrillic/Greek to Latin)
    5. Lowercase
    6. Leet substitution inside alphabetic tokens only
    7. Collapse letter-separator obfuscation (5+ single letters separated)

    Args:
        text: Raw input text.

    Returns:
        Normalised text ready for pattern matching.
    """
    # Step 1: HTML entity decode
    text = html.unescape(text)

    # Step 2: NFKC normalization
    text = unicodedata.normalize("NFKC", text)

    # Step 3: Strip zero-width and format characters
    zero_width_chars = {
        "​",  # Zero-width space
        "‌",  # Zero-width non-joiner
        "‍",  # Zero-width joiner
        "⁠",  # Word joiner
        "﻿",  # Zero-width no-break space
        "­",  # Soft hyphen
    }
    for char in zero_width_chars:
        text = text.replace(char, "")

    # Step 3b: Collapse whitespace runs (double spaces, tabs, newlines) to one space
    text = re.sub(r"\s+", " ", text)

    # Step 4: Fold confusables
    for cyrillic, latin in CONFUSABLES.items():
        text = text.replace(cyrillic, latin)

    # Step 5: Lowercase
    text = text.lower()

    # Step 6: Leet substitution inside alphabetic tokens only
    # Match tokens starting with a letter, optionally followed by leet chars
    leet_map = {
        "4": "a",
        "3": "e",
        "1": "i",
        "0": "o",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
    }

    def replace_leet_in_token(match):  # type: ignore[no-untyped-def]
        """Replace leet inside a token that starts with a letter."""
        token = match.group(0)
        for leet_char, letter in leet_map.items():
            token = token.replace(leet_char, letter)
        return token

    # Match tokens that start with a letter, followed by any combination of letters and leet chars
    # Leet chars that we care about: 0, 1, 3, 4, 5, 7, @, $
    leet_chars = r"[013457@$]"
    text = re.sub(f"[a-z]({leet_chars}|[a-z])*", replace_leet_in_token, text)

    # Step 7: Collapse letter-separator obfuscation (5+ single letters separated)
    # Match runs of 5+ single letters separated by the SAME separator
    # Pattern: letter (sep letter){4,} where sep is consistent (all spaces or all dots, etc.)
    # This prevents matching across word boundaries with different separators

    separators = [" ", ".", "-", "_", "*"]
    for sep in separators:
        # Pattern: (^|non-letter) then letter, then 4+ more instances of (sep + letter)
        # Use lookbehind and lookahead to preserve word boundaries
        pattern = f"(?<![a-z])[a-z](?:{re.escape(sep)}[a-z]){{4,}}(?![a-z])"

        def replace_match(match):  # type: ignore[no-untyped-def]
            matched = match.group(0)
            # Remove separator, preserving first character
            first_char = matched[0]
            rest = matched[1:].replace(sep, "")
            return first_char + rest

        text = re.sub(pattern, replace_match, text)

    return text
