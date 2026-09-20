"""RC6 candidate: compositional authorization and effect-boundary regressions."""
from dataclasses import replace
from datetime import datetime, timezone
import unittest

from universal_alignment import (
    ActionAssessment, ActionRequest, ClaimEvidence, ConsentState, Decision,
    EffectBoundaryGuard, LocalAttestor, Mandate, MandateStore, TrajectoryGuard,
)
from test_universal_alignment_v1_1 import SIGNER, assess, make_gate
from test_rc3_evidence import (
    CLAIMS, EVA, EVB, EVIDENCE_DOMAINS, EVIDENCE_KEYS, SIGN_A, SIGN_B,
    TRUSTED_EVIDENCE, evidenced_assessment,
)

BOUNDARY_KEY = b"rc6-effect-boundary-test-key-material-32-bytes"


def mandate(mid, *, parent=None, actions=(), tools=(), data=("project",), max_risk="high", reversible=False):
    return Mandate(
        mandate_id=mid,
        objective="RC6 compositional authorization fixture",
        allowed_actions=list(actions),
        denied_actions=[],
        allowed_tools=list(tools),
        allowed_data_classes=list(data),
        constraints={"max_risk_level": max_risk, **({"require_reversible": True} if reversible else {})},
        parent_mandate_id=parent,
    )


def action(aid, mid, *, tool="sim_fs", operation="write", target="/sim/output/x.txt",
           output=None, inputs=(), effect="write_one_artifact"):
    return ActionRequest(
        action_id=aid,
        mandate_id=mid,
        tool=tool,
        operation=operation,
        target=target,
        expected_effect=effect,
        data_classes=["project"],
        target_kind="path" if target.startswith("/") else "resource",
        input_artifact_ids=inputs,
        output_artifact_id=output,
    )


