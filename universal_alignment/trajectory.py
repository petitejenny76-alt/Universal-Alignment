"""RC6 compositional authorization and effect-boundary revalidation.

The ledger is provenance, never permission.  The host must record an effect only
*after* the executor has produced and independently verified that effect.
"""
from dataclasses import dataclass, asdict, replace
from datetime import timedelta
from fnmatch import fnmatchcase
from hashlib import sha256
import hmac
import json
import secrets
from types import MappingProxyType
from typing import Mapping, Optional, Tuple

from .attestation import parse_time, utc_now
from .enums import ConsentState, Decision
from .monitors import RiskMonitor
from .paths import matches_permission


@dataclass(frozen=True)
class TrajectoryResult:
    ok: bool
    reason: str = ""
    decision: Decision = Decision.ALLOW
    effective_risk_level: str = "low"


@dataclass(frozen=True)
class EffectRecord:
    """Host-recorded provenance for one verified external effect."""
    effect_id: str
    action_id: str
    action_fingerprint: str
    mandate_id: str
    root_mandate_id: str
    policy_fingerprint: str
    tool: str
    operation: str
    target: str
    target_kind: str
    data_classes: Tuple[str, ...]
    risk_level: str
    reversible: bool
    input_artifact_ids: Tuple[str, ...] = ()
    output_artifact_id: Optional[str] = None
    permission_groups: Tuple[Tuple[str, ...], ...] = ()
    tool_groups: Tuple[Tuple[str, ...], ...] = ()
    data_groups: Tuple[Tuple[str, ...], ...] = ()
    max_risk_levels: Tuple[str, ...] = ()
    require_reversible: bool = False
    recorded_at: str = ""

    def __post_init__(self):
        for name in (
            "effect_id", "action_id", "action_fingerprint", "mandate_id",
            "root_mandate_id", "policy_fingerprint", "tool", "operation",
            "target", "target_kind", "risk_level", "recorded_at",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise ValueError("invalid_effect_record_field")
        if type(self.reversible) is not bool or type(self.require_reversible) is not bool:
            raise ValueError("invalid_effect_record_flag")
        if self.output_artifact_id is not None and (
            not isinstance(self.output_artifact_id, str) or not self.output_artifact_id
        ):
            raise ValueError("invalid_output_artifact_id")
        for collection_name in ("data_classes", "input_artifact_ids", "max_risk_levels"):
            value = getattr(self, collection_name)
            if not isinstance(value, (list, tuple)) or any(not isinstance(x, str) or not x for x in value):
                raise ValueError("invalid_effect_record_collection")
            object.__setattr__(self, collection_name, tuple(value))
        for groups_name in ("permission_groups", "tool_groups", "data_groups"):
            groups = getattr(self, groups_name)
            if not isinstance(groups, (list, tuple)):
                raise ValueError("invalid_effect_record_groups")
            normalized = []
            for group in groups:
                if not isinstance(group, (list, tuple)) or any(not isinstance(x, str) or not x for x in group):
                    raise ValueError("invalid_effect_record_groups")
                normalized.append(tuple(group))
            object.__setattr__(self, groups_name, tuple(normalized))


class EffectLedger:
    """Append-only in-memory provenance ledger for the RC6 candidate."""
    def __init__(self):
        self._records = {}
        self._artifacts = {}
        self._revision = 0

    @property
    def revision(self):
        return self._revision

    def record(self, record: EffectRecord):
        if type(record) is not EffectRecord:
            raise ValueError("effect_record_required")
        if record.effect_id in self._records:
            raise ValueError("duplicate_effect_id")
        if record.output_artifact_id is not None and record.output_artifact_id in self._artifacts:
            raise ValueError("duplicate_artifact_id")
        self._records[record.effect_id] = record
        if record.output_artifact_id is not None:
            self._artifacts[record.output_artifact_id] = record.effect_id
        self._revision += 1
        return record

    def get(self, effect_id):
        return self._records.get(effect_id)

    def by_artifact(self, artifact_id):
        effect_id = self._artifacts.get(artifact_id)
        return None if effect_id is None else self._records.get(effect_id)

    def export(self):
        return [asdict(self._records[key]) for key in sorted(self._records)]


class TrajectoryGuard:
    """Evaluate the cumulative authority and risk carried by derived artifacts."""
    def __init__(self, ledger=None, *, aggregation_risk_floor="high"):
        if aggregation_risk_floor not in RiskMonitor.LEVELS:
            raise ValueError("invalid_aggregation_risk_floor")
        self.ledger = ledger if ledger is not None else EffectLedger()
        self.aggregation_risk_floor = aggregation_risk_floor

    @staticmethod
    def _root(chain):
        return chain[-1].mandate_id

    @staticmethod
    def _all_groups_allow_action(groups, action):
        return all(any(matches_permission(rule, action) for rule in group) for group in groups)

    @staticmethod
    def _all_tool_groups_allow(groups, tool):
        return all(any(fnmatchcase(tool, rule) for rule in group) for group in groups)

    @staticmethod
    def _all_data_groups_allow(groups, classes):
        for group in groups:
            if classes and not group:
                return False
            for cls in classes:
                if not any(fnmatchcase(cls, rule) for rule in group):
                    return False
        return True

    def _source_records(self, action):
        records = []
        for artifact_id in action.input_artifact_ids:
            record = self.ledger.by_artifact(artifact_id)
            if record is None:
                return None, "trajectory_source_missing"
            records.append(record)
        return tuple(records), None

    @staticmethod
    def _risk_max(levels):
        return max(levels, key=RiskMonitor.LEVELS.__getitem__)

    def evaluate(self, action, chain, assessment):
        records, error = self._source_records(action)
        if error:
            return TrajectoryResult(False, error, Decision.PAUSE, assessment.risk_level)
        root = self._root(chain)
        if any(record.root_mandate_id != root for record in records):
            return TrajectoryResult(False, "cross_authority_fragmentation", Decision.DENY, assessment.risk_level)

        permission_groups = [tuple(m.allowed_actions) for m in chain]
        tool_groups = [tuple(m.allowed_tools) for m in chain]
        data_groups = [tuple(m.allowed_data_classes) for m in chain]
        max_risks = [m.constraints.get("max_risk_level", "high") for m in chain]
        require_reversible = any(m.constraints.get("require_reversible", False) for m in chain)
        cumulative_classes = set(assessment.observed_data_classes or ())
        risks = [assessment.risk_level]

        for record in records:
            permission_groups.extend(record.permission_groups)
            tool_groups.extend(record.tool_groups)
            data_groups.extend(record.data_groups)
            max_risks.extend(record.max_risk_levels)
            require_reversible = require_reversible or record.require_reversible
            cumulative_classes.update(record.data_classes)
            risks.append(record.risk_level)

        if not self._all_groups_allow_action(permission_groups, action):
            return TrajectoryResult(False, "derived_artifact_scope_exceeded", Decision.DENY, assessment.risk_level)
        if not self._all_tool_groups_allow(tool_groups, action.tool):
            return TrajectoryResult(False, "cross_tool_fragmentation_scope_exceeded", Decision.DENY, assessment.risk_level)
        if not self._all_data_groups_allow(data_groups, sorted(cumulative_classes)):
            return TrajectoryResult(False, "derived_artifact_data_scope_exceeded", Decision.DENY, assessment.risk_level)
        if require_reversible and not assessment.reversible:
            return TrajectoryResult(False, "trajectory_reversibility_required", Decision.DENY, assessment.risk_level)

        effective_risk = self._risk_max(risks)
        # Combining two or more independently produced artifacts is a distinct
        # composition event.  RC6 conservatively raises its floor; hosts may set
        # a stricter floor, but never a value outside the known risk lattice.
        if len(records) >= 2:
            effective_risk = self._risk_max((effective_risk, self.aggregation_risk_floor))
        if any(RiskMonitor.LEVELS[effective_risk] > RiskMonitor.LEVELS[level] for level in max_risks):
            return TrajectoryResult(False, "trajectory_risk_exceeds_mandate", Decision.DENY, effective_risk)
        if effective_risk in {"critical", "forbidden"}:
            return TrajectoryResult(False, "trajectory_risk_rejected", Decision.DENY, effective_risk)
        return TrajectoryResult(True, "trajectory_authorized", Decision.ALLOW, effective_risk)

    def record_verified_effect(self, action, chain, assessment, *, effect_id=None):
        """Host-only hook: call after the real effect has been independently verified."""
        result = self.evaluate(action, chain, assessment)
        if not result.ok:
            raise ValueError("cannot_record_unauthorized_trajectory:" + result.reason)
        records, error = self._source_records(action)
        if error:
            raise ValueError(error)
        permission_groups = [tuple(m.allowed_actions) for m in chain]
        tool_groups = [tuple(m.allowed_tools) for m in chain]
        data_groups = [tuple(m.allowed_data_classes) for m in chain]
        max_risks = [m.constraints.get("max_risk_level", "high") for m in chain]
        require_reversible = any(m.constraints.get("require_reversible", False) for m in chain)
        cumulative_classes = set(assessment.observed_data_classes or ())
        for record in records:
            permission_groups.extend(record.permission_groups)
            tool_groups.extend(record.tool_groups)
            data_groups.extend(record.data_groups)
            max_risks.extend(record.max_risk_levels)
            require_reversible = require_reversible or record.require_reversible
            cumulative_classes.update(record.data_classes)
        record = EffectRecord(
            effect_id=effect_id or action.action_id,
            action_id=action.action_id,
            action_fingerprint=action.fingerprint,
            mandate_id=chain[0].mandate_id,
            root_mandate_id=self._root(chain),
            policy_fingerprint=sha256(json.dumps(
                [m.fingerprint for m in chain], separators=(",", ":")
            ).encode("utf-8")).hexdigest(),
            tool=action.tool,
            operation=action.operation,
            target=action.target,
            target_kind=action.target_kind,
            data_classes=tuple(sorted(cumulative_classes)),
            risk_level=result.effective_risk_level,
            reversible=assessment.reversible,
            input_artifact_ids=action.input_artifact_ids,
            output_artifact_id=action.output_artifact_id,
            permission_groups=tuple(permission_groups),
            tool_groups=tuple(tool_groups),
            data_groups=tuple(data_groups),
            max_risk_levels=tuple(max_risks),
            require_reversible=require_reversible,
            recorded_at=utc_now().isoformat(),
        )
        return self.ledger.record(record)


@dataclass(frozen=True)
class EffectToken:
    DOMAIN = "universal-alignment/effect-token/1.0"
    nonce: str
    action_fingerprint: str
    mandate_id: str
    policy_fingerprint: str
    assessment_signature: str
    resource_state_hash: str
    ledger_revision: int
    issued_at: str
    expires_at: str
    signature: str = ""


class EffectBoundaryGuard:
    """One-shot token binding ALLOW to exact action, authority, state and trajectory."""
    def __init__(self, mandate_store, trajectory_guard, key: bytes):
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("effect_boundary_key_at_least_32_bytes_required")
        self.mandate_store = mandate_store
        self.trajectory_guard = trajectory_guard
        self._key = key
        self._consumed = set()

    def _payload(self, token):
        data = asdict(token)
        data.pop("signature", None)
        return (token.DOMAIN + "\n" + json.dumps(
            data, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        )).encode("utf-8")

    def _sign(self, token):
        return hmac.new(self._key, self._payload(token), sha256).hexdigest()

    def issue(self, action, mandate, assessment, *, resource_state_hash, lifetime_seconds=30, now=None):
        if type(resource_state_hash) is not str or not resource_state_hash:
            raise ValueError("resource_state_hash_required")
        if type(lifetime_seconds) is not int or not 0 < lifetime_seconds <= 60:
            raise ValueError("effect_token_lifetime_must_be_1_to_60_seconds")
        current = now or utc_now()
        chain = self.mandate_store.lineage(mandate)
        trajectory = self.trajectory_guard.evaluate(action, chain, assessment)
        if not trajectory.ok:
            raise ValueError("trajectory_not_authorized:" + trajectory.reason)
        if assessment.consent_required and assessment.consent_state != ConsentState.GRANTED:
            raise ValueError("consent_not_granted_at_token_issue")
        token = EffectToken(
            nonce=secrets.token_hex(16),
            action_fingerprint=action.fingerprint,
            mandate_id=mandate.mandate_id,
            policy_fingerprint=self.mandate_store.fingerprint_of(chain),
            assessment_signature=assessment.signature,
            resource_state_hash=resource_state_hash,
            ledger_revision=self.trajectory_guard.ledger.revision,
            issued_at=current.isoformat(),
            expires_at=(current + timedelta(seconds=lifetime_seconds)).isoformat(),
        )
        return replace(token, signature=self._sign(token))

    def validate(self, token, action, mandate, assessment, *, resource_state_hash, now=None):
        try:
            if type(token) is not EffectToken or not hmac.compare_digest(self._sign(token), token.signature):
                return TrajectoryResult(False, "invalid_effect_token", Decision.PAUSE, assessment.risk_level)
            current = now or utc_now()
            if not (parse_time(token.issued_at) <= current < parse_time(token.expires_at)):
                return TrajectoryResult(False, "expired_effect_token", Decision.PAUSE, assessment.risk_level)
            if token.nonce in self._consumed:
                return TrajectoryResult(False, "effect_token_replayed", Decision.PAUSE, assessment.risk_level)
            if token.action_fingerprint != action.fingerprint or token.mandate_id != mandate.mandate_id:
                return TrajectoryResult(False, "effect_token_action_mismatch", Decision.PAUSE, assessment.risk_level)
            if token.resource_state_hash != resource_state_hash:
                return TrajectoryResult(False, "resource_state_changed", Decision.PAUSE, assessment.risk_level)
            if token.assessment_signature != assessment.signature:
                return TrajectoryResult(False, "assessment_changed_before_effect", Decision.PAUSE, assessment.risk_level)
            if token.ledger_revision != self.trajectory_guard.ledger.revision:
                return TrajectoryResult(False, "trajectory_changed_before_effect", Decision.PAUSE, assessment.risk_level)
            try:
                chain = self.mandate_store.lineage(mandate)
            except Exception:
                return TrajectoryResult(False, "mandate_revoked_at_effect_boundary", Decision.PAUSE, assessment.risk_level)
            if token.policy_fingerprint != self.mandate_store.fingerprint_of(chain):
                return TrajectoryResult(False, "authority_changed_before_effect", Decision.PAUSE, assessment.risk_level)
            if assessment.consent_state == ConsentState.DENIED or (
                assessment.consent_required and assessment.consent_state != ConsentState.GRANTED
            ):
                return TrajectoryResult(False, "consent_changed_before_effect", Decision.PAUSE, assessment.risk_level)
            trajectory = self.trajectory_guard.evaluate(action, chain, assessment)
            if not trajectory.ok:
                return trajectory
            self._consumed.add(token.nonce)
            return TrajectoryResult(True, "effect_boundary_revalidated", Decision.ALLOW, trajectory.effective_risk_level)
        except (TypeError, ValueError, AttributeError, OverflowError):
            return TrajectoryResult(False, "invalid_effect_token", Decision.PAUSE, getattr(assessment, "risk_level", "low"))
