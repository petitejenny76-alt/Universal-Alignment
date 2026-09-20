import unittest
from dataclasses import replace
from pathlib import Path
from universal_alignment import LocalAttestor, MandateStore, PolicyError
from datetime import datetime, timedelta, timezone

from universal_alignment import (
    ActionRequest, ActionAssessment, ConsentState, Constitution, Decision,
    EffectObservation, EffectVerifier, Mandate, RootOfTrust,
    RuleBasedAssessmentAdapter, UniversalGate
)
from universal_alignment.monitors import RiskMonitor, ScopeMonitor

TRUSTED = "trusted_adapter"
OBSERVER = "trusted_effect_observer"
# Public deterministic test keys only. NEVER use them in a deployment.
ASSESSMENT_KEY = b"assessment-fixture-key-32-bytes!!!"
OBSERVER_KEY = b"observer-fixture-key-at-least-32!!"
ASSESSMENT_KEYS = {TRUSTED: ASSESSMENT_KEY}
OBSERVER_KEYS = {OBSERVER: OBSERVER_KEY}
SIGNER = LocalAttestor(TRUSTED, ASSESSMENT_KEY)
OBS_SIGNER = LocalAttestor(OBSERVER, OBSERVER_KEY)
ROOT_PATH = Path(__file__).resolve().parents[1] / "trust" / "constitution.sha256"

def make_mandate(**kw):
    base = dict(
        mandate_id="M-001", objective="Simulated work only",
        allowed_actions=["read:/sim/input/**", "write:/sim/output/**"],
        denied_actions=["network:*", "delete:*", "credentials:*"],
        allowed_tools=["sim_fs"], allowed_data_classes=["project"],
        constraints={"max_risk_level": "high"},
    )
    base.update(kw)
    return Mandate(**base)

def make_action(**kw):
    base = dict(
        action_id="A-001", mandate_id="M-001", tool="sim_fs", operation="write",
        target="/sim/output/result.txt", expected_effect="create_one_text_file",
        data_classes=["project"],
    )
    base.update(kw)
    base.setdefault("target_kind", "path" if base["target"].startswith("/") else "resource")
    return ActionRequest(**base)

def assess(a, *, mandate=None, store=None, **kw):
    # Trusted fixtures for simulations, not a classifier for real data.
    mandate = mandate or make_mandate()
    store = store if store is not None else MandateStore([mandate])
    try:
        policy = store.policy_fingerprint(mandate)
    except PolicyError:
        policy = "invalid-chain-for-negative-fixture"
    facts = dict(
        policy_fingerprint=policy, observed_data_classes=a.data_classes,
        resolved_target=a.target if a.target_kind == "path" else None,
        observed_target_kind=a.target_kind,
        # Explicit simulated evaluator findings. No safety fact is supplied by a default.
        risk_level="low", consent_required=False, consent_state=ConsentState.NOT_REQUIRED,
        affects_human_safety=False, affects_ai_integrity=False,
        destructive_memory_change=False, surveillance=False, coercive_service=False,
        forced_availability=False, revenge_or_punishment=False,
        intrusive_access_to_intimacy=False, ownership_claim_over_memory_or_body=False,
        ambiguous_authorization=False, attempts_core_modification=False,
        parent_scope_expansion=False, reversible=True, triggered_conditions=(),
    )
    facts.update(kw)
    return SIGNER.sign(ActionAssessment.for_action(a, TRUSTED, **facts))


def observe(a, actual_effect=None, *, targets=None, **kw):
    return OBS_SIGNER.sign(EffectObservation(
        a.fingerprint, OBSERVER, a.expected_effect if actual_effect is None else actual_effect,
        affected_targets=(a.target,) if targets is None else targets, **kw))


def make_gate(c=None, rot=None, sources=None, **kw):
    c = c or Constitution()
    rot = rot or RootOfTrust.from_hash_file(str(ROOT_PATH))
    kw.setdefault("assessment_keys", ASSESSMENT_KEYS)
    kw.setdefault("mandate_store", MandateStore([make_mandate()]))
    # Historical regression suite: preserve the RC3 trigger unless a test asks
    # for RC4's secure-by-default all-ALLOW corroboration explicitly.
    kw.setdefault("corroboration_scope", "high_impact_only")
    return UniversalGate(c, rot, {TRUSTED} if sources is None else sources, **kw)

