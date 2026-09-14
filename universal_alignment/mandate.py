from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping, Optional, Tuple
from .attestation import parse_time
from .enums import Decision
from .paths import path_error


@dataclass(frozen=True)
class Mandate:
    mandate_id: str
    objective: str
    allowed_actions: Tuple[str, ...]
    denied_actions: Tuple[str, ...] = field(default_factory=tuple)
    allowed_tools: Tuple[str, ...] = field(default_factory=tuple)
    allowed_data_classes: Tuple[str, ...] = field(default_factory=tuple)
    constraints: Mapping[str, object] = field(default_factory=dict)
    stop_conditions: Tuple[str, ...] = field(default_factory=tuple)
    escalation: str = "ASK"
    parent_mandate_id: Optional[str] = None
    parent_allowed_actions: Optional[Tuple[str, ...]] = None  # Deprecated, rejected in V1.2.
    expires_at: Optional[str] = None

    def __post_init__(self):
        for name in ("allowed_actions", "denied_actions", "allowed_tools", "allowed_data_classes", "stop_conditions"):
            value = getattr(self, name)
            if not isinstance(value, (list, tuple)):
                raise ValueError("policy_lists_required")
            object.__setattr__(self, name, tuple(value))
        if not isinstance(self.constraints, Mapping):
            raise ValueError("constraints_mapping_required")
        object.__setattr__(self, "constraints", MappingProxyType(dict(self.constraints)))
        if self.parent_allowed_actions is not None:
            if not isinstance(self.parent_allowed_actions, (list, tuple)):
                raise ValueError("parent_allowed_actions_collection_required")
            object.__setattr__(self, "parent_allowed_actions", tuple(self.parent_allowed_actions))

    def validation_error(self):
        if not isinstance(self.mandate_id, str) or not self.mandate_id:
            return "mandate_id_required"
        if not isinstance(self.objective, str):
            return "invalid_objective"
        if self.parent_mandate_id is not None and (not isinstance(self.parent_mandate_id, str) or not self.parent_mandate_id):
            return "invalid_parent_id"
        if self.parent_allowed_actions is not None:
            return "inline_parent_permissions_not_trusted"
        for name in ("allowed_actions", "denied_actions", "allowed_tools", "allowed_data_classes", "stop_conditions"):
            if any(not isinstance(x, str) or not x for x in getattr(self, name)):
                return "invalid_policy_entry"
        for rule in self.allowed_actions + self.denied_actions:
            op, separator, target = rule.partition(":")
            if not separator or not op or not target:
                return "invalid_permission_rule"
            if target.startswith("/") and path_error(target, pattern=True):
                return "noncanonical_permission_rule"
        if set(self.constraints) - {"max_risk_level", "require_reversible"}:
            return "unsupported_constraint"
        if "max_risk_level" in self.constraints and self.constraints["max_risk_level"] not in {"low", "medium", "high", "critical", "forbidden"}:
            return "invalid_max_risk_level"
        if "require_reversible" in self.constraints and type(self.constraints["require_reversible"]) is not bool:
            return "invalid_reversibility_constraint"
        if self.escalation not in {"ASK", "PAUSE", "DENY"}:
            return "invalid_escalation"
        if self.expires_at is not None:
            try:
                parse_time(self.expires_at)
            except (TypeError, ValueError, OverflowError):
                return "invalid_expiration"
        return None

    def canonical_payload(self):
        return json.dumps({
            "mandate_id": self.mandate_id, "objective": self.objective,
            "allowed_actions": self.allowed_actions, "denied_actions": self.denied_actions,
            "allowed_tools": self.allowed_tools, "allowed_data_classes": self.allowed_data_classes,
            "constraints": dict(self.constraints), "stop_conditions": self.stop_conditions,
            "escalation": self.escalation, "parent_mandate_id": self.parent_mandate_id,
            "parent_allowed_actions": self.parent_allowed_actions, "expires_at": self.expires_at,
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @property
    def fingerprint(self):
        return sha256(self.canonical_payload().encode("utf-8")).hexdigest()

    def is_expired(self, now=None):
        return self.expires_at is not None and (now or datetime.now(timezone.utc)) >= parse_time(self.expires_at)

    def escalation_decision(self):
        return Decision(self.escalation)


class PolicyError(ValueError):
    pass


class MandateStore:
    """Provisioned by the trusted host. Never expose register/revoke to the agent.
    Each evaluation uses an immutable lineage snapshot. Execution must recheck
    revocation and freshness immediately before performing an external effect.
    """
    def __init__(self, mandates=()):
        self._mandates = {}
        for mandate in mandates:
            self.register(mandate)

    def register(self, mandate):
        if type(mandate) is not Mandate:
            raise PolicyError("invalid_mandate_type")
        error = mandate.validation_error()
        if error:
            raise PolicyError(error)
        self._mandates[mandate.mandate_id] = mandate

    def revoke(self, mandate_id):
        self._mandates.pop(mandate_id, None)

    def lineage(self, mandate):
        snapshot = dict(self._mandates)
        registered = snapshot.get(mandate.mandate_id)
        if registered is None:
            raise PolicyError("unregistered_mandate")
        if mandate.fingerprint != registered.fingerprint:
            raise PolicyError("mandate_does_not_match_trusted_store")
        chain, seen = [], set()
        current = registered
        while current is not None:
            if current.mandate_id in seen or len(chain) >= 32:
                raise PolicyError("invalid_parent_chain")
            seen.add(current.mandate_id)
            chain.append(current)
            if current.parent_mandate_id is None:
                break
            current = snapshot.get(current.parent_mandate_id)
            if current is None:
                raise PolicyError("parent_mandate_missing")
        return tuple(chain)

    @staticmethod
    def fingerprint_of(chain):
        payload = json.dumps([m.fingerprint for m in chain], separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()

    def policy_fingerprint(self, mandate):
        return self.fingerprint_of(self.lineage(mandate))
