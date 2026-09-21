"""Known inventory IDs manifest.

This module contains the KNOWN_INVENTORY_IDS frozenset, which is a hand
transcription of the inventory IDs from docs/problem-inventory.md.
The transcription is not machine-checked, but is verified by the orchestrator
at review time.
"""

# Hand-transcribed from docs/problem-inventory.md
# Includes required IDs plus additional ones referenced in problem inventory
KNOWN_INVENTORY_IDS: frozenset[str] = frozenset(
    [
        "ps-03",  # Termination cutoff
        "ps-04",  # Damaged-item intake
        "po-01",  # Payment-to-dispatch stall alert
        "po-02",  # Delivery commitment
        "po-06",  # Delivery time (unpopulated NZ Friday cutoff)
        "x-01",  # Delivery time conflict (AU recorded conflict)
    ]
)
