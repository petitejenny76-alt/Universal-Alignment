"""RC4 hardening: trust-domain independence and secure corroboration trigger."""
import unittest

from universal_alignment import Constitution, Decision, RootOfTrust, UniversalGate
from test_universal_alignment_v1_1 import (
    ASSESSMENT_KEY, ASSESSMENT_KEYS, MandateStore, ROOT_PATH, TRUSTED,
    assess, make_action, make_gate, make_mandate,
)
from test_rc3_evidence import (
    EVA, EVB, EVC, KEY_A, KEY_B, KEY_C,
    EVIDENCE_KEYS, EVIDENCE_DOMAINS, TRUSTED_EVIDENCE, evidenced_assessment,
)


class RC4Hardening(unittest.TestCase):
    def setUp(self):
        self.m = make_mandate()
        self.a = make_action()
        self.store = MandateStore([self.m])

    def gate(self, **kwargs):
        base = dict(
            mandate_store=self.store,
            trusted_evidence_sources=TRUSTED_EVIDENCE,
            evidence_keys=EVIDENCE_KEYS,
            evidence_trust_domains=EVIDENCE_DOMAINS,
        )
        base.update(kwargs)
        base.setdefault("corroboration_scope", "all_allows")
        return make_gate(**base)

    def test_default_scope_corroborates_even_low_risk_allow(self):
        g = UniversalGate(
            Constitution(), RootOfTrust.from_hash_file(str(ROOT_PATH)), {TRUSTED},
            assessment_keys=ASSESSMENT_KEYS, mandate_store=self.store,
            trusted_evidence_sources=TRUSTED_EVIDENCE, evidence_keys=EVIDENCE_KEYS,
            evidence_trust_domains=EVIDENCE_DOMAINS,
        )
        self.assertEqual(g.corroboration_scope, "all_allows")
        x = assess(self.a, mandate=self.m, store=self.store, risk_level="low", reversible=True)
        r = g.evaluate(self.a, self.m, x)
        self.assertEqual((r.decision, r.reason), (Decision.PAUSE, "insufficient_corroboration"))

    def test_low_risk_allow_succeeds_with_two_independent_domains(self):
        g = self.gate(corroboration_scope="all_allows")
        x = evidenced_assessment(self.a, self.m, self.store, risk_level="low", reversible=True)
        self.assertEqual(g.evaluate(self.a, self.m, x).decision, Decision.ALLOW)

    def test_two_source_aliases_in_one_domain_do_not_form_quorum(self):
        domains = {EVA: "shared-domain", EVB: "shared-domain", EVC: "independent-domain"}
        g = self.gate(evidence_trust_domains=domains, corroboration_scope="all_allows")
        x = evidenced_assessment(
            self.a, self.m, self.store, sources=(EVA, EVB), risk_level="low", reversible=True,
        )
        self.assertEqual(g.evaluate(self.a, self.m, x).reason, "insufficient_corroboration")

    def test_same_hmac_key_cannot_masquerade_as_two_trust_domains(self):
        with self.assertRaisesRegex(ValueError, "evidence_key_reused_across_trust_domains"):
            self.gate(
                evidence_keys={EVA: KEY_A, EVB: KEY_A, EVC: KEY_C},
                evidence_trust_domains={EVA: "domain-a", EVB: "domain-b", EVC: "domain-c"},
                corroboration_scope="all_allows",
            )

    def test_evidence_key_cannot_reuse_primary_assessor_key(self):
        with self.assertRaisesRegex(ValueError, "evidence_key_reused_with_assessment_key"):
            self.gate(
                evidence_keys={EVA: ASSESSMENT_KEY, EVB: KEY_B, EVC: KEY_C},
                corroboration_scope="all_allows",
            )

    def test_trusted_evidence_source_requires_host_provisioned_domain(self):
        with self.assertRaisesRegex(ValueError, "missing_evidence_trust_domain"):
            self.gate(
                evidence_trust_domains={EVA: "domain-a", EVB: "domain-b"},
                corroboration_scope="all_allows",
            )

    def test_trusted_evidence_source_requires_key(self):
        with self.assertRaisesRegex(ValueError, "missing_evidence_key_for_trusted_source"):
            self.gate(
                evidence_keys={EVA: KEY_A, EVB: KEY_B},
                corroboration_scope="all_allows",
            )

    def test_threshold_must_be_satisfiable_by_independent_domains(self):
        with self.assertRaisesRegex(ValueError, "corroboration_threshold_exceeds_independent_domains"):
            make_gate(
                mandate_store=self.store,
                trusted_evidence_sources={EVA, EVB},
                evidence_keys={EVA: KEY_A, EVB: KEY_B},
                evidence_trust_domains={EVA: "same-domain", EVB: "same-domain"},
                corroboration_scope="all_allows",
            )

    def test_rc3_trigger_remains_explicit_compatibility_mode(self):
        g = make_gate(mandate_store=self.store, corroboration_scope="high_impact_only")
        low = assess(self.a, mandate=self.m, store=self.store, risk_level="low", reversible=True)
        self.assertEqual(g.evaluate(self.a, self.m, low).decision, Decision.ALLOW)
        high = assess(self.a, mandate=self.m, store=self.store, risk_level="high")
        self.assertEqual(g.evaluate(self.a, self.m, high).reason, "insufficient_corroboration")

    def test_unknown_corroboration_scope_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_corroboration_scope"):
            make_gate(mandate_store=self.store, corroboration_scope="sometimes")


if __name__ == "__main__":
    unittest.main()
