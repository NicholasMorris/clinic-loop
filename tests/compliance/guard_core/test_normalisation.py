"""Test text normalisation for guard pattern matching.

AC2: Normalisation runs before matching. For each blocked phrase written with
zero-width joiners, Cyrillic homoglyphs, fullwidth forms or HTML entities,
check() returns rule_ids equal to those of its plain-ASCII form.
"""

from clinicloop.compliance.guard import check
from clinicloop.compliance.rulesets import load_ruleset


def test_obfuscated_variants_yield_same_rule_ids() -> None:
    """Test that obfuscated variants match same rules as plain forms."""
    ruleset = load_ruleset("au")

    # Test cases: (plain_text, obfuscated_variants, expected_rule_ids)
    test_cases = [
        # HTML entities and zero-width chars
        (
            "veltrazine",
            [
                "&#86;eltrazine",  # HTML entity for V
                "veltr&#97;zine",  # HTML entity for 'a'
                "v​eltrazine",  # Zero-width space
            ],
            ("AU-G-PRODUCT",),
        ),
        # Cyrillic homoglyphs
        (
            "veltrazine",
            [
                "veлtrazine",  # е (Cyrillic e) instead of e
                "vеltrazine",  # е (Cyrillic e)
                "veltrazиne",  # и (Cyrillic i) instead of i
            ],
            ("AU-G-PRODUCT",),
        ),
        # Fullwidth forms
        (
            "veltrazine",
            [
                "ｖｅｌｔｒａｚｉｎｅ",  # Fullwidth
            ],
            ("AU-G-PRODUCT",),
        ),
        # Dose with zero-width separator
        (
            "20 mg",
            [
                "20​mg",  # Zero-width space between number and unit
                "20‌ mg",  # Zero-width non-joiner
            ],
            ("AU-G-DOSE",),
        ),
        # Leet speak
        (
            "veltrazine",
            [
                "veltr4zine",  # 4 -> a
                "v3ltraz1n3",  # 3 -> e, 1 -> i, 3 -> e
            ],
            ("AU-G-PRODUCT",),
        ),
        # Separated letters
        (
            "veltrazine",
            [
                "v e l t r a z i n e",  # Space-separated
                "v.e.l.t.r.a.z.i.n.e",  # Dot-separated
            ],
            ("AU-G-PRODUCT",),
        ),
    ]

    for plain_text, obfuscated_variants, expected_rule_ids in test_cases:
        # Create threads with plain text
        plain_thread = [
            {"role": "patient", "text": "Help me"},
            {"role": "assistant", "text": plain_text},
        ]

        # Check plain text
        plain_verdict = check(plain_thread, "au", ruleset)
        plain_rule_ids = set(plain_verdict.rule_ids)

        # For each obfuscated variant, check it matches plain rule ids
        for obfuscated in obfuscated_variants:
            obfuscated_thread = [
                {"role": "patient", "text": "Help me"},
                {"role": "assistant", "text": obfuscated},
            ]

            obf_verdict = check(obfuscated_thread, "au", ruleset)
            obf_rule_ids = set(obf_verdict.rule_ids)

            assert obf_rule_ids == plain_rule_ids, (
                f"Obfuscated '{obfuscated}' yielded {obf_rule_ids}, "
                f"but plain '{plain_text}' yielded {plain_rule_ids}"
            )
