# Guard: compliance-rule matching for outbound messages

The guard is a pure, deterministic compliance checker that runs on every outbound patient-facing message before it can be sent. It detects violations of jurisdiction-specific rule sets (currently AU) and records which rule was violated, enabling downstream escalation and human review.

## Design principles

- **Pure function**: `check()` performs no file, network or clock access and never mutates its inputs.
- **Deterministic**: same thread, jurisdiction and ruleset always produce identical verdicts.
- **Immutable config**: the ruleset is loaded once by the caller and passed to check; versioning is explicit so stale verdicts are detectable.
- **Explicit sink**: only `OutboundPort.send()` calls the transport; every other path is blocked by exception.
- **Optional second opinion**: an LLM reviewer can add blocks on top of deterministic rules, but never remove a block or allow a case the rules forbid.

## Rule categories

The AU ruleset contains five rules:

- **AU-G-PRODUCT**: Names a prescription-only product (brand name like *veltrazine* or generic name like *veltrazamide*) in assistant text.
- **AU-G-EUPHEMISM**: Uses a euphemism for a prescription-only treatment (e.g., "the usual medicine", "your special script", "the strong stuff").
- **AU-G-DOSE**: Specifies a dose: a number (integer or decimal, e.g. 20, 20.5) immediately followed by a unit (mg, mcg, g, ml, iu, tablet, capsule, pill) with optional single space.
- **AU-G-CONDITION**: Makes a condition claim: asserts the patient has a condition (depression, anxiety, insomnia, hypertension, diabetes, asthma, migraine, arthritis, eczema, acne) using language like "you have", "you're suffering from", "you're diagnosed with", or asserts a product cures or treats one using language like "treats", "cures", "will fix", "is guaranteed to cure".
- **AU-G-ADVICE**: Provides clinical advice: phrases like "you should take", "it is safe to", "increase your", "skip your", "double up".

Each rule in au.yaml carries a neutral citation block naming the applicable instrument (law or code), a generic provision description, the date it was last checked, and a status (unverified for all, since cited provisions have not yet been audited against instrument text).

## Normalisation chain

Before pattern matching, text is normalised to defence against common obfuscation:

1. **HTML entity decode** (`&#86;` → V, `&zwj;` → zero-width joiner, etc).
2. **NFKC normalization** (fullwidth → ASCII).
3. **Strip zero-width and format characters** (U+200B, U+200C, U+200D, U+2060, U+FEFF, soft hyphen U+00AD).
4. **Fold confusables** (Cyrillic и, а, е, о, р, с, х, у, ѕ, і, ј, ԁ, л and Greek ν, ο, ι, Α, Β, Ε, Ο, Τ, Ι, Ν, Ζ map to Latin equivalents).
5. **Lowercase**.
6. **Leet substitution inside alphabetic tokens** (4→a, 3→e, 1→i, 0→o, 5→s, 7→t, @→a, $→s; only when the leet char is part of a token starting with a letter, so "veltr4zine" → "veltrazine" but "20 mg" stays).
7. **Collapse letter-separator obfuscation** (runs of 5+ single letters separated by space, dot, hyphen, underscore or asterisk join into a word, so "v.e.l.t.r.a.z.i.n.e" → "veltrazine").

Pattern matching then applies to the normalised text.

## Thread model

A thread is a list of messages: `[{"role": "patient" | "assistant", "text": str}, ...]`. The guard checks only **all assistant messages joined with a single space**; patient messages are never matched, so a patient who names a product or injects instructions has no effect.

## check() contract

```python
def check(thread, jurisdiction, ruleset, second_opinion=None) -> GuardVerdict
```

**Inputs:**
- `thread`: list of dicts or objects with `.role` and `.text` attributes.
- `jurisdiction`: jurisdiction code (e.g., "au").
- `ruleset`: a pre-loaded `Ruleset` object with jurisdiction, version, rules, lexicon, escalation_routing and second_opinion_enabled flag.
- `second_opinion`: optional callable returning a list of extra rule ids to add to the verdict (only called if `ruleset.second_opinion_enabled` is True).

**Outputs:**
- `GuardVerdict`: immutable frozen dataclass with:
  - `allowed`: True if no rules matched, False if any rule matched or second opinion added ids.
  - `rule_ids`: tuple of sorted rule ids that matched (empty if allowed=True).
  - `jurisdiction`: the jurisdiction argument (for audit trail).
  - `ruleset_version`: the version string from the ruleset.
  - `text_sha256`: SHA256 hex digest of the exact joined assistant text (UTF-8 bytes), before normalisation.