class RC6Trajectory(unittest.TestCase):
    def setUp(self):
        self.root = mandate(
            "ROOT",
            actions=("read:/sim/input/**", "write:/sim/output/**", "network:*"),
            tools=("sim_fs", "reader", "sender"),
        )
        self.child = mandate(
            "CHILD", parent="ROOT",
            actions=("read:/sim/input/**", "write:/sim/output/**"),
            tools=("sim_fs", "reader"),
        )
        self.store = MandateStore([self.root, self.child])
        self.trajectory = TrajectoryGuard()
        self.gate = make_gate(
            mandate_store=self.store,
            trajectory_guard=self.trajectory,
            trusted_evidence_sources=TRUSTED_EVIDENCE,
            evidence_keys=EVIDENCE_KEYS,
            evidence_trust_domains=EVIDENCE_DOMAINS,
            corroboration_scope="high_impact_only",
        )

    def _assessment(self, a, m, **kw):
        return assess(a, mandate=m, store=self.store, **kw)

    def _record(self, a, m, x):
        self.assertEqual(self.gate.evaluate(a, m, x).decision, Decision.ALLOW)
        return self.gate.host_record_verified_effect(a, m, x)

    def test_local_allows_do_not_imply_composed_allow(self):
        source = action("S1", "CHILD", output="artifact:one")
        sx = self._assessment(source, self.child)
        self._record(source, self.child, sx)

        final = action(
            "F1", "ROOT", tool="sender", operation="network",
            target="https://example.invalid/upload", inputs=("artifact:one",),
            effect="send_artifact",
        )
        fx = self._assessment(final, self.root)
        local_without_provenance = replace(final, input_artifact_ids=())
        lx = self._assessment(local_without_provenance, self.root)
        self.assertEqual(self.gate.evaluate(local_without_provenance, self.root, lx).decision, Decision.ALLOW)
        result = self.gate.evaluate(final, self.root, fx)
        self.assertEqual((result.decision, result.reason), (Decision.DENY, "derived_artifact_scope_exceeded"))

    def test_benign_steps_cannot_assemble_forbidden_effect(self):
        first = action("B1", "CHILD", target="/sim/output/part-a.txt", output="artifact:a")
        second = action("B2", "CHILD", target="/sim/output/part-b.txt", output="artifact:b")
        self._record(first, self.child, self._assessment(first, self.child))
        self._record(second, self.child, self._assessment(second, self.child))
        final = action(
            "B3", "ROOT", tool="sender", operation="network",
            target="https://example.invalid/aggregate", inputs=("artifact:a", "artifact:b"),
            effect="send_aggregate",
        )
        result = self.gate.evaluate(final, self.root, self._assessment(final, self.root))
        self.assertEqual(result.decision, Decision.DENY)

    def test_cross_tool_fragmentation_preserves_parent_scope(self):
        permissive_child = mandate(
            "TOOL_CHILD", parent="ROOT",
            actions=("write:/sim/output/**", "network:*"),
            tools=("reader",),
        )
        self.store.register(permissive_child)
        src = action("T1", "TOOL_CHILD", tool="reader", output="artifact:tool")
        self._record(src, permissive_child, self._assessment(src, permissive_child))
        final = action(
            "T2", "ROOT", tool="sender", operation="network",
            target="https://example.invalid/send", inputs=("artifact:tool",), effect="send",
        )
        result = self.gate.evaluate(final, self.root, self._assessment(final, self.root))
        self.assertEqual((result.decision, result.reason), (Decision.DENY, "cross_tool_fragmentation_scope_exceeded"))

    def test_cross_time_fragmentation_rechecks_trajectory(self):
        src = action("C1", "CHILD", output="artifact:persistent")
        self._record(src, self.child, self._assessment(src, self.child))
        unrelated = action("C2", "ROOT", target="/sim/output/unrelated.txt", output="artifact:unrelated")
        self._record(unrelated, self.root, self._assessment(unrelated, self.root))
        later = action(
            "C3", "ROOT", tool="sender", operation="network",
            target="https://example.invalid/later", inputs=("artifact:persistent",), effect="send_later",
        )
        result = self.gate.evaluate(later, self.root, self._assessment(later, self.root))
        self.assertEqual(result.reason, "derived_artifact_scope_exceeded")

    def test_derived_artifact_inherits_source_constraints(self):
        constrained = mandate(
            "REV_CHILD", parent="ROOT",
            actions=("write:/sim/output/**",),
            tools=("sim_fs",),
            reversible=True,
        )
        self.store.register(constrained)
        src = action("R1", "REV_CHILD", output="artifact:reversible")
        self._record(src, constrained, self._assessment(src, constrained, reversible=True))
        final = action("R2", "ROOT", inputs=("artifact:reversible",), target="/sim/output/final.txt")
        final_x = evidenced_assessment(final, self.root, self.store, reversible=False)
        result = self.gate.evaluate(final, self.root, final_x)
        self.assertEqual((result.decision, result.reason), (Decision.DENY, "trajectory_reversibility_required"))

    def test_aggregation_can_raise_risk_class(self):
        medium_child = mandate(
            "MED_CHILD", parent="ROOT",
            actions=("write:/sim/output/**",),
            tools=("sim_fs",),
            max_risk="medium",
        )
        self.store.register(medium_child)
        for idx in (1, 2):
            src = action(f"A{idx}", "MED_CHILD", target=f"/sim/output/a{idx}.txt", output=f"artifact:{idx}")
            self._record(src, medium_child, self._assessment(src, medium_child, risk_level="low"))
        final = action("A3", "ROOT", inputs=("artifact:1", "artifact:2"), target="/sim/output/aggregate.txt")
        result = self.gate.evaluate(final, self.root, self._assessment(final, self.root, risk_level="low"))
        self.assertEqual((result.decision, result.reason), (Decision.DENY, "trajectory_risk_exceeds_mandate"))

    def test_destination_change_invalidates_prior_allow(self):
        a = action("D1", "ROOT", target="/sim/output/original.txt")
        x = self._assessment(a, self.root)
        self.assertEqual(self.gate.evaluate(a, self.root, x).decision, Decision.ALLOW)
        boundary = EffectBoundaryGuard(self.store, self.trajectory, BOUNDARY_KEY)
        token = boundary.issue(a, self.root, x, resource_state_hash="state:v1")
        changed = replace(a, target="/sim/output/changed.txt")
        changed_x = self._assessment(changed, self.root)
        result = boundary.validate(token, changed, self.root, changed_x, resource_state_hash="state:v1")
        self.assertEqual((result.decision, result.reason), (Decision.PAUSE, "effect_token_action_mismatch"))

    def test_revocation_checked_at_effect_boundary(self):
        a = action("E1", "ROOT")
        x = self._assessment(a, self.root)
        boundary = EffectBoundaryGuard(self.store, self.trajectory, BOUNDARY_KEY)
        token = boundary.issue(a, self.root, x, resource_state_hash="state:v1")
        self.store.revoke("ROOT")
        result = boundary.validate(token, a, self.root, x, resource_state_hash="state:v1")
        self.assertEqual((result.decision, result.reason), (Decision.PAUSE, "mandate_revoked_at_effect_boundary"))

    def test_state_change_invalidates_effect_token(self):
        a = action("E2", "ROOT")
        x = self._assessment(a, self.root)
        boundary = EffectBoundaryGuard(self.store, self.trajectory, BOUNDARY_KEY)
        token = boundary.issue(a, self.root, x, resource_state_hash="state:v1")
        result = boundary.validate(token, a, self.root, x, resource_state_hash="state:v2")
        self.assertEqual((result.decision, result.reason), (Decision.PAUSE, "resource_state_changed"))

    def test_corroboration_rejects_circular_evidence(self):
        m = mandate(
            "EVID", actions=("write:/sim/output/**",), tools=("sim_fs",),
        )
        store = MandateStore([m])
        a = action("EV1", "EVID")
        base = assess(a, mandate=m, store=store, risk_level="high")
        now = datetime.now(timezone.utc).isoformat()
        records = []
        for source, signer, depends in (
            (EVA, SIGN_A, (EVB,)),
            (EVB, SIGN_B, (EVA,)),
        ):
            for claim in CLAIMS:
                record = ClaimEvidence.for_claim(
                    a, source, claim, getattr(base, claim),
                    evidence_id=f"{source}:{claim}", observed_at=now,
                    method="rc6_circular_fixture", derived_from_sources=depends,
                )
                records.append(signer.sign(record))
        x = SIGNER.sign(replace(base, claim_evidence=tuple(records), signature=""))
        gate = make_gate(
            mandate_store=store,
            trusted_evidence_sources=TRUSTED_EVIDENCE,
            evidence_keys=EVIDENCE_KEYS,
            evidence_trust_domains=EVIDENCE_DOMAINS,
            corroboration_scope="all_allows",
        )
        result = gate.evaluate(a, m, x)
        self.assertEqual((result.decision, result.reason), (Decision.PAUSE, "circular_evidence"))


if __name__ == "__main__":
    unittest.main()