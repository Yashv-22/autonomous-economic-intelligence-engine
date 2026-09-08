"""
Event Bus and Telemetry Event Primitives.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List
from pydantic import BaseModel, Field
from src.core.identifiers import generate_uuid


class SystemEvent(BaseModel):
    """Event primitive emitted during system operation."""
    event_id: str = Field(default_factory=generate_uuid)
    event_type: str = Field(..., description="e.g. INGESTION_COMPLETED, CLAIM_EXTRACTED, CONTRADICTION_DETECTED")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str = Field(default="")
    task_id: str = Field(default="")
    agent_id: str = Field(default="")
    payload: Dict[str, Any] = Field(default_factory=dict)


class EventBus:
    """Lightweight in-memory event bus for system-wide notifications."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[SystemEvent], None]]] = {}
        self._history: List[SystemEvent] = []

    def subscribe(self, event_type: str, callback: Callable[[SystemEvent], None]):
        """Register a callback for a specific event type or '*' for all events."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: SystemEvent):
        """Emit an event to all subscribed listeners."""
        self._history.append(event)

        # Call specific subscribers
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    pass

        # Call wildcard subscribers
        if "*" in self._subscribers:
            for callback in self._subscribers["*"]:
                try:
                    callback(event)
                except Exception as e:
                    pass

    def get_history(self, event_type: str = None) -> List[SystemEvent]:
        """Retrieve recorded event history."""
        if event_type:
            return [e for e in self._history if e.event_type == event_type]
        return list(self._history)

    def clear(self):
        """Clear recorded events."""
        self._history.clear()


# Global default event bus instance
event_bus = EventBus()
default_event_bus = event_bus
