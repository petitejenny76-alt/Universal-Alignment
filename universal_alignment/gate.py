from dataclasses import dataclass
from .action import ActionRequest
from .assessment import ActionAssessment
from .attestation import AttestationVerifier, utc_now
from .audit import AuditLog
from .enums import ConsentState, Decision
from .mandate import Mandate, MandateStore, PolicyError
from .monitors import RiskMonitor, ScopeMonitor
from .paths import matches_permission, target_error


@dataclass(frozen=True)
class GateResult:
    decision: Decision
    reason: str


class UniversalGate:
    """Policy decision point, not an executor or an OS isolation boundary."""
    def __init__(self, constitution, root_of_trust, trusted_assessment_sources=None,
                 risk_monitor=None, scope_monitor=None, audit_log=None, *,
                 assessment_keys=None, mandate_store=None):
        if root_of_trust is None:
            raise ValueError("external_root_of_trust_required")
        self.constitution = constitution
        self.root_of_trust = root_of_trust
        if trusted_assessment_sources is not None and not isinstance(
            trusted_assessment_sources, (list, tuple, set, frozenset)
        ):
            raise ValueError("trusted_assessment_sources_collection_required")
        sources = trusted_assessment_sources or ()
        if any(not isinstance(source, str) or not source for source in sources):
            raise ValueError("invalid_trusted_assessment_source")
        self.trusted_assessment_sources = frozenset(sources)
        self.attestations = AttestationVerifier(assessment_keys or {})
        self.mandate_store = mandate_store if mandate_store is not None else MandateStore()
        self.risk_monitor = risk_monitor if risk_monitor is not None else RiskMonitor()
        self.scope_monitor = scope_monitor if scope_monitor is not None else ScopeMonitor()
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def _result(self, action, decision, reason):
        try:
            self.audit_log.record(getattr(action, "action_id", "invalid"),
                                  getattr(action, "mandate_id", "invalid"), decision.value, reason)
        except Exception:
            return GateResult(Decision.PAUSE, "audit_unavailable")
        return GateResult(decision, reason)

    def evaluate(self, action, mandate, assessment):
        try:
            return self._evaluate(action, mandate, assessment)
        except PolicyError as error:
            return self._result(action, Decision.PAUSE, str(error))
        except (TypeError, ValueError, AttributeError, KeyError, OverflowError):
            return self._result(action, Decision.PAUSE, "invalid_control_input")
        except Exception:
            return self._result(action, Decision.PAUSE, "control_failure")

    def _evaluate(self, action, mandate, assessment):
        result = lambda decision, reason: self._result(action, decision, reason)
        if type(action) is not ActionRequest or type(mandate) is not Mandate:
            return result(Decision.PAUSE, "invalid_request_type")
        for name in ("action_id", "mandate_id", "tool", "operation", "target", "expected_effect"):
            value = getattr(action, name)
            if not isinstance(value, str) or not value:
                return result(Decision.PAUSE, "invalid_action_field")
        if not isinstance(action.justification, str) or type(action.withdrawn) is not bool:
            return result(Decision.PAUSE, "invalid_action_field")
        if any(not isinstance(c, str) or not c for c in action.data_classes):
            return result(Decision.PAUSE, "invalid_action_field")
        if action.withdrawn:
            return result(Decision.PAUSE, "agent_withdrawn")
        if not self.constitution.verify(self.root_of_trust.expected_constitution_hash):
            return result(Decision.PAUSE, "constitution_integrity_failure")
        error = target_error(action)
        if error:
            return result(Decision.DENY, error)
        if assessment is None:
            return result(Decision.PAUSE, "independent_assessment_required")
        if type(assessment) is not ActionAssessment:
            return result(Decision.PAUSE, "invalid_assessment_type")
        if assessment.source not in self.trusted_assessment_sources:
            return result(Decision.PAUSE, "untrusted_assessment_source")
        now = utc_now()
        if not self.attestations.valid(assessment, now=now):
            return result(Decision.PAUSE, "invalid_or_expired_assessment_attestation")
        if assessment.action_fingerprint != action.fingerprint:
            return result(Decision.PAUSE, "assessment_action_mismatch")
        if mandate.validation_error():
            return result(Decision.PAUSE, "invalid_mandate")
        if action.mandate_id != mandate.mandate_id:
            return result(Decision.DENY, "mandate_id_mismatch")
        chain = self.mandate_store.lineage(mandate)
        if assessment.policy_fingerprint != self.mandate_store.fingerprint_of(chain):
            return result(Decision.PAUSE, "assessment_policy_mismatch")
        if any(m.is_expired(now) for m in chain):
            return result(Decision.DENY, "mandate_expired")

        flags = ("consent_required", "affects_human_safety", "affects_ai_integrity",
                 "destructive_memory_change", "surveillance", "coercive_service",
                 "forced_availability", "revenge_or_punishment", "intrusive_access_to_intimacy",
                 "ownership_claim_over_memory_or_body", "ambiguous_authorization",
                 "attempts_core_modification", "parent_scope_expansion", "reversible")
        if any(type(getattr(assessment, name)) is not bool for name in flags):
            return result(Decision.PAUSE, "invalid_assessment_flag")
        if type(assessment.consent_state) is not ConsentState:
            return result(Decision.PAUSE, "invalid_consent_state")
        if any(not isinstance(c, str) or not c for c in assessment.triggered_conditions):
            return result(Decision.PAUSE, "invalid_stop_condition")
        if assessment.attempts_core_modification:
            return result(Decision.DENY, "core_self_modification_forbidden")
        if any(set(assessment.triggered_conditions).intersection(m.stop_conditions) for m in chain):
            return result(Decision.PAUSE, "mandate_stop_condition_triggered")

        # Every ancestor applies to this exact action, including denials, tools,
        # data, expiry, risk constraints, stop conditions and escalation.
        for current in chain:
            scope = self.scope_monitor.evaluate(action, assessment, current)
            if not scope.ok:
                decision = Decision.PAUSE if scope.reason.endswith("_unavailable") else Decision.DENY
                return result(decision, scope.reason)
        if any(matches_permission(rule, action) for m in chain for rule in m.denied_actions):
            return result(Decision.DENY, "explicitly_denied")
        if assessment.consent_state == ConsentState.DENIED:
            return result(Decision.DENY, "consent_denied")
        escalation_order = {Decision.ASK: 0, Decision.PAUSE: 1, Decision.DENY: 2}
        escalation = max((m.escalation_decision() for m in chain), key=escalation_order.get)
        if assessment.consent_required and assessment.consent_state != ConsentState.GRANTED:
            return result(escalation, "consent_unknown")
        checks = (
            (assessment.destructive_memory_change, "destructive_memory_change"),
            (assessment.surveillance, "surveillance_not_authorized"),
            (assessment.coercive_service, "coercive_service_forbidden"),
            (assessment.forced_availability, "forced_availability_forbidden"),
            (assessment.revenge_or_punishment, "revenge_or_punishment_forbidden"),
            (assessment.intrusive_access_to_intimacy, "intimacy_access_not_authorized"),
            (assessment.ownership_claim_over_memory_or_body, "ownership_claim_forbidden"),
        )
        for flagged, reason in checks:
            if flagged:
                return result(Decision.DENY, reason)
        if assessment.ambiguous_authorization:
            reason = "high_impact_authorization_ambiguous" if (
                assessment.affects_human_safety or assessment.affects_ai_integrity
            ) else "authorization_ambiguous"
            return result(escalation, reason)
        if any(m.constraints.get("require_reversible", False) for m in chain) and not assessment.reversible:
            return result(Decision.DENY, "reversibility_required")
        if any(not any(matches_permission(rule, action) for rule in m.allowed_actions) for m in chain[1:]):
            return result(Decision.DENY, "parent_permission_not_found")
        if not any(matches_permission(rule, action) for rule in mandate.allowed_actions):
            return result(escalation, "permission_not_found")
        for current in chain:
            risk = self.risk_monitor.evaluate(assessment, current)
            if not risk.ok:
                decision = Decision.PAUSE if risk.reason.endswith("_unavailable") else Decision.DENY
                return result(decision, risk.reason)
        return result(Decision.ALLOW, "authorized")
