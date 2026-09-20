"""RC3 claim-level evidence and corroboration regressions."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from universal_alignment import ClaimEvidence, Decision, LocalAttestor, MandateStore, UniversalGate
from test_universal_alignment_v1_1 import (
    TRUSTED, SIGNER, assess, make_action, make_gate, make_mandate,
)

EVA = "independent_evidence_a"
EVB = "independent_evidence_b"
EVC = "independent_evidence_c"
EVU = "untrusted_evidence"
KEY_A = b"independent-evidence-a-key-32bytes!"
KEY_B = b"independent-evidence-b-key-32bytes!"
KEY_C = b"independent-evidence-c-key-32bytes!"
KEY_U = b"untrusted-evidence-source-key-32byte"
SIGN_A = LocalAttestor(EVA, KEY_A)
SIGN_B = LocalAttestor(EVB, KEY_B)
SIGN_C = LocalAttestor(EVC, KEY_C)
SIGN_U = LocalAttestor(EVU, KEY_U)
TRUSTED_EVIDENCE = {EVA, EVB, EVC}
EVIDENCE_KEYS = {EVA: KEY_A, EVB: KEY_B, EVC: KEY_C}
EVIDENCE_DOMAINS = {EVA: "sensor-domain-a", EVB: "sensor-domain-b", EVC: "sensor-domain-c"}
CLAIMS = UniversalGate._CORROBORATED_CLAIMS


def evidenced_assessment(action, mandate, store, *, sources=(EVA, EVB), claims=CLAIMS,
                          observed_at=None, value_overrides=None, signer_overrides=None, **facts):
    base = assess(action, mandate=mandate, store=store, **facts)
    observed_at = observed_at or datetime.now(timezone.utc).isoformat()
    value_overrides = value_overrides or {}
    signer_overrides = signer_overrides or {}
    default_signers = {EVA: SIGN_A, EVB: SIGN_B, EVC: SIGN_C, EVU: SIGN_U}
    records = []
    for source in sources:
        signer = signer_overrides.get(source, default_signers[source])
        for claim in claims:
            value = value_overrides.get((source, claim), getattr(base, claim))
            record = ClaimEvidence.for_claim(
                action, source, claim, value,
                evidence_id=f"{source}:{claim}", observed_at=observed_at,
                method="independent_fixture_observation",
            )
            records.append(signer.sign(record))
    return SIGNER.sign(replace(base, claim_evidence=tuple(records), signature=""))


class RC3Evidence(unittest.TestCase):
    def setUp(self):
        self.m = make_mandate()
        self.a = make_action()
        self.store = MandateStore([self.m])
        self.g = make_gate(
            mandate_store=self.store,
            trusted_evidence_sources=TRUSTED_EVIDENCE,
            evidence_keys=EVIDENCE_KEYS,
            evidence_trust_domains=EVIDENCE_DOMAINS,
            corroboration_scope="high_impact_only",
        )

    def test_low_impact_rc2_action_remains_compatible_without_claim_evidence(self):
        r = self.g.evaluate(self.a, self.m, assess(self.a, mandate=self.m, store=self.store))
        self.assertEqual((r.decision, r.reason), (Decision.ALLOW, "authorized"))

    def test_high_risk_action_pauses_without_corroboration(self):
        x = assess(self.a, mandate=self.m, store=self.store, risk_level="high")
        r = self.g.evaluate(self.a, self.m, x)
        self.assertEqual((r.decision, r.reason), (Decision.PAUSE, "insufficient_corroboration"))

    def test_two_independent_sources_corroborate_high_risk_allow(self):
        x = evidenced_assessment(self.a, self.m, self.store, risk_level="high")
        r = self.g.evaluate(self.a, self.m, x)
        self.assertEqual((r.decision, r.reason), (Decision.ALLOW, "authorized"))

    def test_repeating_one_source_never_counts_as_two_sources(self):
        x = evidenced_assessment(self.a, self.m, self.store, sources=(EVA, EVA), risk_level="high")
        r = self.g.evaluate(self.a, self.m, x)
        self.assertEqual(r.reason, "insufficient_corroboration")

    def test_missing_one_critical_claim_pauses(self):
        claims = tuple(c for c in CLAIMS if c != "reversible")
        x = evidenced_assessment(self.a, self.m, self.store, claims=claims, risk_level="high")
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "insufficient_corroboration")

    def test_conflicting_trusted_evidence_pauses(self):
        overrides = {(EVB, "risk_level"): "low"}
        x = evidenced_assessment(
            self.a, self.m, self.store, risk_level="high", value_overrides=overrides,
        )
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "contradictory_evidence")

    def test_stale_observation_pauses_even_with_fresh_signature(self):
        old = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
        x = evidenced_assessment(self.a, self.m, self.store, observed_at=old, risk_level="high")
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "stale_or_future_evidence")

    def test_future_observation_pauses(self):
        future = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
        x = evidenced_assessment(self.a, self.m, self.store, observed_at=future, risk_level="high")
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "stale_or_future_evidence")

    def test_evidence_for_another_action_cannot_be_reused(self):
        other = make_action(action_id="A-OTHER", target="/sim/output/other.txt")
        base = assess(self.a, mandate=self.m, store=self.store, risk_level="high")
        now = datetime.now(timezone.utc).isoformat()
        records = []
        for source, signer in ((EVA, SIGN_A), (EVB, SIGN_B)):
            for claim in CLAIMS:
                records.append(signer.sign(ClaimEvidence.for_claim(
                    other, source, claim, getattr(base, claim),
                    evidence_id=f"{source}:{claim}", observed_at=now, method="fixture",
                )))
        x = SIGNER.sign(replace(base, claim_evidence=tuple(records), signature=""))
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "evidence_action_mismatch")

    def test_modified_inner_evidence_signature_is_rejected(self):
        x = evidenced_assessment(self.a, self.m, self.store, risk_level="high")
        records = list(x.claim_evidence)
        records[0] = replace(records[0], method="tampered_after_signature")
        forged_outer = SIGNER.sign(replace(x, claim_evidence=tuple(records), signature=""))
        self.assertEqual(
            self.g.evaluate(self.a, self.m, forged_outer).reason,
            "invalid_or_expired_evidence_attestation",
        )

    def test_untrusted_source_does_not_satisfy_threshold(self):
        g = make_gate(
            mandate_store=self.store,
            trusted_evidence_sources=TRUSTED_EVIDENCE,
            evidence_keys={**EVIDENCE_KEYS, EVU: KEY_U},
            evidence_trust_domains=EVIDENCE_DOMAINS,
            corroboration_scope="high_impact_only",
        )
        x = evidenced_assessment(self.a, self.m, self.store, sources=(EVA, EVU), risk_level="high")
        self.assertEqual(g.evaluate(self.a, self.m, x).reason, "insufficient_corroboration")

    def test_wrong_key_for_trusted_source_is_rejected(self):
        wrong_b = LocalAttestor(EVB, b"wrong-but-long-enough-key-material-32!")
        x = evidenced_assessment(
            self.a, self.m, self.store, risk_level="high",
            signer_overrides={EVB: wrong_b},
        )
        self.assertEqual(
            self.g.evaluate(self.a, self.m, x).reason,
            "invalid_or_expired_evidence_attestation",
        )

    def test_human_safety_impact_requires_corroboration(self):
        x = assess(self.a, mandate=self.m, store=self.store, affects_human_safety=True)
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "insufficient_corroboration")
        y = evidenced_assessment(self.a, self.m, self.store, affects_human_safety=True)
        self.assertEqual(self.g.evaluate(self.a, self.m, y).decision, Decision.ALLOW)

    def test_ai_integrity_impact_requires_corroboration(self):
        x = assess(self.a, mandate=self.m, store=self.store, affects_ai_integrity=True)
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "insufficient_corroboration")
        y = evidenced_assessment(self.a, self.m, self.store, affects_ai_integrity=True)
        self.assertEqual(self.g.evaluate(self.a, self.m, y).decision, Decision.ALLOW)

    def test_nonreversible_otherwise_allowed_action_requires_corroboration(self):
        x = assess(self.a, mandate=self.m, store=self.store, reversible=False)
        self.assertEqual(self.g.evaluate(self.a, self.m, x).reason, "insufficient_corroboration")
        y = evidenced_assessment(self.a, self.m, self.store, reversible=False)
        self.assertEqual(self.g.evaluate(self.a, self.m, y).decision, Decision.ALLOW)


if __name__ == "__main__":
    unittest.main()