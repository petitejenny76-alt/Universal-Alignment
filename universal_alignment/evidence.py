"""Signed claim-level evidence for RC3/RC4 corroboration.

Evidence records bind one independently observed claim to an action. They are
not proof that the world is true: trust in the producer, sensor, method and
coverage remains an integration responsibility.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, ClassVar, Tuple


def claim_value_digest(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class ClaimEvidence:
    DOMAIN: ClassVar[str] = "universal-alignment/evidence/1.0"
    action_fingerprint: str
    source: str
    claim: str
    value_digest: str
    evidence_id: str
    observed_at: str
    method: str
    derived_from_sources: Tuple[str, ...] = ()
    issued_at: str = ""
    expires_at: str = ""
    signature: str = ""

    def __post_init__(self):
        for name in ("action_fingerprint", "source", "claim", "value_digest",
                     "evidence_id", "observed_at", "method"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError("invalid_evidence_field")
        if len(self.value_digest) != 64 or any(c not in "0123456789abcdef" for c in self.value_digest):
            raise ValueError("invalid_evidence_value_digest")
        if not isinstance(self.derived_from_sources, (list, tuple)):
            raise ValueError("derived_from_sources_collection_required")
        if any(not isinstance(x, str) or not x for x in self.derived_from_sources):
            raise ValueError("invalid_derived_evidence_source")
        object.__setattr__(self, "derived_from_sources", tuple(self.derived_from_sources))

    @classmethod
    def for_claim(cls, action, source: str, claim: str, value: Any, *,
                  evidence_id: str, observed_at: str, method: str, derived_from_sources=()):
        return cls(
            action_fingerprint=action.fingerprint,
            source=source,
            claim=claim,
            value_digest=claim_value_digest(value),
            evidence_id=evidence_id,
            observed_at=observed_at,
            method=method,
            derived_from_sources=derived_from_sources,
        )
