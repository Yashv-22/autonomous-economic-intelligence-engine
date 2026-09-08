import json
from typing import List, Dict, Any, Optional
from src.core.events import event_bus, SystemEvent
from src.models.schemas import AuditRecord
from src.core.identifiers import generate_uuid, compute_sha256
from src.knowledge.interfaces import RelationalStoreInterface
from src.core.logging import logger


class AuditLogger:
    """Manages telemetry events and immutable cryptographic audit trail recording."""

    def __init__(self, relational_store: Optional[RelationalStoreInterface] = None):
        self.relational_store = relational_store
        # Subscribe to all events on event bus
        event_bus.subscribe("*", self._handle_event)

    def _handle_event(self, event: SystemEvent):
        """Process and record telemetry events with deterministic cryptographic hashing."""
        if self.relational_store:
            try:
                # Extract run_id if present in payload or correlation_id
                run_id = "LEGACY-CORPUS"
                if isinstance(event.payload, dict) and event.payload.get("run_id"):
                    run_id = str(event.payload["run_id"])
                elif event.correlation_id and event.correlation_id.startswith("RUN-"):
                    run_id = event.correlation_id

                input_meta = {
                    "event_type": event.event_type,
                    "correlation_id": event.correlation_id or "NONE",
                    "agent_id": event.agent_id or "system",
                    "timestamp": event.timestamp,
                }
                output_payload = event.payload if isinstance(event.payload, dict) else {"payload": str(event.payload)}

                in_hash = compute_sha256(json.dumps(input_meta, sort_keys=True, default=str))
                out_hash = compute_sha256(json.dumps(output_payload, sort_keys=True, default=str))

                record = AuditRecord(
                    audit_id=f"AUD-{generate_uuid()[:8].upper()}",
                    run_id=run_id,
                    correlation_id=event.correlation_id or "NONE",
                    timestamp=event.timestamp,
                    action=event.event_type,
                    actor=event.agent_id or "system",
                    input_hash=in_hash,
                    output_hash=out_hash,
                    metadata=output_payload,
                    status="SUCCESS",
                )
                self.relational_store.log_audit_record(record)
            except Exception as e:
                logger.error(f"Failed to record audit event: {e}")
