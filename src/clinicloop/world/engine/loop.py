"""Discrete-event simulation engine for SimClinic."""

import hashlib
import heapq
from typing import Any, Literal, NamedTuple

from clinicloop.world.queues import queues
from clinicloop.world.regimes import get_regime
from clinicloop.world.workers import load_staffing


class Event(NamedTuple):
    """A scheduled event in the simulation.

    Attributes:
        timestamp: Simulated time in minutes.
        sequence_number: Insertion order for tie-breaking.
        event_type: Type of event (e.g., "enqueue", "dequeue").
        entity_id: ID of the entity involved in the event.
        queue_name: Name of the queue (if applicable).
    """

    timestamp: int
    sequence_number: int
    event_type: str
    entity_id: str
    queue_name: str | None = None


class Engine:
    """Heap-based discrete-event simulation engine.

    The engine advances a simulated clock only through scheduled events,
    maintaining four named queues and worker pools with service-time distributions.
    """

    def __init__(self, world: Any, regime_key: Literal["au", "nz", "uk"] = "au") -> None:
        """Initialize the engine.

        Args:
            world: The World object with generated entities.
            regime_key: Jurisdiction key ("au", "nz", or "uk").
        """
        self.world = world
        self.regime_key = regime_key
        self.event_heap: list[tuple[int, int, Event]] = []
        self.sequence_counter = 0
        self._queues = queues()
        self._event_log: list[str] = []
        self._regime = get_regime(regime_key)

    def run(self, duration_minutes: int) -> None:
        """Run the simulation for the specified duration.

        Args:
            duration_minutes: Simulated duration in minutes.

        Raises:
            RegimeParameterNotSet: If required regime parameters are missing.
        """
        # Load staffing configuration to validate it exists and has all required parameters
        _staffing = load_staffing()

        # Verify regime parameters exist for the three SLA rules
        # This will raise RegimeParameterNotSet if parameters are missing
        _ = self._regime.termination_cutoff_business_days
        _ = self._regime.damage_report_window_days
        _ = self._regime.dispatch_commitment_business_days

        # Schedule initial events from the world
        self._schedule_initial_events(duration_minutes)

        # Process events until we reach the end of the simulation duration
        while self.event_heap:
            timestamp, seq, event = heapq.heappop(self.event_heap)

            # Stop if we've exceeded the duration
            if timestamp > duration_minutes:
                break

            # Process the event
            self._process_event(event)

            # Log the event
            self._event_log.append(f"{timestamp}:{event.event_type}:{event.entity_id}")

    def _schedule_initial_events(self, duration_minutes: int) -> None:
        """Schedule initial events from the world entities.

        Args:
            duration_minutes: Simulation duration in minutes.
        """
        # Schedule questionnaire submissions as intake queue enqueues
        for questionnaire in self.world.questionnaires:
            if questionnaire.submitted_at_minute <= duration_minutes:
                event = Event(
                    timestamp=questionnaire.submitted_at_minute,
                    sequence_number=self.sequence_counter,
                    event_type="intake_enqueue",
                    entity_id=questionnaire.questionnaire_id,
                    queue_name="intake",
                )
                heapq.heappush(
                    self.event_heap,
                    (event.timestamp, event.sequence_number, event),
                )
                self.sequence_counter += 1

        # Schedule consults as prescriber_review queue enqueues
        for consult in self.world.consults:
            if consult.scheduled_at_minute <= duration_minutes:
                event = Event(
                    timestamp=consult.scheduled_at_minute,
                    sequence_number=self.sequence_counter,
                    event_type="prescriber_review_enqueue",
                    entity_id=consult.consult_id,
                    queue_name="prescriber_review",
                )
                heapq.heappush(
                    self.event_heap,
                    (event.timestamp, event.sequence_number, event),
                )
                self.sequence_counter += 1

        # Schedule orders as pharmacy_fulfilment queue enqueues
        for order in self.world.orders:
            if order.created_at_minute <= duration_minutes:
                event = Event(
                    timestamp=order.created_at_minute,
                    sequence_number=self.sequence_counter,
                    event_type="pharmacy_fulfilment_enqueue",
                    entity_id=order.order_id,
                    queue_name="pharmacy_fulfilment",
                )
                heapq.heappush(
                    self.event_heap,
                    (event.timestamp, event.sequence_number, event),
                )
                self.sequence_counter += 1

        # Schedule messages as support_inbox queue enqueues
        for message in self.world.messages:
            if message.received_at_minute <= duration_minutes:
                event = Event(
                    timestamp=message.received_at_minute,
                    sequence_number=self.sequence_counter,
                    event_type="support_inbox_enqueue",
                    entity_id=message.message_id,
                    queue_name="support_inbox",
                )
                heapq.heappush(
                    self.event_heap,
                    (event.timestamp, event.sequence_number, event),
                )
                self.sequence_counter += 1

    def _process_event(self, event: Event) -> None:
        """Process a single event.

        Args:
            event: The event to process.
        """
        if event.event_type.endswith("_enqueue") and event.queue_name:
            # Enqueue the item
            queue = self._queues[event.queue_name]
            queue.enqueue(event.entity_id, event.timestamp)

    def run_hash(self) -> str:
        """Return a hash representing the run's event log.

        Returns:
            A string hash that uniquely identifies the run's events and outcomes.
        """
        # Create a comprehensive hash from:
        # 1. The event log
        # 2. The final queue states
        hash_input = "\n".join(self._event_log)

        # Add queue final states
        for queue_name, queue in sorted(self._queues.items()):
            queue_state = "|".join(
                f"{item.item_id}:{item.enqueued_at}:{item.dequeued_at}" for item in queue.items
            )
            hash_input += f"\n{queue_name}:{queue_state}"

        # Generate SHA256 hash
        return hashlib.sha256(hash_input.encode()).hexdigest()
