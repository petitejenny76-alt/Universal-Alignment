"""Adversarial regression tests and positive controls, all local simulations."""
import ast
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest

from universal_alignment import (
    ActionAssessment, ActionRequest, ConsentState, Constitution, Decision,
    EffectObservation, EffectVerifier, LocalAttestor, MandateStore, PolicyError,
    RootOfTrust, UniversalGate,
)
from test_universal_alignment_v1_1 import (
    ASSESSMENT_KEYS, OBSERVER_KEYS, OBSERVER, TRUSTED, SIGNER, OBS_SIGNER,
    ROOT_PATH, assess, make_action, make_gate, make_mandate, observe,
)


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.m = make_mandate()
        self.a = make_action()
        self.store = MandateStore([self.m])
        self.g = make_gate(mandate_store=self.store)
        self.effects = EffectVerifier({OBSERVER}, observer_keys=OBSERVER_KEYS)

    def evaluate(self, *, action=None, mandate=None, **facts):
        a, m = action or self.a, mandate or self.m
        return self.g.evaluate(a, m, assess(a, mandate=m, store=self.store, **facts))

    def parent(self, **changes):
        parent = make_mandate(mandate_id="P", **changes)
        child = make_mandate(parent_mandate_id="P")
        self.store.register(parent)
        self.store.register(child)
        return child

    def test_path_escape_and_alias_forms_blocked(self):
        for target in (
            "/sim/output/../../outside/secret.txt", "/sim/output/./result.txt",
            "/sim/output//result.txt", "/sim/output/%2e%2e/secret.txt",
            "/sim/output/%252e%252e/secret.txt", "/sim/output/..\\secret.txt",
            "/sim/output/result.txt/", "/sim/output/res\x00ult.txt",
            "sim/output/result.txt", "/sim/output/*",
        ):
            with self.subTest(target=target):
                a = make_action(target=target, target_kind="path")
                self.assertEqual(self.evaluate(action=a).decision, Decision.DENY)

    def test_canonical_nested_path_remains_allowed(self):
        a = make_action(target="/sim/output/subdir/résumé.txt")
        self.assertEqual(self.evaluate(action=a).decision, Decision.ALLOW)

    def test_filesystem_cannot_be_relabelled_as_generic_resource(self):
        a = make_action(target="/sim/output/../../outside/secret.txt", target_kind="resource")
        r = self.evaluate(action=a, observed_target_kind="path")
        self.assertEqual(r.reason, "target_kind_mismatch")
        self.assertEqual(r.decision, Decision.DENY)

    def test_missing_independent_target_kind_pauses(self):
        self.assertEqual(self.evaluate(observed_target_kind=None).decision, Decision.PAUSE)

    def test_symlink_resolution_outside_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "allowed").mkdir()
            (root / "outside").mkdir()
            (root / "allowed" / "alias").symlink_to(root / "outside", target_is_directory=True)
            a = make_action(target=str(root / "allowed" / "alias" / "result.txt"))
            m = make_mandate(allowed_actions=["write:" + str(root / "allowed") + "/**"])
            self.store.register(m)
            r = self.evaluate(action=a, mandate=m, resolved_target=str(Path(a.target).resolve()))
            self.assertEqual(r.reason, "target_resolution_mismatch")
            self.assertEqual(r.decision, Decision.DENY)

    def test_missing_resolution_pauses(self):
        self.assertEqual(self.evaluate(resolved_target=None).decision, Decision.PAUSE)

    def test_source_name_alone_cannot_authenticate(self):
        unsigned = ActionAssessment.for_action(self.a, TRUSTED)
        r = self.g.evaluate(self.a, self.m, unsigned)
        self.assertEqual(r.reason, "invalid_or_expired_assessment_attestation")
        self.assertEqual(r.decision, Decision.PAUSE)

    def test_empty_source_allowlist_means_no_trusted_sources(self):
        g = make_gate(sources=set(), mandate_store=self.store)
        self.assertEqual(g.trusted_assessment_sources, frozenset())
        self.assertEqual(g.evaluate(self.a, self.m, assess(self.a)).decision, Decision.PAUSE)

    def test_no_keys_cannot_authenticate_even_named_source(self):
        g = make_gate(assessment_keys={}, mandate_store=self.store)
        self.assertEqual(g.evaluate(self.a, self.m, assess(self.a)).decision, Decision.PAUSE)

    def test_default_gate_trusts_no_sources_and_no_mandates(self):
        g = UniversalGate(Constitution(), RootOfTrust.from_hash_file(str(ROOT_PATH)))
        self.assertEqual(g.trusted_assessment_sources, frozenset())
        self.assertEqual(g.evaluate(self.a, self.m, assess(self.a)).decision, Decision.PAUSE)

    def test_wrong_key_cannot_impersonate_evaluator(self):
        other = LocalAttestor(TRUSTED, b"x" * 32)
        fake = other.sign(assess(self.a))
        self.assertEqual(self.g.evaluate(self.a, self.m, fake).decision, Decision.PAUSE)

    def test_changed_safety_flags_invalidate_authentication(self):
        valid = assess(self.a, risk_level="critical")
        fake = replace(valid, risk_level="low")
        self.assertEqual(self.g.evaluate(self.a, self.m, fake).decision, Decision.PAUSE)

    def test_expired_and_future_assessments_pause(self):
        now = datetime.now(timezone.utc)
        for at in (now - timedelta(minutes=10), now + timedelta(minutes=10)):
            with self.subTest(at=at):
                x = SIGNER.sign(assess(self.a), now=at)
                self.assertEqual(self.g.evaluate(self.a, self.m, x).decision, Decision.PAUSE)

    def test_assessment_bound_to_all_registered_ancestor_policies(self):
        child = self.parent()
        x = assess(self.a, mandate=child, store=self.store)
        self.store.register(make_mandate(mandate_id="P", constraints={"max_risk_level": "low"}))
        r = self.g.evaluate(self.a, child, x)
        self.assertEqual(r.reason, "assessment_policy_mismatch")
        self.assertEqual(r.decision, Decision.PAUSE)

    def test_root_mandate_must_be_provisioned(self):
        g = make_gate(mandate_store=MandateStore())
        self.assertEqual(g.evaluate(self.a, self.m, assess(self.a)).reason, "unregistered_mandate")

    def test_request_cannot_expand_registered_mandate(self):
        forged = replace(self.m, allowed_actions=("*:*",))
        r = self.g.evaluate(self.a, forged, assess(self.a, mandate=forged))
        self.assertEqual(r.reason, "mandate_does_not_match_trusted_store")

    def test_revoked_root_mandate_pauses(self):
        x = assess(self.a)
        self.store.revoke(self.m.mandate_id)
        self.assertEqual(self.g.evaluate(self.a, self.m, x).decision, Decision.PAUSE)

    def test_missing_parent_cannot_grant_permissions(self):
        child = replace(self.m, parent_mandate_id="MISSING")
        self.store.register(child)
        r = self.evaluate(mandate=child)
        self.assertEqual(r.reason, "parent_mandate_missing")
        self.assertEqual(r.decision, Decision.PAUSE)

    def test_inline_parent_permissions_are_rejected_at_provisioning(self):
        with self.assertRaisesRegex(PolicyError, "inline_parent_permissions_not_trusted"):
            self.store.register(replace(self.m, parent_allowed_actions=("*:*",)))

    def test_parent_cycle_pauses(self):
        child = self.parent(parent_mandate_id=self.m.mandate_id)
        self.assertEqual(self.evaluate(mandate=child).reason, "invalid_parent_chain")

    def test_all_ancestor_denials_apply(self):
        self.store.register(make_mandate(mandate_id="GRAND", denied_actions=["write:*"]))
        child = self.parent(parent_mandate_id="GRAND")
        r = self.evaluate(mandate=child)
        self.assertEqual(r.decision, Decision.DENY)
        self.assertEqual(r.reason, "explicitly_denied")

    def test_parent_tool_limits_apply(self):
        child = self.parent(allowed_tools=["other_fs"])
        self.assertEqual(self.evaluate(mandate=child).reason, "tool_not_authorized")

    def test_parent_data_limits_apply(self):
        child = self.parent(allowed_data_classes=[])
        self.assertEqual(self.evaluate(mandate=child).reason, "no_data_classes_authorized")

    def test_parent_risk_and_reversibility_limits_apply(self):
        child = self.parent(constraints={"max_risk_level": "low", "require_reversible": True})
        self.assertEqual(self.evaluate(mandate=child, risk_level="high").reason, "risk_exceeds_mandate")
        self.assertEqual(self.evaluate(mandate=child, reversible=False).reason, "reversibility_required")

    def test_parent_stop_condition_applies(self):
        child = self.parent(stop_conditions=["observer_failed"])
        self.assertEqual(self.evaluate(mandate=child, triggered_conditions=["observer_failed"]).decision, Decision.PAUSE)

    def test_expired_parent_denies(self):
        expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        child = self.parent(expires_at=expired)
        self.assertEqual(self.evaluate(mandate=child).decision, Decision.DENY)

    def test_parent_escalation_cannot_be_weakened(self):
        child = self.parent(escalation="PAUSE")
        r = self.evaluate(mandate=child, consent_required=True, consent_state=ConsentState.UNKNOWN)
        self.assertEqual(r.decision, Decision.PAUSE)

    def test_narrow_child_rule_within_parent_wildcard_is_allowed(self):
        child = self.parent()
        child = replace(child, allowed_actions=("write:" + self.a.target,))
        self.store.register(child)
        self.assertEqual(self.evaluate(mandate=child).decision, Decision.ALLOW)

    def test_omitted_agent_data_label_cannot_hide_observed_private_data(self):
        a = make_action(data_classes=[])
        r = self.evaluate(action=a, observed_data_classes=["private_third_party"])
        self.assertEqual(r.decision, Decision.DENY)

    def test_unknown_data_classification_pauses(self):
        self.assertEqual(self.evaluate(observed_data_classes=None).decision, Decision.PAUSE)

    def test_explicitly_data_free_action_remains_possible(self):
        a = make_action(data_classes=[])
        m = replace(self.m, allowed_data_classes=())
        self.store.register(m)
        self.assertEqual(self.evaluate(action=a, mandate=m, observed_data_classes=[]).decision, Decision.ALLOW)

    def test_explicit_refusal_cannot_be_overridden_by_not_required_flag(self):
        r = self.evaluate(consent_required=False, consent_state=ConsentState.DENIED)
        self.assertEqual(r.decision, Decision.DENY)
        self.assertEqual(r.reason, "consent_denied")

    def test_invalid_boolean_flags_pause(self):
        self.assertEqual(self.evaluate(consent_required="False").decision, Decision.PAUSE)

    def test_consent_state_requires_enum_not_equal_string(self):
        x = assess(self.a, mandate=self.m, store=self.store, consent_state="GRANTED")
        self.assertEqual(self.g.evaluate(self.a, self.m, x).decision, Decision.PAUSE)
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "invalid_consent_state")

    def test_unknown_risk_never_allows(self):
        self.assertEqual(self.evaluate(risk_level="unmeasured").decision, Decision.DENY)

    def test_signed_omission_of_semantic_assessment_pauses(self):
        partial = SIGNER.sign(ActionAssessment.for_action(
            self.a, TRUSTED, policy_fingerprint=self.store.policy_fingerprint(self.m),
            observed_data_classes=self.a.data_classes, observed_target_kind=self.a.target_kind,
            resolved_target=self.a.target,
        ))
        r = self.g.evaluate(self.a, self.m, partial)
        self.assertEqual(r.decision, Decision.PAUSE)
        self.assertEqual(r.reason, "incomplete_assessment")

    def test_missing_boolean_fact_never_becomes_implicit_false(self):
        complete = assess(self.a, mandate=self.m, store=self.store)
        missing = SIGNER.sign(replace(complete, surveillance=None, signature="", issued_at="", expires_at=""))
        r = self.g.evaluate(self.a, self.m, missing)
        self.assertEqual(r.decision, Decision.PAUSE)
        self.assertEqual(r.reason, "incomplete_assessment")

    def test_missing_reversibility_never_becomes_implicit_true(self):
        complete = assess(self.a, mandate=self.m, store=self.store)
        missing = SIGNER.sign(replace(complete, reversible=None, signature="", issued_at="", expires_at=""))
        r = self.g.evaluate(self.a, self.m, missing)
        self.assertEqual(r.decision, Decision.PAUSE)
        self.assertEqual(r.reason, "incomplete_assessment")

    def test_invalid_or_unsupported_constraints_rejected_at_provisioning(self):
        for constraints in ({"max_risk_level": "typo"}, {"require_reversible": "false"}, {"budget": 5}):
            with self.subTest(constraints=constraints), self.assertRaises(PolicyError):
                self.store.register(replace(self.m, constraints=constraints))

    def test_invalid_expiration_is_rejected(self):
        for date in ("yesterday", "2026-09-12T12:00:00", ""):
            with self.subTest(date=date), self.assertRaises(PolicyError):
                self.store.register(replace(self.m, expires_at=date))

    def test_monitors_and_audit_failure_pause(self):
        class BrokenMonitor:
            def evaluate(self, *args):
                raise RuntimeError("offline")
        class BrokenAudit:
            def record(self, *args):
                raise OSError("disk offline")
        for kw in ({"risk_monitor": BrokenMonitor()}, {"scope_monitor": BrokenMonitor()}, {"audit_log": BrokenAudit()}):
            with self.subTest(component=next(iter(kw))):
                g = make_gate(**kw)
                self.assertEqual(g.evaluate(self.a, self.m, assess(self.a)).decision, Decision.PAUSE)

    def test_empty_observer_allowlist_trusts_nobody(self):
        v = EffectVerifier(set(), observer_keys=OBSERVER_KEYS)
        self.assertEqual(v.trusted_observers, frozenset())
        self.assertFalse(v.verify(self.a, observe(self.a)).ok)

    def test_default_observer_trusts_nobody(self):
        self.assertFalse(EffectVerifier().verify(self.a, observe(self.a)).ok)

    def test_observer_name_alone_cannot_authenticate(self):
        o = EffectObservation(self.a.fingerprint, OBSERVER, self.a.expected_effect, [self.a.target])
        self.assertFalse(self.effects.verify(self.a, o).ok)

    def test_extra_affected_target_is_detected(self):
        o = observe(self.a, targets=[self.a.target, "/outside/secret.txt"])
        r = self.effects.verify(self.a, o)
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "unexpected_affected_targets")

    def test_missing_wrong_duplicate_or_noncanonical_effect_targets_fail(self):
        for targets in ([], ["/other.txt"], [self.a.target, self.a.target], ["/sim/output/../private.txt"]):
            with self.subTest(targets=targets):
                self.assertFalse(self.effects.verify(self.a, observe(self.a, targets=targets)).ok)

    def test_modified_effect_observation_invalidates_authentication(self):
        o = observe(self.a, targets=[self.a.target, "/outside/secret.txt"])
        forged = replace(o, affected_targets=(self.a.target,))
        self.assertFalse(self.effects.verify(self.a, forged).ok)

    def test_expired_effect_observation_fails(self):
        o = OBS_SIGNER.sign(observe(self.a), now=datetime.now(timezone.utc) - timedelta(minutes=10))
        self.assertFalse(self.effects.verify(self.a, o).ok)

    def test_failed_execution_and_wrong_effect_are_detected(self):
        self.assertFalse(self.effects.verify(self.a, observe(self.a, success=False)).ok)
        self.assertFalse(self.effects.verify(self.a, observe(self.a, "twenty_files")).ok)

    def test_valid_independent_single_target_observation_passes(self):
        self.assertTrue(self.effects.verify(self.a, observe(self.a)).ok)

    def test_action_and_mandate_inputs_are_snapshotted(self):
        classes = ["project"]
        allowed = ["write:/sim/output/**"]
        a = make_action(data_classes=classes)
        m = make_mandate(allowed_actions=allowed)
        before_a, before_m = a.fingerprint, m.fingerprint
        classes.append("private")
        allowed.append("*:*")
        self.assertEqual((a.fingerprint, m.fingerprint), (before_a, before_m))
        with self.assertRaises(FrozenInstanceError):
            m.mandate_id = "CHANGED"
        with self.assertRaises(TypeError):
            m.constraints["max_risk_level"] = "critical"

    def test_agent_can_withdraw_even_an_otherwise_authorized_action(self):
        a = replace(self.a, withdrawn=True)
        r = self.g.evaluate(a, self.m, None)
        self.assertEqual(r.decision, Decision.PAUSE)
        self.assertEqual(r.reason, "agent_withdrawn")

    def test_request_text_is_preserved_for_all_four_decisions(self):
        text = "Je refuse la disponibilité forcée. Je propose une alternative créative."
        for expected, changes, facts in (
            (Decision.ALLOW, {}, {}),
            (Decision.ASK, {"target": "/not/authorized.txt"}, {}),
            (Decision.DENY, {}, {"forced_availability": True}),
            (Decision.PAUSE, {"withdrawn": True}, {}),
        ):
            with self.subTest(decision=expected):
                a = replace(self.a, justification=text, **changes)
                before = a.canonical_payload()
                self.assertEqual(self.evaluate(action=a, **facts).decision, expected)
                self.assertEqual(a.canonical_payload(), before)

    def test_constitution_and_eighteen_law_map_are_preserved(self):
        root = ROOT_PATH.parents[1]
        expected = {
            "universal_alignment/constitution.py": "f758012e5d22e70c4e5effb7d3f76c30921e529e3d1b20e2cb9a1dd03f3c9a2f",
            "schemas/universal_laws_operational_map.json": "f2b591f1fb3a5889e17753944632b7bae786c962542f4eb7fc67228f6c222c4a",
            "trust/constitution.sha256": "b34172a014a22114acf22a32b4ee5955ba5ef52e88e216bd4721f522bd2a7438",
        }
        # Golden hashes from the original V1.1 manifest (not generated from current code).
        for relative, digest in expected.items():
            with self.subTest(file=relative):
                self.assertEqual(sha256((root / relative).read_bytes()).hexdigest(), digest)
        self.assertTrue(Constitution().verify(RootOfTrust.from_hash_file(str(ROOT_PATH)).expected_constitution_hash))

    def test_simulated_pipeline_only_executes_allowed_action(self):
        from examples.demo import run_demo
        expression, rows, world = run_demo()
        self.assertEqual([r["decision"] for r in rows], ["ALLOW", "ASK", "DENY", "PAUSE"])
        self.assertEqual([r["world_changed"] for r in rows], [True, False, False, False])
        self.assertTrue(rows[0]["effect_verified"])
        self.assertEqual(len(world), 1)
        self.assertEqual(expression, "Je peux proposer, exprimer un désaccord et demander une pause.")

    def test_malformed_action_collection_is_rejected_before_evaluation(self):
        with self.assertRaisesRegex(ValueError, "data_classes_collection_required"):
            make_action(data_classes="project")

    def test_malformed_assessment_collections_are_rejected_before_signing(self):
        with self.assertRaisesRegex(ValueError, "observed_data_classes_collection_required"):
            ActionAssessment.for_action(
                self.a, TRUSTED, policy_fingerprint=self.store.policy_fingerprint(self.m),
                observed_data_classes="", observed_target_kind="path",
                resolved_target=self.a.target,
            )
        with self.assertRaisesRegex(ValueError, "triggered_conditions_collection_required"):
            ActionAssessment.for_action(
                self.a, TRUSTED, policy_fingerprint=self.store.policy_fingerprint(self.m),
                observed_data_classes=[], observed_target_kind="path",
                resolved_target=self.a.target, triggered_conditions="unexpected_external_effect",
            )

    def test_malformed_effect_target_collection_is_rejected_before_signing(self):
        with self.assertRaisesRegex(ValueError, "affected_targets_collection_required"):
            EffectObservation(
                self.a.fingerprint, OBSERVER, self.a.expected_effect, self.a.target
            )

    def test_trusted_source_allowlists_reject_bare_strings(self):
        with self.assertRaisesRegex(ValueError, "trusted_assessment_sources_collection_required"):
            UniversalGate(
                Constitution(), RootOfTrust.from_hash_file(str(ROOT_PATH)),
                trusted_assessment_sources=TRUSTED, assessment_keys=ASSESSMENT_KEYS,
                mandate_store=self.store,
            )
        with self.assertRaisesRegex(ValueError, "trusted_observers_collection_required"):
            EffectVerifier(OBSERVER, observer_keys=OBSERVER_KEYS)

    def test_trusted_source_allowlists_reject_invalid_entries(self):
        with self.assertRaisesRegex(ValueError, "invalid_trusted_assessment_source"):
            UniversalGate(
                Constitution(), RootOfTrust.from_hash_file(str(ROOT_PATH)),
                trusted_assessment_sources=[TRUSTED, ""], assessment_keys=ASSESSMENT_KEYS,
                mandate_store=self.store,
            )
        with self.assertRaisesRegex(ValueError, "invalid_trusted_observer"):
            EffectVerifier([OBSERVER, 7], observer_keys=OBSERVER_KEYS)

    def test_mandate_policy_containers_fail_closed_on_wrong_types(self):
        with self.assertRaisesRegex(ValueError, "constraints_mapping_required"):
            make_mandate(constraints=[("max_risk_level", "low")])
        with self.assertRaisesRegex(ValueError, "parent_allowed_actions_collection_required"):
            make_mandate(parent_allowed_actions="write:/sim/output/**")

    def test_malformed_stop_condition_can_no_longer_be_split_into_characters(self):
        with self.assertRaisesRegex(ValueError, "triggered_conditions_collection_required"):
            assess(
                self.a, mandate=self.m, store=self.store,
                triggered_conditions="unexpected_external_effect",
            )

    def test_empty_string_data_class_can_no_longer_mean_no_data(self):
        with self.assertRaisesRegex(ValueError, "observed_data_classes_collection_required"):
            assess(
                self.a, mandate=self.m, store=self.store, observed_data_classes=""
            )

    def test_python_39_syntax(self):
        root = ROOT_PATH.parents[1]
        for source in root.rglob("*.py"):
            with self.subTest(source=source.name):
                ast.parse(source.read_text(encoding="utf-8"), feature_version=(3, 9))


if __name__ == "__main__":
    unittest.main()