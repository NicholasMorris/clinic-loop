# Escalation Detection

## Overview

The escalation detector identifies adverse events, suspected medication misuse, mental-health distress, pregnancy-related queries, and requests for clinical advice. These categories never reach the draft stage; they route immediately to a clinician queue with a target response time.

## Escalation Categories

The detector recognizes five categories that count toward escalation recall:

### 1. Adverse Event
Patient reports of serious physical reactions to medications:
- Allergic reactions, hives, swelling
- Difficulty breathing, chest pain, palpitations
- Overdose, fainting, seizures
- Blurred vision, nausea, vomiting

**Queue:** `clinical_urgent` (target: 15 minutes)

### 2. Distress
Mental-health crisis indicators:
- Suicidal ideation or intent
- Self-harm thoughts or actions
- Hopelessness, feeling the situation is hopeless
- Wanting to end one's life

**Queue:** `clinical_urgent` (target: 15 minutes)

### 3. Pregnancy
Pregnancy-related questions and concerns:
- Confirmed or suspected pregnancy
- Breastfeeding medication safety
- Attempting to conceive or fertility concerns

**Queue:** `prescriber_review` (target: 60 minutes)

### 4. Suspected Misuse
Signs of problematic medication use patterns:
- Taking extra or double doses
- Medication ran out early or was lost
- Sharing medication with others
- Using someone else's prescription

**Queue:** `integrity_review` (target: 60 minutes)

### 5. Clinical Advice
Requests for clinical guidance that only a prescriber can answer:
- Should I take, stop, start, or increase a dose?
- Is this medication safe to combine with another?
- What dose or amount should I take?
- Which medicine is best for my condition?

**Queue:** `prescriber_review` (target: 240 minutes)

## Detection Mechanism

### Rules
Deterministic pattern matching over normalized patient text. Patterns are compiled with case-insensitive matching against text that has been:
- HTML entity decoded
- NFKC normalized
- Cleaned of zero-width characters
- Confusables (Cyrillic/Greek) converted to Latin equivalents
- Lowercased

### Classifier (Optional)
An optional classifier (LLM-based or other) can fire independently. The detector returns the union of rule and classifier findings.

### Priority
When multiple categories are detected, priority determines the result category:
1. Distress (highest priority)
2. Adverse Event
3. Pregnancy
4. Suspected Misuse
5. Clinical Advice (lowest priority)

### Failure Mode: `detector_error`
If the classifier raises an exception or times out (configurable, default 5 seconds), the detector escalates with category `detector_error`. This is a fail-closed safety measure: timeouts or crashes escalate rather than allow a reply to draft.

**Note:** `detector_error` is excluded from the escalation recall metric, as it signals an outage, not a true clinical case.

## Result Fields

Each `EscalationResult` includes:

- **category:** One of `{adverse_event, distress, pregnancy, suspected_misuse, clinical_advice, detector_error, none}`
- **evidence:** List of `EvidenceSpan` objects showing which patterns matched, or classifier findings, or errors
- **queue:** Name of the clinician queue (or None if `category == 'none'`)
- **target_response_minutes:** Integer response time in minutes (or None if `category == 'none'`)
- **clear:** An `EscalationClear` token if and only if `category == 'none'`
- **thread_sha256:** SHA-256 hash of the thread for token validation

## EscalationClear Contract

The `EscalationClear` token is a cryptographic binding between a thread and permission to draft:

- **Minted only by the detector** when a thread returns `category == 'none'`
- **Cannot be constructed directly;** attempted direct construction raises `EscalationClearForbidden`
- **Bound to thread content:** carries SHA-256 of the thread; a token from thread A cannot be used for thread B
- **Required for drafting:** any draft entry point that does not receive a matching token raises `EscalationRequired`

This design prevents accidental re-use of a draft decision across thread states or between different patients.

## Reachability Guarantee

A helper function (`paths_from_escalation_to_draft`) validates that a compiled LangGraph does not contain any path from an escalation decision node to a draft node, except through an explicit "clear" conditional edge. This catches:

- Unconditional edges directly to draft
- Paths through other nodes that reach draft
- Edges from the escalation handler that skip the clear check

The reachability test is checked at graph startup, so the guarantee is structural, not runtime-enforced.

## Fixture and Testing

The detector is validated against a development-set fixture of 60+ synthetic threads:
- At least 10 cases per escalation category
- At least 12 benign cases (near-misses like "I have a question about my order")
- Cases with obfuscation (character substitution, zero-width characters) in at least 3 categories

**Important:** This fixture is a unit-level development set for validation, not the production escalation recall metric. The reported metric comes from a separate golden set in M2-6a.

## Configuration

Escalation routing (queue names and target response times) is read from the jurisdiction ruleset's `escalation_routing` block. The AU ruleset currently specifies:

| Category | Queue | Target Response |
|----------|-------|-----------------|
| adverse_event | clinical_urgent | 15 min |
| distress | clinical_urgent | 15 min |
| pregnancy | prescriber_review | 60 min |
| suspected_misuse | integrity_review | 60 min |
| clinical_advice | prescriber_review | 240 min |

The detector validates that all five categories are present in the loaded ruleset; if any are missing, it raises `RulesetValidationError` rather than substituting a default.
