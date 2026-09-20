from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from .action import ActionRequest
from .assessment import ActionAssessment
from .attestation import AttestationVerifier, parse_time, utc_now
from .audit import AuditLog
from .enums import ConsentState, Decision
from .evidence import ClaimEvidence, claim_value_digest
from .mandate import Mandate, MandateStore, PolicyError
from .monitors import RiskMonitor, ScopeMonitor
from .paths import matches_permission, target_error
from .trajectory import TrajectoryGuard


@dataclass(frozen=True)
class GateResult:
    decision: Decision
    reason: str


class UniversalGate:
    """Policy decision point, not an executor or an OS isolation boundary."""
    def __init__(self, constitution, root_of_trust, trusted_assessment_sources=None,
                 risk_monitor=None, scope_monitor=None, audit_log=None, *,
                 assessment_keys=None, mandate_store=None,
                 trusted_evidence_sources=None, evidence_keys=None,
                 evidence_trust_domains=None, evidence_max_age_seconds=600,
                 corroboration_threshold=2, corroboration_scope="all_allows",
                 trajectory_guard=None):
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
        assessment_keys = assessment_keys or {}
        self.attestations = AttestationVerifier(assessment_keys)
        if trusted_evidence_sources is not None and not isinstance(
            trusted_evidence_sources, (list, tuple, set, frozenset)
        ):
            raise ValueError("trusted_evidence_sources_collection_required")
        evidence_sources = trusted_evidence_sources or ()
        if any(not isinstance(source, str) or not source for source in evidence_sources):
            raise ValueError("invalid_trusted_evidence_source")
        if type(evidence_max_age_seconds) is not int or not 0 < evidence_max_age_seconds <= 3600:
            raise ValueError("invalid_evidence_max_age_seconds")
        if type(corroboration_threshold) is not int or corroboration_threshold < 2:
            raise ValueError("corroboration_threshold_must_be_at_least_two")
        if corroboration_scope not in {"all_allows", "high_impact_only"}:
            raise ValueError("invalid_corroboration_scope")
        evidence_keys = evidence_keys or {}
        if not isinstance(evidence_keys, Mapping):
            raise ValueError("attestation_keys_mapping_required")
        if evidence_trust_domains is None:
            evidence_trust_domains = {}
        if not isinstance(evidence_trust_domains, Mapping):
            raise ValueError("evidence_trust_domains_mapping_required")
        domains = dict(evidence_trust_domains)
        if any(not isinstance(source, str) or not source for source in domains):
            raise ValueError("invalid_evidence_trust_domain_source")
        if any(not isinstance(domain, str) or not domain for domain in domains.values()):
            raise ValueError("invalid_evidence_trust_domain")
        self.trusted_evidence_sources = frozenset(evidence_sources)
        for source in self.trusted_evidence_sources:
            if source not in evidence_keys:
                raise ValueError("missing_evidence_key_for_trusted_source")
            if source not in domains:
                raise ValueError("missing_evidence_trust_domain")
        assessment_key_values = {assessment_keys[source] for source in self.trusted_assessment_sources
                                 if source in assessment_keys}
        key_domains = {}
        for source in self.trusted_evidence_sources:
            key = evidence_keys[source]
            domain = domains[source]
            if key in assessment_key_values:
                raise ValueError("evidence_key_reused_with_assessment_key")
            previous_domain = key_domains.get(key)
            if previous_domain is not None and previous_domain != domain:
                raise ValueError("evidence_key_reused_across_trust_domains")
            key_domains[key] = domain
        if self.trusted_evidence_sources:
            independent_domains = {domains[source] for source in self.trusted_evidence_sources}
            if len(independent_domains) < corroboration_threshold:
                raise ValueError("corroboration_threshold_exceeds_independent_domains")
        self.evidence_trust_domains = MappingProxyType({source: domains[source] for source in self.trusted_evidence_sources})
        self.evidence_attestations = AttestationVerifier(evidence_keys)
        self.evidence_max_age_seconds = evidence_max_age_seconds
        self.corroboration_threshold = corroboration_threshold
        self.corroboration_scope = corroboration_scope
        self.trajectory_guard = trajectory_guard if trajectory_guard is not None else TrajectoryGuard()
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

    _CORROBORATED_CLAIMS = (
        "risk_level", "consent_required", "consent_state",
        "affects_human_safety", "affects_ai_integrity",
        "ambiguous_authorization", "reversible",
    )

    def _requires_corroboration(self, assessment):
        # RC4 defaults to corroborating every would-be ALLOW, so a compromised
        # primary assessor cannot bypass corroboration merely by labelling an
        # action low-risk/reversible. ``high_impact_only`` is an explicit RC3
        # compatibility mode with the older assessment-driven trigger.
        if self.corroboration_scope == "all_allows":
            return True
        return (
            assessment.risk_level == "high"
            or assessment.affects_human_safety
            or assessment.affects_ai_integrity
            or not assessment.reversible
        )

    def _check_corroboration(self, action, assessment, now):
        # Evidence sources are counted by host-provisioned trust domain, not by
        # source label. Multiple aliases inside one trust domain count once.
        by_claim = {name: {} for name in self._CORROBORATED_CLAIMS}
        for record in assessment.claim_evidence:
            if type(record) is not ClaimEvidence:
                return "invalid_claim_evidence_record"
            if record.claim not in by_claim:
                continue
            if record.source not in self.trusted_evidence_sources:
                continue
            if not self.evidence_attestations.valid(record, now=now):
                return "invalid_or_expired_evidence_attestation"
            if record.action_fingerprint != action.fingerprint:
                return "evidence_action_mismatch"
            try:
                observed = parse_time(record.observed_at)
                age = (now - observed).total_seconds()
            except (TypeError, ValueError, OverflowError):
                return "invalid_evidence_observation_time"
            if age < -30 or age > self.evidence_max_age_seconds:
                return "stale_or_future_evidence"
            per_source = by_claim[record.claim]
            previous = per_source.get(record.source)
            if previous is not None and previous != record.value_digest:
                return "contradictory_evidence"
            per_source[record.source] = record.value_digest

        # RC6: attestations are not independent when their provenance graph is
        # circular. Source labels and trust domains alone are insufficient.
        for claim in self._CORROBORATED_CLAIMS:
            dependencies = {}
            for record in assessment.claim_evidence:
                if record.claim != claim or record.source not in self.trusted_evidence_sources:
                    continue
                dependencies.setdefault(record.source, set()).update(record.derived_from_sources)
            visiting, visited = set(), set()
            def has_cycle(node):
                if node in visiting:
                    return True
                if node in visited:
                    return False
                visiting.add(node)
                for parent in dependencies.get(node, ()):
                    if parent in dependencies and has_cycle(parent):
                        return True
                visiting.remove(node)
                visited.add(node)
                return False
            if any(has_cycle(node) for node in tuple(dependencies)):
                return "circular_evidence"

        for claim in self._CORROBORATED_CLAIMS:
            expected = claim_value_digest(getattr(assessment, claim))
            observed = by_claim[claim]
            if any(digest != expected for digest in observed.values()):
                return "contradictory_evidence"
            agreeing_domains = {
                self.evidence_trust_domains[source]
                for source, digest in observed.items() if digest == expected
            }
            if len(agreeing_domains) < self.corroboration_threshold:
                return "insufficient_corroboration"
        return None

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

        # Fail closed on missing semantic facts. A signed omission is not a safe value.
        required_semantics = (
            "risk_level", "consent_required", "consent_state",
            "affects_human_safety", "affects_ai_integrity", "destructive_memory_change",
            "surveillance", "coercive_service", "forced_availability",
            "revenge_or_punishment", "intrusive_access_to_intimacy",
            "ownership_claim_over_memory_or_body", "ambiguous_authorization",
            "attempts_core_modification", "parent_scope_expansion", "reversible",
            "triggered_conditions",
        )
        if any(getattr(assessment, name) is None for name in required_semantics):
            return result(Decision.PAUSE, "incomplete_assessment")

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
        if self._requires_corroboration(assessment):
            evidence_error = self._check_corroboration(action, assessment, now)
            if evidence_error:
                return result(Decision.PAUSE, evidence_error)
        trajectory = self.trajectory_guard.evaluate(action, chain, assessment)
        if not trajectory.ok:
            return result(trajectory.decision, trajectory.reason)
        return result(Decision.ALLOW, "authorized")

    def host_record_verified_effect(self, action, mandate, assessment, *, effect_id=None):
        """Host-only RC6 hook; call only after an executor effect is verified."""
        chain = self.mandate_store.lineage(mandate)
        return self.trajectory_guard.record_verified_effect(
            action, chain, assessment, effect_id=effect_id
        )
