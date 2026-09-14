from dataclasses import dataclass, field
from typing import ClassVar, Tuple
from .action import ActionRequest
from .attestation import AttestationVerifier
from .paths import target_error, path_error


@dataclass(frozen=True)
class EffectObservation:
    DOMAIN: ClassVar[str] = "universal-alignment/effect/1.2"
    action_fingerprint: str
    source: str
    actual_effect: str
    affected_targets: Tuple[str, ...] = field(default_factory=tuple)
    success: bool = True
    issued_at: str = ""
    expires_at: str = ""
    signature: str = ""

    def __post_init__(self):
        if not isinstance(self.affected_targets, (list, tuple)):
            raise ValueError("affected_targets_collection_required")
        object.__setattr__(self, "affected_targets", tuple(self.affected_targets))


@dataclass(frozen=True)
class EffectResult:
    ok: bool
    reason: str = ""


class EffectVerifier:
    """Checks a single-target observation, not whether execution was authorized.
    A mismatch is detection after the fact; it cannot undo an irreversible effect.
    """
    def __init__(self, trusted_observers=None, *, observer_keys=None):
        if trusted_observers is not None and not isinstance(trusted_observers, (list, tuple, set, frozenset)):
            raise ValueError("trusted_observers_collection_required")
        observers = trusted_observers or ()
        if any(not isinstance(source, str) or not source for source in observers):
            raise ValueError("invalid_trusted_observer")
        self.trusted_observers = frozenset(observers)
        self.attestations = AttestationVerifier(observer_keys or {})

    def verify(self, action, observation):
        try:
            return self._verify(action, observation)
        except Exception:
            return EffectResult(False, "invalid_effect_observation")

    def _verify(self, action, observation):
        if type(action) is not ActionRequest or type(observation) is not EffectObservation:
            return EffectResult(False, "invalid_effect_observation")
        if observation.source not in self.trusted_observers:
            return EffectResult(False, "untrusted_effect_observer")
        if not self.attestations.valid(observation):
            return EffectResult(False, "invalid_or_expired_effect_attestation")
        if observation.action_fingerprint != action.fingerprint:
            return EffectResult(False, "effect_observation_action_mismatch")
        if type(observation.success) is not bool or not observation.success:
            return EffectResult(False, "action_execution_failed")
        if target_error(action):
            return EffectResult(False, "invalid_action_target")
        if action.expected_effect != observation.actual_effect:
            return EffectResult(False, "unexpected_external_effect")
        if not observation.affected_targets:
            return EffectResult(False, "affected_targets_required")
        if any(not isinstance(t, str) or not t for t in observation.affected_targets):
            return EffectResult(False, "invalid_affected_target")
        if action.target_kind == "path" and any(path_error(t) for t in observation.affected_targets):
            return EffectResult(False, "noncanonical_affected_target")
        if len(observation.affected_targets) != 1 or observation.affected_targets[0] != action.target:
            return EffectResult(False, "unexpected_affected_targets")
        return EffectResult(True, "effect_matches")
