"""Discrete-event simulation engine for SimClinic."""

import hashlib
import heapq
import json
from collections import deque
from dataclasses import dataclass
from typing import Any, Literal, NamedTuple

import numpy as np

from clinicloop.world.ports.registry import PortFailure, PortRegistry
from clinicloop.world.regimes import get_regime
from clinicloop.world.workers import load_staffing


class ItemRecord(NamedTuple):
    """Record of an item's journey through a queue.

    Attributes:
        queue: Name of the queue.
        item_id: Unique identifier for the item.
        enqueued_at: Timestamp when item was enqueued.
        started_at: Timestamp when service started (None if not started).
        finished_at: Timestamp when service finished (None if not finished).
        server: Server ID that processed this item (None if not started).
    """

    queue: str
    item_id: str
    enqueued_at: int
    started_at: int | None
    finished_at: int | None
    server: int | None


@dataclass(frozen=True)
class RunResult:
    """Result of a simulation run.

    Attributes:
        records: Tuple of ItemRecords, sorted by (queue, item_id).
        queue_depth: Dict mapping queue name to tuple of (timestamp, depth) samples.
        duration_minutes: The simulation duration in minutes.
        staffing: Dict mapping queue name to staffing level.
        agent_toggles: Dict mapping agent name to boolean toggle state.
        run_hash: SHA256 hash of the run.
    """

    records: tuple[ItemRecord, ...]
    queue_depth: dict[str, tuple[tuple[int, int], ...]]
    duration_minutes: int
    staffing: dict[str, int]
    agent_toggles: dict[str, bool]
    run_hash: str
    port_failures: tuple[PortFailure, ...] = ()


class Event(NamedTuple):
    """A scheduled event in the simulation.

    Attributes:
        timestamp: Simulated time in minutes.
        sequence_number: Insertion order for tie-breaking.
        event_type: Type of event (e.g., "arrive", "finish").
        queue: Name of the queue (if applicable).
        item_id: ID of the item involved in the event.
        server: Server ID for finish events.
    """

    timestamp: int
    sequence_number: int
    event_type: str
    queue: str
    item_id: str
    server: int | None = None


