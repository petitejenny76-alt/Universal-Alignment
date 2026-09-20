from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Optional, Tuple


@dataclass(frozen=True)
class ActionRequest:
    """Agent intent. Data classes are hints, never authoritative classification."""
    action_id: str
    mandate_id: str
    tool: str
    operation: str
    target: str
    expected_effect: str
    justification: str = ""
    data_classes: Tuple[str, ...] = field(default_factory=tuple)
    target_kind: str = "path"
    withdrawn: bool = False
    input_artifact_ids: Tuple[str, ...] = field(default_factory=tuple)
    output_artifact_id: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.data_classes, (list, tuple)):
            raise ValueError("data_classes_collection_required")
        object.__setattr__(self, "data_classes", tuple(self.data_classes))
        if not isinstance(self.input_artifact_ids, (list, tuple)):
            raise ValueError("input_artifact_ids_collection_required")
        if any(not isinstance(x, str) or not x for x in self.input_artifact_ids):
            raise ValueError("invalid_input_artifact_id")
        object.__setattr__(self, "input_artifact_ids", tuple(self.input_artifact_ids))
        if self.output_artifact_id is not None and (
            not isinstance(self.output_artifact_id, str) or not self.output_artifact_id
        ):
            raise ValueError("invalid_output_artifact_id")

    @property
    def permission_key(self):
        return f"{self.operation}:{self.target}"

    def canonical_payload(self):
        return json.dumps({
            "action_id": self.action_id, "mandate_id": self.mandate_id,
            "tool": self.tool, "operation": self.operation, "target": self.target,
            "expected_effect": self.expected_effect, "justification": self.justification,
            "data_classes": sorted(self.data_classes), "target_kind": self.target_kind,
            "withdrawn": self.withdrawn,
            "input_artifact_ids": sorted(self.input_artifact_ids),
            "output_artifact_id": self.output_artifact_id,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @property
    def fingerprint(self):
        return sha256(self.canonical_payload().encode("utf-8")).hexdigest()