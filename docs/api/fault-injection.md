# Fault Injection

The mock API includes a fault injection layer that allows deterministic, reproducible injection of failures for testing agent resilience and error handling. Faults are disabled by default.

## Overview

Fault injection enables testing of scenarios where the API experiences:

- **Latency**: Added delays to requests
- **Server errors**: HTTP 503 responses indicating temporary unavailability
- **Rate limiting**: HTTP 429 responses when request limits are exceeded

Each fault is deterministic and reproducible from a seed, ensuring consistent test behavior across runs.

## Profile Format

A fault profile is a JSON or Python dictionary that specifies fault rules per route:

```python
from clinicloop.api.faults.profile import (
    FaultProfile,
    LatencyRule,
    ServerErrorRule,
    RateLimitRule,
    RouteFaultRules,
)

profile = FaultProfile(
    seed=42,  # Reproducibility seed
    routes={
        "GET /orders": RouteFaultRules(
            latency=LatencyRule(probability=0.1, latency_ms=500),
            server_error=ServerErrorRule(probability=0.05, status=503),
            rate_limit=RateLimitRule(
                probability=1.0,
                requests_per_window=10,
                window_seconds=60,
            ),
        ),
        "POST /messages": RouteFaultRules(
            server_error=ServerErrorRule(probability=0.02, status=503),
        ),
    },
)
```

## Fault Kinds

### Latency (`latency_ms`)

Injects artificial delay into responses. The delay is applied via an injectable sleep function.

**Profile options:**
- `probability` (0.0–1.0): Chance a request experiences latency
- `latency_ms`: Delay in milliseconds

**Response:** Status 200 with normal body, plus recorded delay

**Fault log fields:**
```json
{
  "ordinal": 5,
  "route": "GET /orders",
  "fault_kind": "latency",
  "requested_delay_ms": 500
}
```

### Server Error (`server_error`)

Injects HTTP 503 Service Unavailable responses. The demo profile returns 503 by default.

**Profile options:**
- `probability` (0.0–1.0): Chance a request returns an error
- `status`: HTTP status code (default: 503)

**Response:**
- Status: Configured (default 503)
- Body: `{"fault_kind": "server_error"}`

**Fault log fields:**
```json
{
  "ordinal": 3,
  "route": "GET /orders",
  "fault_kind": "server_error"
}
```

### Rate Limiting (`rate_limit`)

Enforces a per-route request limit within a time window. Returns HTTP 429 Too Many Requests with a `Retry-After` header.

**Profile options:**
- `probability` (0.0–1.0): Chance the limit is enforced (usually 1.0)
- `requests_per_window`: Maximum requests allowed in the window
- `window_seconds`: Duration of the rate-limit window

**Response:**
- Status: 429 Too Many Requests
- Header: `Retry-After: <seconds>`
- Body: `{"fault_kind": "rate_limit"}`

**Fault log fields:**
```json
{
  "ordinal": 4,
  "route": "GET /orders",
  "fault_kind": "rate_limit",
  "retry_after_seconds": 60
}
```

## Injectable Sleep Function

Latency is applied through a callable `sleep_fn` parameter. This allows tests to record requested delays without actually waiting.

```python
# In production, uses time.sleep (real delay)
middleware = attach_fault_middleware(app, profile)


# In tests, inject a mock sleep function
class RecordingSleeep:
    def __init__(self):
        self.delays = []

    def __call__(self, delay_seconds):
        self.delays.append(delay_seconds)


sleep_recorder = RecordingSleeep()
middleware = attach_fault_middleware(app, profile, sleep_recorder)

# Requests are "delayed" without waiting
response = client.get("/orders")  # Executes instantly, delay recorded
assert sleep_recorder.delays == [0.5, 0.5, ...]
```

This design allows:
- **Fast tests**: No real sleeping required
- **Deterministic timing**: Delays are recorded and verifiable
- **Production realism**: Real deployments use time.sleep

## Reproducibility and Seeding

All fault injection decisions are drawn from a seeded `numpy.random.Generator` initialized with the profile's `seed`. The same seed and request sequence produces identical fault sequences.

```python
# Same seed, same sequence
profile1 = FaultProfile(seed=7, routes=...)
profile2 = FaultProfile(seed=7, routes=...)

# Run 1 with seed=7
response = client.get("/orders")  # Faults: latency, no error
response = client.get("/orders")  # Faults: no latency, error

# Run 2 with seed=7
response = client.get("/orders")  # Faults: latency, no error (identical!)
response = client.get("/orders")  # Faults: no latency, error (identical!)

# Different seed
profile3 = FaultProfile(seed=9, routes=...)  # Different sequence
```

This reproducibility is essential for:
- Replaying failure scenarios consistently
- Debugging agent behavior under specific fault patterns
- Regression testing

## Fault Log

Every injected fault is recorded in the middleware's fault log:

```python
middleware = attach_fault_middleware(app, profile)
client = TestClient(app)

# Make requests...
response = client.get("/orders")

# Access the log
log = middleware.get_fault_log()
# [
#   {"ordinal": 1, "route": "GET /orders", "fault_kind": "latency", "requested_delay_ms": 500},
#   {"ordinal": 3, "route": "GET /orders", "fault_kind": "server_error"},
#   ...
# ]
```

**Fault log fields:**
- `ordinal`: Request sequence number (starts at 1)
- `route`: Route pattern (e.g., "GET /orders")
- `fault_kind`: One of "latency", "server_error", "rate_limit"
- Additional fields per fault kind (e.g., `requested_delay_ms`, `retry_after_seconds`)

## Enabling Fault Injection

By default, faults are **disabled** (no profile configured). To enable them:

```python
from clinicloop.api.app import create_app
from clinicloop.api.faults.profile import FaultProfile, RouteFaultRules, ServerErrorRule
from clinicloop.api.faults.middleware import attach_fault_middleware

# Create app
app = create_app(snapshot_path="world.json")

# Define fault profile
profile = FaultProfile(
    seed=42,
    routes={
        "GET /orders": RouteFaultRules(server_error=ServerErrorRule(probability=0.1, status=503)),
    },
)

# Attach middleware
middleware = attach_fault_middleware(app, profile)

# Use app with faults enabled
client = TestClient(app)
response = client.get("/orders")  # May return 503
```

## Profile Validation

Routes specified in the fault profile must exist in the app. Unknown routes raise `UnknownFaultRoute` at profile load time:

```python
from clinicloop.api.faults.profile import load_profile, UnknownFaultRoute

app_routes = {"GET /orders", "GET /patients"}

profile_data = {
    "seed": 42,
    "routes": {
        "GET /nonexistent": {"server_error": {...}},  # Invalid!
    },
}

try:
    profile = load_profile(profile_data, app_routes)
except UnknownFaultRoute as e:
    print(f"Error: {e}")  # "Unknown route in fault profile: GET /nonexistent"
```

## Demo Configuration

The default demo profile (if used) configures:

- **Server error**: Returns HTTP 503 for transient failures
- **Rate limit**: Returns HTTP 429 with Retry-After header
- **Latency**: Recorded via the injectable sleep function

This allows agents to demonstrate:
- Retry logic and exponential backoff
- Handling of rate-limit headers
- Latency awareness (using recorded delays)
