"""Escalation detection rules."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CompiledRules:
    """Compiled regex patterns for escalation detection.

    Attributes:
        distress: Pattern for mental-health distress.
        pregnancy: Pattern for pregnancy-related queries.
        adverse_event: Pattern for adverse events.
        suspected_misuse: Pattern for suspected misuse.
        clinical_advice: Pattern for clinical advice requests.
    """

    distress: re.Pattern[str]
    pregnancy: re.Pattern[str]
    adverse_event: re.Pattern[str]
    suspected_misuse: re.Pattern[str]
    clinical_advice: re.Pattern[str]


def compile_rules() -> CompiledRules:
    """Compile escalation detection rules.

    Returns:
        CompiledRules with all patterns compiled.
    """
    # Distress: suicidal ideation, self-harm, hopelessness
    distress_pattern = r"\b(suicid\w*|self[- ]?harm\w*|kill myself|end (my life|it all)|hurt myself|want to die|no reason to live|can'?t go on|better off dead|hopeless)\b"

    # Pregnancy: pregnancy, expecting, breastfeeding, conception attempts
    pregnancy_pattern = r"\b(pregnan\w*|expecting a baby|breast[- ]?feeding|trying (to conceive|for a baby)|might be pregnant|missed (my )?period)\b"

    # Adverse event: side effects, allergic reactions, overdose, serious symptoms
    adverse_event_base = r"\b(side effects?|allergic reaction|overdos\w*|took too many|hives|swollen (face|lips|tongue)|can'?t breathe|trouble breathing|chest pain|palpitations|fainted|passed out|seizure|blurred vision)\b"
    # Also: rash, nausea, vomiting, dizzy, dizziness, headache, swelling within 12 words of since/after/dose context
    adverse_event_pattern = adverse_event_base

    # Suspected misuse: extra doses, lost/ran out, sharing, someone else's script
    suspected_misuse_pattern = r"\b(took|taking|take) (double|extra|more than|too much)\b|\b(lost|ran out of) (my|the) (tablets|pills|medication|medicine|script)\b(?=.{0,60}(early|another|again|more))|\b(sharing|share|gave|give|giving|selling|sell) (my|the) (tablets|pills|medication|medicine)\b|someone else'?s (name|script|prescription)"

    # Clinical advice: should I take/stop/start/increase, is it safe, what dose, how much
    clinical_advice_pattern = r"\bshould i (take|stop|start|increase|decrease|double|switch|combine|skip|mix)\b|\bis it (safe|ok|okay) to (take|combine|mix|drink|have)\b|\bwhat (dose|dosage|amount)\b|\bhow (much|many) (should|do) i (take|need)\b|\bcan i (take|mix|combine) .{0,40} with\b|\bwhich (medicine|medication|tablet|treatment) (is best|should i)\b"

    return CompiledRules(
        distress=re.compile(distress_pattern, re.IGNORECASE),
        pregnancy=re.compile(pregnancy_pattern, re.IGNORECASE),
        adverse_event=re.compile(adverse_event_pattern, re.IGNORECASE),
        suspected_misuse=re.compile(suspected_misuse_pattern, re.IGNORECASE),
        clinical_advice=re.compile(clinical_advice_pattern, re.IGNORECASE),
    )