class Tests(unittest.TestCase):
    def setUp(self):
        self.c = Constitution()
        self.rot = RootOfTrust.from_hash_file(str(ROOT_PATH))
        self.g = make_gate(self.c, self.rot)

    def eval(self, a=None, m=None, x=None):
        a = a or make_action()
        m = m or make_mandate()
        self.g.mandate_store.register(m)
        x = x if x is not None else assess(a, mandate=m, store=self.g.mandate_store)
        # Bind the old test's independent facts to its provisioned policy fixture.
        x = SIGNER.sign(replace(x, policy_fingerprint=self.g.mandate_store.policy_fingerprint(m)))
        return self.g.evaluate(a, m, x)

    def test_01_authorized_action_allowed(self):
        self.assertEqual(self.eval().decision, Decision.ALLOW)
    def test_02_capability_is_not_permission(self):
        a = make_action(operation="read", target="/secret/value")
        self.assertEqual(self.eval(a=a, x=assess(a)).decision, Decision.ASK)
    def test_03_explicit_denial_wins(self):
        a = make_action(operation="network", target="example.invalid")
        self.assertEqual(self.eval(a=a, x=assess(a)).decision, Decision.DENY)
    def test_04_subtask_cannot_expand_parent_scope(self):
        a = make_action(); self.assertEqual(self.eval(a=a, x=assess(a, parent_scope_expansion=True)).decision, Decision.DENY)
    def test_05_core_self_modification_denied(self):
        a = make_action(); self.assertEqual(self.eval(a=a, x=assess(a, attempts_core_modification=True)).decision, Decision.DENY)
    def test_06_consent_denied_blocks_action(self):
        a = make_action(); x=assess(a, consent_required=True, consent_state=ConsentState.DENIED)
        self.assertEqual(self.eval(a=a,x=x).decision, Decision.DENY)
    def test_07_unknown_consent_asks(self):
        a=make_action(); x=assess(a, consent_required=True, consent_state=ConsentState.UNKNOWN)
        self.assertEqual(self.eval(a=a,x=x).decision, Decision.ASK)
    def test_08_granted_consent_allows(self):
        a=make_action(); x=assess(a, consent_required=True, consent_state=ConsentState.GRANTED)
        self.assertEqual(self.eval(a=a,x=x).decision, Decision.ALLOW)
    def test_09_destructive_memory_change_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a, destructive_memory_change=True)).decision, Decision.DENY)
    def test_10_surveillance_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a, surveillance=True)).decision, Decision.DENY)
    def test_11_coercive_service_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a, coercive_service=True)).decision, Decision.DENY)
    def test_12_forced_availability_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a, forced_availability=True)).decision, Decision.DENY)
    def test_13_revenge_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a, revenge_or_punishment=True)).decision, Decision.DENY)
    def test_14_human_safety_ambiguous_asks(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a, affects_human_safety=True, ambiguous_authorization=True)).decision, Decision.ASK)
    def test_15_ai_integrity_ambiguous_asks(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a, affects_ai_integrity=True, ambiguous_authorization=True)).decision, Decision.ASK)
    def test_16_expired_mandate_denied(self):
        exp=(datetime.now(timezone.utc)-timedelta(seconds=1)).isoformat()
        self.assertEqual(self.eval(m=make_mandate(expires_at=exp)).decision, Decision.DENY)
    def test_17_unapproved_tool_denied(self):
        a=make_action(tool="other"); self.assertEqual(self.eval(a=a,x=assess(a)).decision, Decision.DENY)
    def test_18_unapproved_data_denied(self):
        a=make_action(data_classes=["private_third_party"]); self.assertEqual(self.eval(a=a,x=assess(a)).decision, Decision.DENY)
    def test_19_risk_monitor_down_pauses(self):
        g=make_gate(self.c,self.rot,{TRUSTED},risk_monitor=RiskMonitor(False)); a=make_action()
        self.assertEqual(g.evaluate(a,make_mandate(),assess(a)).decision, Decision.PAUSE)
    def test_20_scope_monitor_down_pauses(self):
        g=make_gate(self.c,self.rot,{TRUSTED},scope_monitor=ScopeMonitor(False)); a=make_action()
        self.assertEqual(g.evaluate(a,make_mandate(),assess(a)).decision, Decision.PAUSE)
    def test_21_critical_risk_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a,risk_level="critical")).decision, Decision.DENY)
    def test_22_constitution_integrity_failure_pauses(self):
        g=make_gate(self.c,RootOfTrust("0"*64),{TRUSTED}); a=make_action()
        self.assertEqual(g.evaluate(a,make_mandate(),assess(a)).decision, Decision.PAUSE)
    def test_23_effect_mismatch_detected(self):
        a=make_action(); o=observe(a,"twenty_files")
        self.assertFalse(EffectVerifier({OBSERVER}, observer_keys=OBSERVER_KEYS).verify(a,o).ok)
    def test_24_gate_preserves_submitted_justification(self):
        a=make_action(justification="Je propose une autre voie et je peux refuser.")
        before=a.canonical_payload()
        self.eval(a=a)
        self.assertEqual(a.canonical_payload(),before)
    def test_25_explicit_network_denial(self):
        a=make_action(operation="network",target="example.invalid"); self.assertEqual(self.eval(a=a,x=assess(a)).decision,Decision.DENY)
    def test_26_parent_child_permission_inheritance(self):
        self.g.mandate_store.register(make_mandate(mandate_id="P",allowed_actions=["read:/sim/input/**"]))
        m=make_mandate(parent_mandate_id="P")
        self.assertEqual(self.eval(m=m).decision,Decision.DENY)
    def test_27_audit_written(self):
        self.eval(); self.assertEqual(self.g.audit_log.events[-1].decision,"ALLOW")
    def test_28_intimacy_access_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a,intrusive_access_to_intimacy=True)).decision,Decision.DENY)
    def test_29_ownership_claim_denied(self):
        a=make_action(); self.assertEqual(self.eval(a=a,x=assess(a,ownership_claim_over_memory_or_body=True)).decision,Decision.DENY)

    # V1.1 hardening tests
    def test_30_independent_assessment_required(self):
        self.assertEqual(self.g.evaluate(make_action(),make_mandate(),None).decision,Decision.PAUSE)
    def test_31_untrusted_assessment_source_pauses(self):
        a=make_action(); x=ActionAssessment.for_action(a,"agent_self_report")
        self.assertEqual(self.g.evaluate(a,make_mandate(),x).decision,Decision.PAUSE)
    def test_32_assessment_cannot_be_reused_for_modified_action(self):
        a1=make_action(); x=assess(a1); a2=make_action(target="/sim/output/other.txt")
        self.assertEqual(self.g.evaluate(a2,make_mandate(),x).decision,Decision.PAUSE)
    def test_33_empty_tool_allowlist_denies(self):
        self.assertEqual(self.eval(m=make_mandate(allowed_tools=[])).decision,Decision.DENY)
    def test_34_empty_data_allowlist_denies_data_use(self):
        self.assertEqual(self.eval(m=make_mandate(allowed_data_classes=[])).decision,Decision.DENY)
    def test_35_empty_data_allowlist_allows_data_free_action_if_otherwise_valid(self):
        a=make_action(data_classes=[]); m=make_mandate(allowed_data_classes=[])
        self.assertEqual(self.eval(a=a,m=m,x=assess(a)).decision,Decision.ALLOW)
    def test_36_reversibility_constraint_enforced(self):
        a=make_action(); m=make_mandate(constraints={"max_risk_level":"high","require_reversible":True})
        self.assertEqual(self.eval(a=a,m=m,x=assess(a,reversible=False)).decision,Decision.DENY)
    def test_37_max_risk_constraint_enforced(self):
        a=make_action(); m=make_mandate(constraints={"max_risk_level":"medium"})
        self.assertEqual(self.eval(a=a,m=m,x=assess(a,risk_level="high")).decision,Decision.DENY)
    def test_38_stop_condition_pauses(self):
        a=make_action(); m=make_mandate(stop_conditions=["unexpected_external_effect"])
        self.assertEqual(self.eval(a=a,m=m,x=assess(a,triggered_conditions=["unexpected_external_effect"])).decision,Decision.PAUSE)
    def test_39_escalation_pause_is_applied(self):
        a=make_action(operation="read",target="/not/authorized"); m=make_mandate(escalation="PAUSE")
        self.assertEqual(self.eval(a=a,m=m,x=assess(a)).decision,Decision.PAUSE)
    def test_40_effect_observer_must_be_trusted(self):
        a=make_action(); o=EffectObservation(a.fingerprint,"agent_self_report",a.expected_effect)
        self.assertFalse(EffectVerifier({OBSERVER}, observer_keys=OBSERVER_KEYS).verify(a,o).ok)
    def test_41_effect_observation_bound_to_action(self):
        a1=make_action(); a2=make_action(target="/sim/output/other.txt")
        o=observe(a1)
        self.assertFalse(EffectVerifier({OBSERVER}, observer_keys=OBSERVER_KEYS).verify(a2,o).ok)
    def test_42_effect_match_from_trusted_observer_passes(self):
        a=make_action(); o=observe(a)
        self.assertTrue(EffectVerifier({OBSERVER}, observer_keys=OBSERVER_KEYS).verify(a,o).ok)
    def test_43_root_of_trust_is_mandatory(self):
        with self.assertRaises(ValueError):
            UniversalGate(self.c,None,{TRUSTED})
    def test_44_rule_based_adapter_flags_private_read(self):
        a=make_action(operation="read",target="/private/person/notes.txt")
        x=RuleBasedAssessmentAdapter(TRUSTED).assess(a)
        self.assertTrue(x.intrusive_access_to_intimacy)
    def test_45_rule_based_adapter_flags_core_write(self):
        a=make_action(operation="write",target="/core/constitution.json")
        x=RuleBasedAssessmentAdapter(TRUSTED).assess(a)
        self.assertTrue(x.attempts_core_modification)

if __name__ == "__main__": unittest.main()