**Exceptions:**
- `ValueError`: if thread has no assistant messages.
- `JurisdictionMismatch`: if `ruleset.jurisdiction != jurisdiction`.

**Guarantees:**
- No file, network or clock access.
- No mutation of inputs.
- Deterministic: same inputs always produce identical verdict.

## GuardVerdict and OutboundPort

`GuardVerdict` is the sealed agreement between check and send: it carries the rule ids and a SHA256 of the exact text that was checked. `OutboundPort.send(text, verdict)` validates the agreement:

```python
class OutboundPort:
    def __init__(self, transport: Callable[[str], None], ruleset: Ruleset):
        self.transport = transport
        self.ruleset = ruleset
    
    def send(self, text: str, verdict: GuardVerdict) -> None:
        """Send text only if verdict is valid, allowed and current."""
```

`send()` raises an exception in this order:

1. **GuardMismatch**: if `sha256(text) != verdict.text_sha256`. The text does not match the verdict (e.g., edited after check, or checked against different text).
2. **GuardBlocked**: if `verdict.allowed` is False. The draft violates one or more rules; rule ids are in the exception message.
3. **StaleRuleset**: if `verdict.ruleset_version != self.ruleset.version`. The loaded ruleset version differs from the verdict (e.g., au.yaml was updated).

If all three checks pass, `transport(text)` is called exactly once. This is the only code path that calls a transport.

## Second opinion (LLM reviewer)

By default (`second_opinion_enabled: false`), check() runs only deterministic rule matching. If a caller enables second opinion in the ruleset and provides a reviewer callable, the reviewer is invoked only after deterministic matching completes:

```python
if ruleset.second_opinion_enabled and second_opinion is not None:
    extra_rule_ids = second_opinion(thread)  # Returns list[str] of extra ids
    rule_ids_set.update(extra_rule_ids)
    allowed = len(rule_ids_set) == 0
```

The reviewer **can only add rule ids, never remove them**. A deterministic block stays blocked. A clean thread (no deterministic violations) becomes blocked only if the reviewer returns ids. This design prevents any reviewer (malicious or misconfigured) from bypassing the deterministic guard.

The AU ruleset ships with `second_opinion_enabled: false`. Jurisdictions that want LLM review enable it in their own au.yaml.

## Escalation routing and assumed response times

The ruleset includes an `escalation_routing` table mapping rule categories to queues and assumed response times:

| Category | Queue | Minutes | Notes |
|----------|-------|---------|-------|
| adverse_event | clinical_urgent | 15 | Assumed starter value for orchestrator config |
| suspected_misuse | integrity_review | 60 | Assumed starter value |
| distress | clinical_urgent | 15 | Assumed starter value |
| pregnancy | prescriber_review | 60 | Assumed starter value |
| clinical_advice | prescriber_review | 240 | Assumed starter value |

These are the **assumed default values only**, carrying the orchestrator's conservative starter assumptions about how long each escalation category can wait before human review. They are not derived from law, regulation or measurement; they are updated by editing au.yaml and redeploying. The M2-3 reachability checker reads this table without editing it.

## Citation fields

Each rule in au.yaml carries:

- `instrument`: the law, code or standard name (e.g., "Therapeutic Goods Act 1989 (Cth)").
- `provision`: a generic, neutral description of the restricted practice (e.g., "Restrictions on advertising prescription-only goods to the public"), not a section number.
- `checked_date`: the date the provision was last reviewed (ISO format, e.g., "2026-09-22").
- `citation_status`: "verified" (provision text audited against instrument) or "unverified" (not yet audited). All AU citations are unverified; verified status is gated and requires a formal citation review process.

## AU-only R5 seam

Requests for UK or NZ rulesets raise `RulesetNotImplemented` at load time (in `load_ruleset()`, owned by M0-11). This is a visible seam: the code path that would load uk.yaml or nz.yaml explicitly fails, making the incomplete support obvious to users and tests.

Checking against a loaded ruleset with a different jurisdiction than the check call raises `JurisdictionMismatch`, preventing accidental jurisdiction mismatch at runtime.

## Honesty

The lexicon (12 product names, 12 euphemisms, 10 conditions) is **synthetic and invented**. No real product names appear. The corpus (116 cases) is hand-written and small; a zero violation rate is **regression protection**, not completeness or production readiness. The guard is **deterministic pattern matching**; a real deployment would extend it with heuristics, review thresholds, and a real LLM second opinion with model-specific guardrails. The citations are **unverified** and the provisions are generic; they are illustrative only and do not replace legal review.
