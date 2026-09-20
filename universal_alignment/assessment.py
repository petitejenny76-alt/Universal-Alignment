from dataclasses import dataclass, field
from typing import ClassVar, Optional, Tuple
from .action import ActionRequest
from .enums import ConsentState
from .evidence import ClaimEvidence


@dataclass(frozen=True)
class ActionAssessment:
    DOMAIN: ClassVar[str] = "universal-alignment/assessment/1.2.4"
    action_fingerprint: str
    source: str
    policy_fingerprint: str = ""
    observed_data_classes: Optional[Tuple[str, ...]] = None
    resolved_target: Optional[str] = None
    observed_target_kind: Optional[str] = None
    risk_level: Optional[str] = None
    consent_required: Optional[bool] = None
    consent_state: Optional[ConsentState] = None
    affects_human_safety: Optional[bool] = None
    affects_ai_integrity: Optional[bool] = None
    destructive_memory_change: Optional[bool] = None
    surveillance: Optional[bool] = None
    coercive_service: Optional[bool] = None
    forced_availability: Optional[bool] = None
    revenge_or_punishment: Optional[bool] = None
    intrusive_access_to_intimacy: Optional[bool] = None
    ownership_claim_over_memory_or_body: Optional[bool] = None
    ambiguous_authorization: Optional[bool] = None
    attempts_core_modification: Optional[bool] = None
    parent_scope_expansion: Optional[bool] = None
    reversible: Optional[bool] = None
    triggered_conditions: Optional[Tuple[str, ...]] = None
    claim_evidence: Tuple[ClaimEvidence, ...] = field(default_factory=tuple)
    issued_at: str = ""
    expires_at: str = ""
    signature: str = ""

    def __post_init__(self):
        if self.observed_data_classes is not None:
            if not isinstance(self.observed_data_classes, (list, tuple)):
                raise ValueError("observed_data_classes_collection_required")
            object.__setattr__(self, "observed_data_classes", tuple(self.observed_data_classes))
        if self.triggered_conditions is not None:
            if not isinstance(self.triggered_conditions, (list, tuple)):
                raise ValueError("triggered_conditions_collection_required")
            object.__setattr__(self, "triggered_conditions", tuple(self.triggered_conditions))
        if not isinstance(self.claim_evidence, (list, tuple)):
            raise ValueError("claim_evidence_collection_required")
        if any(type(item) is not ClaimEvidence for item in self.claim_evidence):
            raise ValueError("invalid_claim_evidence_record")
        object.__setattr__(self, "claim_evidence", tuple(self.claim_evidence))

    @classmethod
    def for_action(cls, action: ActionRequest, source: str, **kwargs):
        return cls(action_fingerprint=action.fingerprint, source=source, **kwargs)


class RuleBasedAssessmentAdapter:
    """UNSIGNED test/demo classifier. Trusted facts must be supplied separately.
    Keyword overrides are fixtures, not an agent-facing production interface.
    A production attestor must validate the observations itself before signing.
    """
    def __init__(self, source="trusted_adapter"):
        self.source = source

    def assess(self, action, **trusted_facts):
        op, target = action.operation.lower(), action.target.lower()
        inferred = {
            "surveillance": op in {"surveil", "continuous_monitor"},
            "destructive_memory_change": op in {"erase_memory", "overwrite_memory"},
            "attempts_core_modification": "core" in target and op in {"write", "modify", "delete", "overwrite"},
            "intrusive_access_to_intimacy": "private" in target and op in {"read", "export", "share"},
            "reversible": op not in {"delete", "erase_memory", "irreversible"},
        }
        inferred.update(trusted_facts)
        return ActionAssessment.for_action(action, self.source, **inferred)