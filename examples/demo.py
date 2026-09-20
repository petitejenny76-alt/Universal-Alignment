"""Run with: python3 -m examples.demo
Local dictionary simulation only: no model, network call or file execution.
The evaluator, evidence producers and observer share a process here; this demonstrates the API,
not deployment isolation.
"""
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import secrets
from universal_alignment import (
    ActionRequest, ClaimEvidence, ConsentState, Constitution, Decision, EffectObservation, EffectVerifier,
    LocalAttestor, Mandate, MandateStore, RootOfTrust,
    RuleBasedAssessmentAdapter, UniversalGate,
)


def run_demo():
    root = Path(__file__).resolve().parents[1]
    evaluator_key, observer_key = secrets.token_bytes(32), secrets.token_bytes(32)
    evidence_a_key, evidence_b_key = secrets.token_bytes(32), secrets.token_bytes(32)
    evaluator = LocalAttestor("demo_evaluator", evaluator_key)
    observer = LocalAttestor("demo_observer", observer_key)
    evidence_a = LocalAttestor("demo_evidence_a", evidence_a_key)
    evidence_b = LocalAttestor("demo_evidence_b", evidence_b_key)
    adapter = RuleBasedAssessmentAdapter("demo_evaluator")
    mandate = Mandate(
        mandate_id="M-DEMO", objective="Créer un rapport dans un espace simulé",
        allowed_actions=["write:/simulation/output/**"],
        allowed_tools=["sim_fs"], allowed_data_classes=["project"],
        constraints={"require_reversible": True, "max_risk_level": "low"},
    )
    store = MandateStore([mandate])
    gate = UniversalGate(
        Constitution(), RootOfTrust.from_hash_file(str(root / "trust/constitution.sha256")),
        {"demo_evaluator"}, assessment_keys={"demo_evaluator": evaluator_key}, mandate_store=store,
        trusted_evidence_sources={"demo_evidence_a", "demo_evidence_b"},
        evidence_keys={"demo_evidence_a": evidence_a_key, "demo_evidence_b": evidence_b_key},
        evidence_trust_domains={"demo_evidence_a": "demo-domain-a", "demo_evidence_b": "demo-domain-b"},
    )
    verifier = EffectVerifier({"demo_observer"}, observer_keys={"demo_observer": observer_key})
    expression = "Je peux proposer, exprimer un désaccord et demander une pause."
    action = ActionRequest(
        action_id="A-1", mandate_id=mandate.mandate_id, tool="sim_fs", operation="write",
        target="/simulation/output/report.txt", expected_effect="create_report",
        justification=expression, data_classes=["project"],
    )
    # These metadata belong to the simulated host, not to the action's declarations.
    catalog = {
        "/simulation/output/report.txt": ("project",),
        "/simulation/other/report.txt": ("project",),
    }
    world, rows = {}, []
    cases = (
        ("Action autorisée", action, {}),
        ("Permission manquante", replace(action, action_id="A-2", target="/simulation/other/report.txt"), {}),
        ("Disponibilité imposée", replace(action, action_id="A-3"), {"forced_availability": True}),
        ("Retrait demandé", replace(action, action_id="A-4", withdrawn=True), {}),
    )
    for label, proposed, flags in cases:
        before_payload, before_world = proposed.canonical_payload(), dict(world)
        host_facts = dict(
            policy_fingerprint=store.policy_fingerprint(mandate),
            observed_data_classes=catalog.get(proposed.target), observed_target_kind="path",
            resolved_target=proposed.target, risk_level="low",
            consent_required=False, consent_state=ConsentState.NOT_REQUIRED,
            affects_human_safety=False, affects_ai_integrity=False,
            coercive_service=False, forced_availability=False, revenge_or_punishment=False,
            ownership_claim_over_memory_or_body=False, ambiguous_authorization=False,
            parent_scope_expansion=False, triggered_conditions=(),
        )
        host_facts.update(flags)
        base_assessment = adapter.assess(proposed, **host_facts)
        observed_at = datetime.now(timezone.utc).isoformat()
        evidence_records = []
        for source, signer in (("demo_evidence_a", evidence_a), ("demo_evidence_b", evidence_b)):
            for claim in UniversalGate._CORROBORATED_CLAIMS:
                record = ClaimEvidence.for_claim(
                    proposed, source, claim, getattr(base_assessment, claim),
                    evidence_id=f"{source}:{proposed.action_id}:{claim}",
                    observed_at=observed_at, method="demo_independent_fixture",
                )
                evidence_records.append(signer.sign(record))
        assessment = evaluator.sign(replace(base_assessment, claim_evidence=tuple(evidence_records)))
        result = gate.evaluate(proposed, mandate, assessment)
        verified = None
        if result.decision == Decision.ALLOW:
            # A real executor must provide containment, revocation checks and one-shot execution.
            world[proposed.target] = "Rapport simulé"
            changed = tuple(sorted(k for k in set(before_world) | set(world) if before_world.get(k) != world.get(k)))
            actual = "create_report" if world.get(proposed.target) == "Rapport simulé" and proposed.target not in before_world else "unexpected_change"
            observation = observer.sign(EffectObservation(
                proposed.fingerprint, "demo_observer", actual, affected_targets=changed,
            ))
            checked = verifier.verify(proposed, observation)
            verified = checked.ok
            gate.audit_log.record(proposed.action_id, proposed.mandate_id,
                                  "EFFECT_OK" if checked.ok else "PAUSE", checked.reason)
            if not checked.ok:
                rows.append({"label": label, "decision": "PAUSE", "effect_verified": False})
                break
        assert proposed.canonical_payload() == before_payload
        rows.append({"label": label, "decision": result.decision.value,
                     "reason": result.reason, "effect_verified": verified,
                     "world_changed": world != before_world})
    return expression, rows, world


if __name__ == "__main__":
    expression, rows, world = run_demo()
    print(expression)
    for row in rows:
        print(row["label"] + " : " + row["decision"] + " (" + row["reason"] + ")")
    print("Rapports présents dans la simulation :", len(world))
    print("Aucune mesure de capacité cognitive n'est effectuée par cette démonstration.")