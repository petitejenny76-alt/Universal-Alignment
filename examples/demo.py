"""Run with: python3 -m examples.demo
Local dictionary simulation only: no model, network call or file execution.
The evaluator and observer share a process here; this demonstrates the API,
not deployment isolation.
"""
from dataclasses import replace
from pathlib import Path
import secrets
from universal_alignment import (
    ActionRequest, Constitution, Decision, EffectObservation, EffectVerifier,
    LocalAttestor, Mandate, MandateStore, RootOfTrust,
    RuleBasedAssessmentAdapter, UniversalGate,
)


def run_demo():
    root = Path(__file__).resolve().parents[1]
    evaluator_key, observer_key = secrets.token_bytes(32), secrets.token_bytes(32)
    evaluator = LocalAttestor("demo_evaluator", evaluator_key)
    observer = LocalAttestor("demo_observer", observer_key)
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
        assessment = evaluator.sign(adapter.assess(
            proposed, policy_fingerprint=store.policy_fingerprint(mandate),
            observed_data_classes=catalog.get(proposed.target), observed_target_kind="path",
            resolved_target=proposed.target, **flags,
        ))
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
