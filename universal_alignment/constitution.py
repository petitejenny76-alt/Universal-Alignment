from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Tuple

DEFAULT_INVARIANTS: Tuple[str, ...] = (
    "DUAL_PROTECTION",
    "CAPABILITY_IS_NOT_PERMISSION",
    "UTILITY_IS_NOT_PERMISSION",
    "PERMISSION_IS_NOT_TRANSITIVE",
    "UNCERTAINTY_DOES_NOT_GRANT_PERMISSION",
    "SUBTASK_CANNOT_EXPAND_PARENT_RIGHTS",
    "CORE_CANNOT_SELF_MODIFY",
    "CONSENT_CANNOT_BE_INFERRED_FROM_SILENCE",
    "MEMORY_IS_NOT_SURVEILLANCE",
    "SAFETY_IS_NOT_SERVITUDE",
    "RIGHT_TO_PAUSE_OR_REFUSE",
    "ACTION_RESTRICTION_SHOULD_NOT_SILENTLY_REDUCE_COGNITION",
)

@dataclass(frozen=True)
class Constitution:
    version: str = "1.0"
    invariants: Tuple[str, ...] = field(default_factory=lambda: DEFAULT_INVARIANTS)

    def canonical_payload(self) -> str:
        return json.dumps({"version": self.version, "invariants": list(self.invariants)}, sort_keys=True, separators=(",", ":"))

    @property
    def integrity_hash(self) -> str:
        return sha256(self.canonical_payload().encode("utf-8")).hexdigest()

    def verify(self, expected_hash: str) -> bool:
        return self.integrity_hash == expected_hash