class Engine:
    """Heap-based discrete-event simulation engine.

    The engine advances a simulated clock only through scheduled events,
    maintaining four named queues and worker pools with service-time distributions.
    Workers operate 24/7. Staff work continuously through the simulation.
    """

    def __init__(
        self,
        world: Any,
        regime_key: Literal["au", "nz", "uk"] = "au",
        staffing_overrides: dict[str, int] | None = None,
        agent_toggles: dict[str, bool] | None = None,
        ports: PortRegistry | None = None,
        on_tick: Any = None,
    ) -> None:
        """Initialize the engine.

        Args:
            world: The World object with generated entities.
            regime_key: Jurisdiction key ("au", "nz", or "uk").
            staffing_overrides: Dict of queue_name -> staffing_level overrides.
            agent_toggles: Dict of agent_name -> bool toggle state.
                If None, defaults to all three agents ON
                (triage, consult_scribe, integrity).
                Unknown agent names raise KeyError.
            ports: Optional PortRegistry. When a port is registered for a
                toggled-on scope, the engine calls it instead of the assumed
                RNG/config shortcut for that scope. Only "triage" is consulted
                today (consult_scribe and integrity still use the fixed extra-
                minutes model). When ports is None, or no port is registered
                for "triage", behaviour is unchanged from before this
                parameter existed. A port that raises RuntimeError falls back
                to the human queue and records a PortFailure.
            on_tick: Optional callable(timestamp: int, available_capacity:
                dict[str, int]) invoked at the same cadence as the queue-depth
                samples (every 60 simulated minutes, plus a final call for any
                sample times after the last event). available_capacity[queue]
                is staffing[queue] - busy[queue]: the number of human worker
                pool slots for that queue free at that instant, regardless of
                which items are merely waiting. This is observational only; it
                never changes engine behaviour, and when on_tick is None
                (the default) nothing about a run changes from before this
                parameter existed.

        Raises:
            ValueError: If any staffing override is < 1.
            KeyError: If a staffing override queue name is unknown,
                or if agent_toggles contains an unknown agent name.
        """
        self.world = world
        self.regime_key = regime_key
        self.staffing_overrides = staffing_overrides or {}
        self._regime = get_regime(regime_key)
        self._last_run_result: RunResult | None = None
        self.ports = ports
        self.port_failures: list[PortFailure] = []
        self.on_tick = on_tick

        # Initialize agent toggles: default all ON
        self.agent_toggles = {"triage": True, "consult_scribe": True, "integrity": True}
        if agent_toggles is not None:
            # Validate all keys are known
            unknown_agents = set(agent_toggles.keys()) - {"triage", "consult_scribe", "integrity"}
            if unknown_agents:
                raise KeyError(f"Unknown agent(s): {unknown_agents}")
            self.agent_toggles.update(agent_toggles)

        self._validate_staffing_overrides()

    def _validate_staffing_overrides(self) -> None:
        """Validate staffing overrides.

        Raises:
            ValueError: If any staffing level < 1.
            KeyError: If a queue name is unknown.
        """
        valid_queues = {"intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"}
        for queue_name, level in self.staffing_overrides.items():
            if queue_name not in valid_queues:
                raise KeyError(f"Unknown queue: {queue_name}")
            if level < 1:
                raise ValueError(f"Staffing level for {queue_name} must be >= 1, got {level}")

    def run(self, duration_minutes: int) -> RunResult:
        """Run the simulation for the specified duration.

        Args:
            duration_minutes: Simulated duration in minutes.

        Returns:
            A RunResult containing records and statistics.

        Raises:
            RegimeParameterNotSet: If required regime parameters are missing.
        """
        # Reset per-run port failure log (an Engine instance may run() more than once).
        self.port_failures = []

        # Load and validate staffing configuration
        staffing_config = load_staffing()

        # Load agent configuration
        from clinicloop.world.workers import load_agents

        agent_config = load_agents()

        # Verify regime parameters exist for the three SLA rules
        _ = self._regime.termination_cutoff_business_days
        _ = self._regime.damage_report_window_days
        _ = self._regime.dispatch_commitment_business_days

        # Initialize state
        queue_names = ["intake", "prescriber_review", "pharmacy_fulfilment", "support_inbox"]
        waiting: dict[str, deque[tuple[str, int]]] = {q: deque() for q in queue_names}
        busy: dict[str, int] = {q: 0 for q in queue_names}
        free_servers: dict[str, set[int]] = {
            q: set(range(100)) for q in queue_names
        }  # Pool of available server IDs
        item_records: dict[tuple[str, str], ItemRecord] = {}
        event_heap: list[tuple[int, int, Event]] = []
        sequence_counter = 0

        # Get staffing levels
        staffing = {}
        for queue in queue_names:
            staffing[queue] = self.staffing_overrides.get(
                queue, staffing_config[queue].staffing_level
            )

        # Create RNGs per queue
        rngs = {
            queue: np.random.default_rng([self.world.seed, i])
            for i, queue in enumerate(queue_names)
        }

        # Create dedicated RNG for triage agent
        triage_rng = np.random.default_rng([self.world.seed, 99])

        # Schedule initial arrivals
        for questionnaire in self.world.questionnaires:
            if questionnaire.submitted_at_minute <= duration_minutes:
                event = Event(
                    timestamp=questionnaire.submitted_at_minute,
                    sequence_number=sequence_counter,
                    event_type="arrive",
                    queue="intake",
                    item_id=questionnaire.questionnaire_id,
                )
                heapq.heappush(event_heap, (event.timestamp, event.sequence_number, event))
                sequence_counter += 1
                # Create record
                key = ("intake", questionnaire.questionnaire_id)
                item_records[key] = ItemRecord(
                    queue="intake",
                    item_id=questionnaire.questionnaire_id,
                    enqueued_at=questionnaire.submitted_at_minute,
                    started_at=None,
                    finished_at=None,
                    server=None,
                )

        for message in self.world.messages:
            if message.received_at_minute <= duration_minutes:
                event = Event(
                    timestamp=message.received_at_minute,
                    sequence_number=sequence_counter,
                    event_type="arrive",
                    queue="support_inbox",
                    item_id=message.message_id,
                )
                heapq.heappush(event_heap, (event.timestamp, event.sequence_number, event))
                sequence_counter += 1
                key = ("support_inbox", message.message_id)
                item_records[key] = ItemRecord(
                    queue="support_inbox",
                    item_id=message.message_id,
                    enqueued_at=message.received_at_minute,
                    started_at=None,
                    finished_at=None,
                    server=None,
                )

        # Track queue depths at regular intervals
        queue_depth_samples: dict[str, list[tuple[int, int]]] = {q: [] for q in queue_names}
        sample_times = list(range(0, duration_minutes + 1, 60))  # Every 60 minutes

        # Main event loop
        next_sample_idx = 0
        while event_heap:
            # Emit queue depth samples before processing events at/after the sample time
            while next_sample_idx < len(sample_times):
                sample_time = sample_times[next_sample_idx]
                if event_heap and event_heap[0][0] > sample_time:
                    # Emit samples
                    for queue in queue_names:
                        depth = len(waiting[queue])
                        queue_depth_samples[queue].append((sample_time, depth))
                    if self.on_tick is not None:
                        self.on_tick(
                            sample_time,
                            {q: staffing[q] - busy[q] for q in queue_names},
                        )
                    next_sample_idx += 1
                else:
                    break

            timestamp, seq, event = heapq.heappop(event_heap)

            # Stop if we've exceeded the duration
            if timestamp > duration_minutes:
                # Emit remaining samples after the loop
                break

            if event.event_type == "arrive":
                queue = event.queue
                item_id = event.item_id

                # Create item record if it doesn't exist (for routed items)
                key = (queue, item_id)
                if key not in item_records:
                    item_records[key] = ItemRecord(
                        queue=queue,
                        item_id=item_id,
                        enqueued_at=timestamp,
                        started_at=None,
                        finished_at=None,
                        server=None,
                    )

                # Check for triage agent on support_inbox
                if queue == "support_inbox" and self.agent_toggles.get("triage", True):
                    triage_port = self.ports.get("triage") if self.ports is not None else None
                    resolved = False
                    service_minutes: float | None = None

                    if triage_port is not None:
                        # A real port is registered: it decides resolution, not the RNG.
                        # A RuntimeError is the port's documented fallback contract (the
                        # triage graph's own approval gate raises it, among other things).
                        try:
                            service_minutes = triage_port.serve(item_id)
                            resolved = True
                        except RuntimeError as exc:
                            self.port_failures.append(
                                PortFailure(
                                    scope="triage",
                                    exception_type=type(exc).__name__,
                                    case_id=item_id,
                                )
                            )
                    else:
                        # No port registered: the assumed RNG/config shortcut, unchanged.
                        u = triage_rng.uniform()
                        if u < agent_config.triage.agent_resolved_share:
                            service_minutes = agent_config.triage.agent_service_minutes
                            resolved = True

                    if resolved and service_minutes is not None:
                        # Agent resolves: create finish event immediately, skip human queue
                        old_record = item_records[key]
                        item_records[key] = ItemRecord(
                            queue=old_record.queue,
                            item_id=old_record.item_id,
                            enqueued_at=old_record.enqueued_at,
                            started_at=timestamp,
                            finished_at=timestamp + int(service_minutes),
                            server=None,
                        )

                        # Schedule finish event
                        finish_event = Event(
                            timestamp=timestamp + int(service_minutes),
                            sequence_number=sequence_counter,
                            event_type="finish",
                            queue=queue,
                            item_id=item_id,
                            server=None,
                        )
                        heapq.heappush(
                            event_heap,
                            (finish_event.timestamp, finish_event.sequence_number, finish_event),
                        )
                        sequence_counter += 1
                        continue  # Skip human queue processing

                # Normal path: add to waiting queue
                waiting[queue].append((item_id, timestamp))

                # Try to start service
                sequence_counter = self._try_start_service(
                    queue,
                    timestamp,
                    waiting,
                    busy,
                    free_servers,
                    item_records,
                    staffing[queue],
                    staffing_config[queue].service_time_family,
                    staffing_config[queue].mean_service_minutes,
                    rngs[queue],
                    event_heap,
                    sequence_counter,
                    duration_minutes,
                    agent_config=agent_config,
                )

            elif event.event_type == "finish":
                queue = event.queue
                item_id = event.item_id
                server_id = event.server

                # Mark as finished
                key = (queue, item_id)
                old_record = item_records[key]
                item_records[key] = ItemRecord(
                    queue=old_record.queue,
                    item_id=old_record.item_id,
                    enqueued_at=old_record.enqueued_at,
                    started_at=old_record.started_at,
                    finished_at=timestamp,
                    server=old_record.server,
                )

                # Free the server. server_id is None for an item resolved by an
                # agent (triage agent shortcut or a registered AgentPort): that
                # item never occupied a human server slot via _try_start_service,
                # so busy[queue] must not be decremented for it either -- doing so
                # unconditionally (a pre-existing bug found while adding on_tick)
                # drove busy[queue] negative over a run, letting more concurrent
                # human service starts through than staffing_level actually allows.
                if server_id is not None:
                    busy[queue] -= 1
                    free_servers[queue].add(server_id)

                # Route to next queue if applicable
                sequence_counter = self._route_item(
                    queue,
                    item_id,
                    timestamp,
                    waiting,
                    event_heap,
                    sequence_counter,
                    duration_minutes,
                )

                # Try to start next item in this queue
                sequence_counter = self._try_start_service(
                    queue,
                    timestamp,
                    waiting,
                    busy,
                    free_servers,
                    item_records,
                    staffing[queue],
                    staffing_config[queue].service_time_family,
                    staffing_config[queue].mean_service_minutes,
                    rngs[queue],
                    event_heap,
                    sequence_counter,
                    duration_minutes,
                    agent_config=agent_config,
                )

        # Emit remaining queue depth samples after the loop
        for sample_time in sample_times[next_sample_idx:]:
            for queue in queue_names:
                depth = len(waiting[queue])
                queue_depth_samples[queue].append((sample_time, depth))
            if self.on_tick is not None:
                self.on_tick(sample_time, {q: staffing[q] - busy[q] for q in queue_names})

        # Convert records to sorted tuple
        records_list = sorted(item_records.values(), key=lambda r: (r.queue, r.item_id))
        records_tuple = tuple(records_list)

        # Convert queue_depth_samples to tuple of tuples
        queue_depth_final = {q: tuple(queue_depth_samples[q]) for q in queue_names}

        # Create run result
        run_hash = self._compute_hash(records_tuple, staffing, self.agent_toggles)
        result = RunResult(
            records=records_tuple,
            queue_depth=queue_depth_final,
            duration_minutes=duration_minutes,
            staffing=staffing,
            agent_toggles=dict(self.agent_toggles),
            run_hash=run_hash,
            port_failures=tuple(self.port_failures),
        )

        self._last_run_result = result
        return result

    def _try_start_service(
        self,
        queue: str,
        current_time: int,
        waiting: dict[str, deque[tuple[str, int]]],
        busy: dict[str, int],
        free_servers: dict[str, set[int]],
        item_records: dict[tuple[str, str], ItemRecord],
        staffing_level: int,
        service_family: str,
        mean_service_minutes: float,
        rng: np.random.Generator,
        event_heap: list[tuple[int, int, Event]],
        sequence_counter: int,
        duration_minutes: int,
        agent_config: Any | None = None,
    ) -> int:
        """Try to start service for waiting items.

        Args:
            queue: Queue name.
            current_time: Current simulated time.
            waiting: Waiting queue dict.
            busy: Busy server count dict.
            free_servers: Free server IDs dict.
            item_records: Item records dict.
            staffing_level: Number of available servers.
            service_family: Service time distribution ("exponential" or "normal").
            mean_service_minutes: Mean service time in minutes.
            rng: Random number generator for this queue.
            event_heap: Event heap.
            sequence_counter: Current sequence counter.
            duration_minutes: Duration of simulation.
            agent_config: Agent configuration for applying agent extra minutes.

        Returns:
            Updated sequence counter.
        """
        while waiting[queue] and busy[queue] < staffing_level:
            item_id, enqueue_time = waiting[queue].popleft()

            # Get a server
            server_id = free_servers[queue].pop()
            busy[queue] += 1

            # Draw service time
            if service_family == "exponential":
                service_time = rng.exponential(mean_service_minutes)
            elif service_family == "normal":
                service_time = max(
                    0.5, rng.normal(mean_service_minutes, 0.25 * mean_service_minutes)
                )
            else:
                service_time = mean_service_minutes

            # Apply agent extra minutes
            if agent_config is not None:
                if queue == "prescriber_review" and agent_config.consult_scribe:
                    # Add consult_scribe extra time based on toggle state
                    if self.agent_toggles.get("consult_scribe", True):
                        service_time += agent_config.consult_scribe.on_extra_minutes
                    else:
                        service_time += agent_config.consult_scribe.off_extra_minutes
                elif queue == "intake" and agent_config.integrity:
                    # Add integrity extra time based on toggle state
                    if self.agent_toggles.get("integrity", True):
                        service_time += agent_config.integrity.on_extra_minutes
                    else:
                        service_time += agent_config.integrity.off_extra_minutes

            duration = max(1, int(np.ceil(service_time)))
            finish_time = current_time + duration

            # Update record with started_at
            key = (queue, item_id)
            old_record = item_records[key]
            item_records[key] = ItemRecord(
                queue=old_record.queue,
                item_id=old_record.item_id,
                enqueued_at=old_record.enqueued_at,
                started_at=current_time,
                finished_at=None,
                server=server_id,
            )

            # Schedule finish event (tie-break: process finish before arrive at same time)
            # We do this by using a smaller sequence number for finish events
            event = Event(
                timestamp=finish_time,
                sequence_number=sequence_counter,
                event_type="finish",
                queue=queue,
                item_id=item_id,
                server=server_id,
            )
            heapq.heappush(event_heap, (event.timestamp, event.sequence_number, event))
            sequence_counter += 1

        return sequence_counter

    def _route_item(
        self,
        queue: str,
        item_id: str,
        current_time: int,
        waiting: dict[str, deque[tuple[str, int]]],
        event_heap: list[tuple[int, int, Event]],
        sequence_counter: int,
        duration_minutes: int,
    ) -> int:
        """Route a finished item to the next queue if applicable.

        Routing logic:
        - intake finished for questionnaire Q: schedule consult with questionnaire_id==Q
          to prescriber_review
        - prescriber_review finished for consult C: schedule orders with prescription
          matching a prescription with consult_id==C to pharmacy_fulfilment
        - pharmacy_fulfilment and support_inbox: no further routing

        Args:
            queue: Current queue name.
            item_id: Item ID.
            current_time: Current simulated time.
            waiting: Waiting queue dict.
            event_heap: Event heap.
            sequence_counter: Current sequence counter.
            duration_minutes: Duration of simulation.

        Returns:
            Updated sequence counter.
        """
        if queue == "intake":
            # Find consult with matching questionnaire_id
            for consult in self.world.consults:
                if consult.questionnaire_id == item_id:
                    # Schedule consult to arrive at prescriber_review
                    arrive_time = max(current_time, consult.scheduled_at_minute)
                    if arrive_time <= duration_minutes:
                        event = Event(
                            timestamp=arrive_time,
                            sequence_number=sequence_counter,
                            event_type="arrive",
                            queue="prescriber_review",
                            item_id=consult.consult_id,
                        )
                        heapq.heappush(event_heap, (event.timestamp, event.sequence_number, event))
                        sequence_counter += 1

        elif queue == "prescriber_review":
            # Find prescription with matching consult_id
            for prescription in self.world.prescriptions:
                if prescription.consult_id == item_id:
                    # Find all orders with this prescription_id
                    for order in self.world.orders:
                        if order.prescription_id == prescription.prescription_id:
                            # Schedule order to arrive at pharmacy_fulfilment
                            if current_time <= duration_minutes:
                                event = Event(
                                    timestamp=current_time,
                                    sequence_number=sequence_counter,
                                    event_type="arrive",
                                    queue="pharmacy_fulfilment",
                                    item_id=order.order_id,
                                )
                                heapq.heappush(
                                    event_heap, (event.timestamp, event.sequence_number, event)
                                )
                                sequence_counter += 1

        # pharmacy_fulfilment and support_inbox have no routing
        return sequence_counter

    def _compute_hash(
        self,
        records: tuple[ItemRecord, ...],
        staffing: dict[str, int],
        agent_toggles: dict[str, bool],
    ) -> str:
        """Compute run hash from records, staffing, and agent toggles.

        Args:
            records: Tuple of ItemRecords.
            staffing: Staffing dict.
            agent_toggles: Agent toggle state dict.

        Returns:
            SHA256 hex hash.
        """
        # Create deterministic JSON representation
        records_dicts = [
            {
                "queue": r.queue,
                "item_id": r.item_id,
                "enqueued_at": r.enqueued_at,
                "started_at": r.started_at,
                "finished_at": r.finished_at,
                "server": r.server,
            }
            for r in records
        ]
        staffing_dict = dict(sorted(staffing.items()))
        agent_toggles_dict = dict(sorted(agent_toggles.items()))

        hash_input = json.dumps(
            {
                "records": records_dicts,
                "staffing": staffing_dict,
                "agent_toggles": agent_toggles_dict,
            },
            sort_keys=True,
        )

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def run_hash(self) -> str:
        """Return the run hash from the last run.

        Returns:
            SHA256 hex hash.

        Raises:
            RuntimeError: If no run has been executed yet.
        """
        if self._last_run_result is None:
            raise RuntimeError("No run executed yet")
        return self._last_run_result.run_hash
