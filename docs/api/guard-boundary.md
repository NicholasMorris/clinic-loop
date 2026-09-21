# Guard Boundary

The guard boundary is a FastAPI dependency that enforces compliance rules on every outbound message via POST `/messages` before any message is stored. This is the single runtime control that ensures agent-written code cannot bypass the guard by calling the API directly.

## Behaviour

### Allowed Message (HTTP 201)

When a message passes the guard check:

- HTTP status: **201 Created**
- Response body includes `text_sha256`, `jurisdiction`, and `jurisdiction_source`
- Response header `X-Jurisdiction-Source` is set to the jurisdiction source
- Message is stored and returned with all guard verdict fields

Example:

```json
{
  "message_id": "M000001",
  "patient_id": "P001",
  "channel": "chat",
  "body": "Are there any gentle approaches to managing this condition?",
  "synthetic": true,
  "text_sha256": "abc123...",
  "jurisdiction": "au",
  "jurisdiction_source": "request"
}
```

Header: `X-Jurisdiction-Source: request`

### Blocked Message (HTTP 422)

When a message violates one or more rules:

- HTTP status: **422 Unprocessable Entity**
- Response body contains:
  - `code`: `"GuardBlocked"`
  - `rule_ids`: List of violated rule identifiers (e.g., `["AU-G-PRODUCT"]`)
  - `jurisdiction`: The jurisdiction code used for the check
  - `jurisdiction_source`: Either `"request"` or `"default_au"`
  - `ruleset_version`: Version of the ruleset applied
  - `matches`: Array of match objects with `rule_id`, `start`, and `end`
- Message is **not stored**
- Response header `X-Jurisdiction-Source` is set
- **Matched text and lexicon terms are never returned in the response**

Offsets in the `matches` array are **0-indexed character positions in the normalised text**, not the original. This allows callers to identify where violations occur without echoing back the prohibited wording.

Example:

```json
{
  "code": "GuardBlocked",
  "rule_ids": ["AU-G-PRODUCT"],
  "jurisdiction": "au",
  "jurisdiction_source": "default_au",
  "ruleset_version": "1.0.0",
  "matches": [
    {
      "rule_id": "AU-G-PRODUCT",
      "start": 42,
      "end": 51
    }
  ]
}
```

Header: `X-Jurisdiction-Source: default_au`

### Unimplemented Jurisdiction (HTTP 501)

When an explicit jurisdiction is specified that is not yet implemented:

- HTTP status: **501 Not Implemented**
- Response body contains:
  - `code`: `"RulesetNotImplemented"`
  - `jurisdiction`: The requested jurisdiction code (e.g., `"uk"`, `"nz"`)
  - `jurisdiction_source`: `"request"` (since the caller explicitly specified it)
- Response header `X-Jurisdiction-Source` is set

This is the chosen mapping of M0-11 seam error. Explicit `--jurisdiction uk` or `--jurisdiction nz` returns 501; only an unset default falls back to AU strict rules with a banner.

Example:

```json
{
  "code": "RulesetNotImplemented",
  "jurisdiction": "uk",
  "jurisdiction_source": "request"
}
```

Header: `X-Jurisdiction-Source: request`

### Unknown Jurisdiction (HTTP 400)

When an unknown jurisdiction code is provided:

- HTTP status: **400 Bad Request**
- Response body contains:
  - `code`: `"UnknownJurisdiction"`
  - `jurisdiction`: The requested jurisdiction code
  - `jurisdiction_source`: `"request"`
- Response header `X-Jurisdiction-Source` is set

## Jurisdiction Handling

The guard reads jurisdiction from the request:

- **Explicit jurisdiction**: If `jurisdiction` is set in the `MessageCreate` payload, it is validated and used. Source is `"request"`.
- **Unset jurisdiction**: If `jurisdiction` is `null` or omitted, AU rules are applied as a silent default. Source is `"default_au"` and included in the response to signal the fallback to the caller.
- **Unknown jurisdiction**: If jurisdiction is not one of `au`, `uk`, or `nz`, returns HTTP 400.

## Scope

The guard boundary checks only the message body (`text`), not patient identifiers, order IDs, or other request metadata. This ensures the guard enforces compliance rules on agent output without over-scoping to request context.

The boundary runs for every caller, including internal ones via the dependency injection mechanism in FastAPI. No HTTP caller can bypass the guard by posting directly to `/messages`.

## Response Header

The response header `X-Jurisdiction-Source` (exported as `JURISDICTION_SOURCE_HEADER` from `clinicloop.api.guard_boundary`) is set on all responses (201, 422, 501, 400) to communicate whether the jurisdiction was explicit or defaulted:

- `X-Jurisdiction-Source: request` — caller specified the jurisdiction
- `X-Jurisdiction-Source: default_au` — unset jurisdiction fell back to AU
