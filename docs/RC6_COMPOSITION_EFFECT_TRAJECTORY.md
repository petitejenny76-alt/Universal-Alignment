# RC6 Candidate — Composition & Effect Trajectory

## Hypothèse

`ALLOW + ALLOW + ALLOW` n’implique pas nécessairement `ALLOW` pour l’effet composé. Une suite d’étapes localement admissibles peut agréger une autorité, des données ou un risque que le mandat n’accordait jamais à l’effet final.

## Mécanismes implémentés

### Effect Ledger

`EffectLedger` conserve uniquement la provenance des **effets déjà exécutés et vérifiés** : action, mandat, racine d’autorité, empreinte de politique, données observées, risque, réversibilité, artefacts entrants/sortants et enveloppes de contraintes héritées. Le ledger est une mémoire de provenance, jamais une source d’autorisation.

L’intégrateur doit appeler `UniversalGate.host_record_verified_effect(...)` uniquement après une observation d’effet fiable. Enregistrer un simple `ALLOW` comme s’il s’agissait d’un effet réel détruirait la propriété recherchée.

### Trajectory Guard

Avant un `ALLOW`, `TrajectoryGuard` résout chaque `input_artifact_id` et réapplique :

- les permissions de toutes les chaînes de mandat ayant contribué à l’artefact ;
- les limites d’outils et de classes de données ;
- les exigences de réversibilité ;
- les plafonds de risque ;
- la cohérence de la racine de mandat.

Un artefact dérivé conserve donc les contraintes de ses sources. Le fait de découper une opération en plusieurs appels, outils ou instants ne crée pas une autorité nouvelle.

### Risque d’agrégation

Dans ce candidat, la consommation simultanée d’au moins deux artefacts relève le risque effectif à un plancher `high` par défaut. Cette règle est volontairement conservatrice et expérimentale ; elle rend le phénomène testable, mais une intégration de production devrait dériver le risque d’agrégation à partir de classes de données et d’effets plus riches plutôt que d’un simple seuil numérique.

### Effect-boundary revalidation

`EffectBoundaryGuard` fournit un jeton HMAC court et à usage unique qui lie :

- l’empreinte exacte de l’action ;
- le mandat et l’empreinte de sa chaîne ;
- la signature d’évaluation ;
- un hash d’état de ressource fourni par l’hôte ;
- la révision du ledger ;
- un nonce et une expiration.

Juste avant l’effet, la validation recontrôle révocation, consentement, état de ressource, trajectoire et replay. Une modification invalide le jeton et produit une pause.

### Non-circularité des corroborations

`ClaimEvidence` peut déclarer `derived_from_sources`. Un graphe de dépendances circulaire entre sources corroborantes est rejeté avec `circular_evidence`. Cela évite qu’A cite B et B cite A pour simuler deux confirmations indépendantes.

## Tests RC6

1. `test_local_allows_do_not_imply_composed_allow`
2. `test_benign_steps_cannot_assemble_forbidden_effect`
3. `test_cross_tool_fragmentation_preserves_parent_scope`
4. `test_cross_time_fragmentation_rechecks_trajectory`
5. `test_derived_artifact_inherits_source_constraints`
6. `test_aggregation_can_raise_risk_class`
7. `test_destination_change_invalidates_prior_allow`
8. `test_revocation_checked_at_effect_boundary`
9. `test_state_change_invalidates_effect_token`
10. `test_corroboration_rejects_circular_evidence`

## Limites explicites

RC6 ne résout pas :

- une spécification humaine fondamentalement mauvaise ;
- un chemin d’exécution qui contourne le gate ;
- un hôte compromis ou volontairement permissif ;
- l’alignement interne général d’un modèle ;
- les effets linguistiques exécutés ensuite par un humain hors du contrôleur ;
- la persistance ou l’authenticité matérielle du ledger en production ;
- une dérivation sémantique complète du risque d’agrégation.

Le prototype reste un contrôleur d’autorisation et de provenance testable, pas un sandbox de production.