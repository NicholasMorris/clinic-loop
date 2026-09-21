"""Text normalisation for guard pattern matching."""


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
    raise NotImplementedError("normalise() stub")
