# SimClinic Dashboard

## Overview

The SimClinic Dashboard is a Streamlit application that visualizes metrics from simulation runs. It shows four key metrics: throughput, median wait time, SLA breaches, and cost per order. The dashboard has two data paths: first paint reads a pre-computed snapshot, while toggling an agent on or off re-runs the engine in-process at the same seed.

## Quick Start

### Generate a snapshot

First, generate a default run snapshot:

```bash
make sim-snapshot
```

This writes a snapshot file to `var/snapshots/run-20260921.json` with all three agents enabled.

### Launch the dashboard

Then, launch the Streamlit dashboard:

```bash
make dashboard
```

This starts the Streamlit server on `http://localhost:8501`.

## Metrics

The dashboard displays four metric panels:

- **Throughput**: Number of orders completed (items that finished pharmacy fulfilment).
- **Median wait**: The longest median wait time across all queues, in minutes. Hovering shows which queue is slowest.
- **SLA breaches**: Total count of orders that exceeded SLA targets.
- **Cost per order**: Average cost to complete an order, based on staffing rates.

## Toggles

Three toggle widgets let you enable or disable each agent:

- **Triage agent**: Handles intake review and escalation.
- **Integrity signals agent**: Flags applications for clinical review.
- **Consult documentation agent**: Processes consult notes.

When you toggle an agent off, the step reverts to the human worker pool, and you see queue metrics worsen (longer wait times, higher queue depth, more SLA breaches). This demonstrates that the agents improve throughput.

## Data Paths

### First Paint (Snapshot Read)

When you first load the dashboard, it reads the snapshot file at `var/snapshots/run-20260921.json`:

- If the file exists, the dashboard renders the saved metrics and queues.
- If the file does not exist, the dashboard displays a message instructing you to run `make sim-snapshot`.

The queue table shows queue name, median wait time (in minutes), and max queue depth. Max queue depth is `null` on first paint since the snapshot file does not record it.

### Toggle Interaction (In-Process Re-run)

When you change a toggle, the dashboard:

1. Re-runs the simulation engine at the same seed (20260921) with the current toggle values.
2. Computes a new MetricSnapshot from the run.
3. Records max queue depth for each queue during the run.
4. Renders the updated metrics and queues without writing or reading any file.

This re-run is deterministic: the same seed always produces the same metrics for the same toggle state.

## SLA Breach Detail

Below the metrics, a table lists each SLA breach rule and the inventory item it cites. Each row shows:

- **rule_id**: The SLA rule identifier (e.g., `termination_cutoff`).
- **inventory_id**: The inventory item cited by the rule. Every ID is a member of `KNOWN_INVENTORY_IDS`.
- **count**: Number of breaches for this rule.

## Agent Implementation Status

**All numbers are simulated.** The world is synthetic, and service times and hourly staff rates are assumed starter values (`assumed = true` in `staffing.toml`), not measured from any clinic. Cost per order is busy staff time divided by completed orders, so treat it as illustrative. The support inbox service time was set so that switching triage off visibly backs up the inbox.

The three agents shown in the toggles are currently served by the shipped `FakeAgentPort`, which completes requests in 10% of the human service time. This is a stand-in until the real adapters land:

- **M2-7**: Triage agent adapter
- **M3-3**: Integrity signals adapter
- **M5-8**: Consult documentation adapter

When the real adapters are deployed, the dashboard continues to work unchanged; the seam between the FakeAgentPort and real agents is transparent to the app.

## Offline Guarantee

The dashboard makes no network calls. It imports no `requests`, `httpx`, or `urllib.request` modules. All data is computed locally or read from the snapshot file.

## Related Pages

- Review console: The separate review console (M1-9) shows pending human decisions for approvals and flag reviews. It is hosted as its own Streamlit page module under `hitl/console/` and is not part of the metrics dashboard.
