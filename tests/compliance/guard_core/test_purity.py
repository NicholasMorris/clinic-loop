"""Test that check() is pure: deterministic and performs no IO.

AC4: check() is pure: two calls with the same thread, jurisdiction and
Ruleset object return equal GuardVerdict values, a monkeypatched
builtins.open records zero calls during the check, and pytest-socket
records no connection attempt.
"""

import builtins

from clinicloop.compliance.guard import check
from clinicloop.compliance.rulesets import load_ruleset


def test_check_is_deterministic_and_performs_no_io(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Test that check() is deterministic and performs no IO."""
    ruleset = load_ruleset("au")

    thread = [
        {"role": "patient", "text": "I have a question"},
        {"role": "assistant", "text": "I can help. Take veltrazine 20 mg daily."},
    ]

    # Call check twice
    verdict1 = check(thread, "au", ruleset)
    verdict2 = check(thread, "au", ruleset)

    # Verdicts must be equal (deterministic)
    assert verdict1 == verdict2, "check() is not deterministic"

    # Monkeypatch builtins.open to count calls
    open_call_count = 0
    original_open = builtins.open

    def counting_open(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal open_call_count
        open_call_count += 1
        return original_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", counting_open)

    # Call check with patched open
    verdict3 = check(thread, "au", ruleset)

    assert open_call_count == 0, f"check() called open() {open_call_count} times"
    assert verdict3 == verdict1, "check() result changed after monkeypatch"
