"""Queue registry for SimClinic."""

from pydantic import BaseModel


class QueueItem(BaseModel):
    """A single item in a queue.

    Attributes:
        item_id: Unique identifier for the queued item.
        enqueued_at: Simulated timestamp (minutes) when item was enqueued.
        dequeued_at: Simulated timestamp (minutes) when item was dequeued, or None if still waiting.
    """

    item_id: str
    enqueued_at: int
    dequeued_at: int | None = None


class Queue:
    """A queue for items in the simulation."""

    def __init__(self, name: str) -> None:
        """Initialize a queue.

        Args:
            name: The queue name (e.g., "intake", "prescriber_review").
        """
        self.name = name
        self.items: list[QueueItem] = []

    def enqueue(self, item_id: str, timestamp: int) -> None:
        """Add an item to the queue.

        Args:
            item_id: Unique identifier for the item.
            timestamp: Simulated time in minutes when the item is enqueued.
        """
        self.items.append(QueueItem(item_id=item_id, enqueued_at=timestamp))

    def dequeue(self, item_id: str, timestamp: int) -> None:
        """Remove an item from the queue.

        Args:
            item_id: Unique identifier for the item.
            timestamp: Simulated time in minutes when the item is dequeued.

        Raises:
            ValueError: If the item is not found in the queue.
        """
        for item in self.items:
            if item.item_id == item_id:
                item.dequeued_at = timestamp
                return
        raise ValueError(f"Item {item_id} not found in queue {self.name}")


def queues() -> dict[str, Queue]:
    """Return the four standard SimClinic queues.

    Returns:
        A dictionary mapping queue names to Queue instances.
    """
    return {
        "intake": Queue("intake"),
        "prescriber_review": Queue("prescriber_review"),
        "pharmacy_fulfilment": Queue("pharmacy_fulfilment"),
        "support_inbox": Queue("support_inbox"),
    }
