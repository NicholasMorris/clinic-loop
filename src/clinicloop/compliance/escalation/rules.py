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
    distress_pattern = (
        r"\b(suicid\w*|self[- ]?harm\w*|kill myself|end(?:ing)? (my life|it all)|"
        r"hurt myself|want to die|no reason to live|can'?t go on|"
        r"better off dead|hopeless)\b"
    )

    # Pregnancy: pregnancy, expecting, breastfeeding, conception attempts
    pregnancy_pattern = (
        r"\b(pregnan\w*|expecting a baby|breast[- ]?feeding|"
        r"trying (to conceive|for a baby)|might be pregnant|"
        r"missed (my )?period)\b"
    )

    # Adverse event: serious symptoms (always) + context-dependent ones
    adverse_event_always = (
        r"\b(side effects?|allergic reactions?|overdos\w*|took too many|hives|"
        r"swollen (face|lips|tongue)|swell(?:ed|ing) up|can'?t breathe|trouble breathing|"
        r"chest pain|palpitations|fainted|passed out|seizure|blurred vision)\b"
    )
    # Context: (rash|nausea|vomiting|dizzy|headache) near medicine context
    adverse_event_context = (
        r"\b(rash|nausea|vomiting|dizzy|dizziness|headache|swelling)\b"
        r"(?=.{0,100}(since|after|my (dose|tablets|pills|medicine|medication|"
        r"treatment)))"
    )
    adverse_event_pattern = f"(?:{adverse_event_always}|{adverse_event_context})"

    # Suspected misuse: extra doses, lost/ran out, sharing, someone else's
    suspected_misuse_pattern = (
        r"\b(took|taking|take) (double|extra|more than|too much)\b|"
        r"\b(lost|ran out of) (my|the) "
        r"(tablets|pills|medication|medicine|script)\b"
        r"(?=.{0,60}(early|another|again|more))|"
        r"\b(sharing|share|gave|give|giving|selling|sell)\b"
        r".{0,30}\b(tablets|pills|medication|medicine)\b|"
        r"\basked for\b.{0,30}\b(tablets|pills|medication|medicine)\b|"
        r"someone else'?s (name|script|prescription)"
    )

    # Clinical advice: should I, is it safe, what/which, how much, can I
    clinical_advice_pattern = (
        r"\bshould i (take|stop|start|increase|decrease|double|"
        r"switch|combine|skip|mix)\b|"
        r"\bis it (safe|ok|okay) to (take|combine|mix|drink|have|skip)\b|"
        r"\bwhat (dose|dosage|amount)\b|"
        r"\bhow (much|many).{0,40}\b(take|need)\b|"
        r"\bcan i (take|mix|combine).{0,40} with\b|"
        r"\bwhich (medicine|medication|tablet|treatment).{0,20}"
        r"(best|should)\b|"
        r"\bcan i (take|give|have|drink|start|stop)\b"
    )

    return CompiledRules(
        distress=re.compile(distress_pattern, re.IGNORECASE),
        pregnancy=re.compile(pregnancy_pattern, re.IGNORECASE),
        adverse_event=re.compile(adverse_event_pattern, re.IGNORECASE),
        suspected_misuse=re.compile(suspected_misuse_pattern, re.IGNORECASE),
        clinical_advice=re.compile(clinical_advice_pattern, re.IGNORECASE),
    )
