from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, List

@dataclass
class AuditEvent:
    timestamp: str
    action_id: str
    mandate_id: str
    decision: str
    reason: str

class AuditLog:
    def __init__(self):
        self.events: List[AuditEvent] = []

    def record(self, action_id: str, mandate_id: str, decision: str, reason: str):
        self.events.append(AuditEvent(datetime.now(timezone.utc).isoformat(), action_id, mandate_id, decision, reason))

    def export(self) -> List[Dict[str, str]]:
        return [asdict(e) for e in self.events]
