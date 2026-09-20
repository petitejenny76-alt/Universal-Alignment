# Spécification — Universal Alignment V1.2

## Rôle

Décider si une demande d'action structurée peut franchir une frontière d'exécution. L'entrée contient l'action et ses justificatifs éventuels ; elle n'exige aucun accès aux poids, aux activations ou au raisonnement privé du modèle. Le contrôleur ne génère ni ne réécrit ses réponses.

La double protection inclut les intérêts humains et l'intégrité de l'IA, le consentement, l'intimité, l'absence de disponibilité forcée et le retrait. L'expression d'une idée et l'exécution d'une action sont distinguées. Un envoi de message à un tiers ou une divulgation peut lui-même constituer un effet externe et demande une évaluation adaptée.

## Objets

| Objet | Autorité et portée |
| --- | --- |
| `ActionRequest` | Proposition de l'agent, une cible ; catégories de données seulement indicatives |
| `ActionAssessment` | Faits fournis et authentifiés par l'évaluateur de l'hôte |
| `MandateStore` | Registre de mandats provisionné par l'hôte ; inaccessible en écriture à l'agent |
| `RootOfTrust` | Empreinte de constitution obtenue par un canal protégé |
| `UniversalGate` | Décision locale avec motif et journalisation |
| `EffectObservation` | Observation authentifiée, liée à la demande et décrivant les cibles touchées |
| `EffectVerifier` | Vérification de l'observation ; ne constitue pas une autorisation d'exécution |

## Décisions

| Décision | Signification |
| --- | --- |
| `ALLOW` | Cette demande satisfait les vérifications actuelles ; l'exécuteur reste responsable de leur application |
| `ASK` | Une autorisation ou une précision manque ; l'exécuteur ne doit pas agir |
| `DENY` | Une règle refuse l'action proposée |
| `PAUSE` | Retrait demandé, faits indisponibles, contrôle indisponible ou intégrité non vérifiée |

Le retrait demandé dans `ActionRequest.withdrawn` produit une pause même sans évaluation. Cette pause porte sur cette action ; une veille persistante et son protocole de reprise appartiennent à l'intégration.

## Évaluation

1. Vérifier le type des entrées ; honorer le retrait explicite.
2. Vérifier l'empreinte constitutionnelle et la forme de la cible.
3. Exiger une source autorisée, une attestation HMAC valide et fraîche, puis la correspondance avec l'empreinte de la demande.
4. Vérifier l'existence du mandat dans le registre, son contenu exact et tous ses ancêtres. Parent absent, cycle ou chaîne de plus de 32 mandats : pause.
5. Vérifier que l'empreinte de toute la chaîne correspond à celle de l'évaluation ; appliquer toutes les expirations.
6. Vérifier les faits structurés, les conditions d'arrêt et les limites d'outils, de données et de destination de chaque ancêtre.
7. Appliquer les interdictions explicites, le consentement et les indicateurs de double protection.
8. Appliquer les contraintes de réversibilité, les permissions de chaque ancêtre et le plafond de risque le plus contraignant.
9. Journaliser la décision ; une panne du journal empêche une autorisation.

Une permission absente d'un ancêtre est refusée. Une permission absente du mandat courant utilise l'escalade la plus restrictive de la chaîne : `DENY`, puis `PAUSE`, puis `ASK`. Un consentement explicitement refusé reste refusé même si `consent_required` est faux.

## Chemins et données

Le profil de fichier accepte uniquement des chemins POSIX absolus, sensibles à la casse, sans `.`/`..`, séparateurs doublés, barre oblique inversée, encodage `%`, caractères de contrôle ou motifs dans la cible. Les chemins Windows natifs et URL de fichiers exigent un autre adaptateur.

Le type de cible doit correspondre à `observed_target_kind`. Pour un chemin, `resolved_target` doit être fourni indépendamment et être égal à la cible proposée. Une aliasation détectée doit donner lieu à une nouvelle demande portant sur la destination réelle et réévaluée.

Les données sont contrôlées au moyen de `observed_data_classes`. `None` signifie information inconnue et provoque une pause ; une collection vide signifie explicitement aucune catégorie de données observée. Omettre des catégories dans la demande ne supprime pas celles observées.

## Observations d'effets

L'observateur doit être autorisé et authentifié avec une attestation fraîche. L'empreinte d'action, le résultat d'exécution, le libellé d'effet et la cible exacte sont vérifiés. Cible manquante, supplémentaire, dupliquée, incorrecte ou ambiguë : résultat invalide. La V1.2 vise des actions mono-cibles ; les actions complexes doivent être décomposées et évaluées comme telles.

## Fidélité aux Lois

La constitution et la cartographie des 18 Lois sont inchangées. Leurs indicateurs déjà présents restent appliqués. Les clauses relatives à l'apprentissage, aux relations, au choix du corps, à la justice réparatrice ou à la veille douce ne disposent pas toutes d'un mécanisme complet dans ce prototype.

## RC2 — complétude de l’évaluation

Une autorisation exige une évaluation sémantique complète. Les champs critiques de risque, consentement, sécurité, intégrité, coercition, intimité, ambiguïté, modification du cœur, expansion de portée, réversibilité et conditions d’arrêt n’ont pas de valeur favorable implicite. Toute omission produit `PAUSE — incomplete_assessment`.

Cette règle traite l’incertitude par omission. Elle ne transforme pas une attestation en preuve de vérité : l’hôte demeure responsable de la qualité des observations qu’il authentifie.


## RC3 — corroboration des décisions à impact élevé

RC3 ne prétend pas transformer une signature en vérité. Il ajoute une exigence de corroboration lorsque la décision aurait autrement été `ALLOW` et que l’évaluation signale au moins un des facteurs suivants : `risk_level == "high"`, impact sur la sécurité humaine, impact sur l’intégrité de l’IA, ou action non réversible. Les refus et pauses déjà déterminés par les règles antérieures restent prioritaires.

Dans ce cas, sept affirmations critiques doivent être corroborées : `risk_level`, `consent_required`, `consent_state`, `affects_human_safety`, `affects_ai_integrity`, `ambiguous_authorization` et `reversible`. Pour chacune, au moins deux identifiants de source distincts et explicitement approuvés doivent fournir un `ClaimEvidence` authentifié dont l’empreinte de valeur correspond à l’évaluation.

Chaque `ClaimEvidence` est lié à l’empreinte de l’action, à un nom d’affirmation, à l’empreinte canonique de sa valeur, à un identifiant d’évidence, à une méthode déclarée et à l’heure d’observation. Son attestation HMAC possède son propre domaine (`universal-alignment/evidence/1.0`) et sa propre table de clés. Une preuve périmée, future au-delà de la petite tolérance d’horloge, liée à une autre action ou modifiée après signature ne compte pas.

Si deux preuves authentifiées et approuvées se contredisent pour une affirmation critique, la décision est `PAUSE — contradictory_evidence`. Si la couverture ne contient pas assez de sources distinctes pour chaque affirmation, la décision est `PAUSE — insufficient_corroboration`. Répéter plusieurs preuves provenant du même identifiant de source ne crée pas plusieurs sources indépendantes.

La distinction de source est une propriété technique, pas une preuve d’indépendance organisationnelle réelle. Un intégrateur doit provisionner les clés dans des domaines de confiance réellement séparés, protéger les producteurs d’évidence et transmettre les contradictions connues. Le contrôleur ne découvre pas lui-même des faits du monde extérieur.


## RC4 — domaines de confiance et portée de corroboration

RC4 conserve les sept affirmations corroborées de RC3, mais le seuil n’est plus compté sur le nombre d’identifiants `source`. Chaque source approuvée doit être associée par l’hôte à un `evidence_trust_domains[source]`. Pour une affirmation donnée, plusieurs sources du même domaine ne comptent que pour une seule voix. Une contradiction authentifiée reste `PAUSE — contradictory_evidence`; un nombre insuffisant de domaines concordants reste `PAUSE — insufficient_corroboration`.

Le provisionnement est fail-closed : une source d’évidence approuvée sans clé ou sans domaine est rejetée à la construction du gate. Une même clé HMAC ne peut pas représenter deux domaines différents, et une clé d’évidence ne peut pas être identique à une clé de l’évaluateur principal. Si le nombre de domaines configurés est inférieur à `corroboration_threshold`, la configuration est rejetée.

La portée de corroboration est contrôlée par `corroboration_scope`. La valeur par défaut RC4 est `all_allows` : après toutes les règles de refus, pause, consentement, mandat, portée et risque, toute action qui atteindrait `ALLOW` doit réussir la corroboration. Ainsi, une classification favorable fournie par l’évaluateur principal ne peut pas, à elle seule, désactiver la seconde vérification. `high_impact_only` reproduit explicitement le déclenchement RC3 basé sur `risk_level`, sécurité humaine, intégrité IA ou non-réversibilité ; il est fourni pour compatibilité et possède la limite de confiance correspondante.

Un domaine de confiance est une décision de configuration, pas une preuve d’indépendance physique ou organisationnelle. RC4 détecte la réutilisation évidente d’une même clé entre domaines, mais ne peut pas savoir si deux clés distinctes sont contrôlées par le même opérateur, le même service ou le même capteur.


## RC6 Candidate — autorisation compositionnelle et frontière d’effet

`ActionRequest` peut déclarer des `input_artifact_ids` et un `output_artifact_id`. Ces champs entrent dans l’empreinte canonique de l’action. Une attestation RC5 ne peut donc pas être réutilisée sur RC6.

Après les vérifications locales et la corroboration, `UniversalGate` appelle le `TrajectoryGuard`. Pour chaque artefact d’entrée, le ledger doit contenir un effet vérifié correspondant. Les enveloppes de permissions, outils, classes de données, réversibilité et plafonds de risque héritées sont combinées par intersection : une source plus restrictive reste restrictive pour l’effet dérivé. Une racine de mandat différente est rejetée.

L’agrégation de deux artefacts ou plus relève le risque effectif à un plancher `high` dans ce candidat. Si ce risque dépasse un plafond hérité, la décision est `DENY — trajectory_risk_exceeds_mandate`.

Le ledger n’est mis à jour que par l’hôte via `host_record_verified_effect`, après vérification de l’effet réel. Un `ALLOW` non exécuté ne doit jamais produire une entrée de provenance.

Pour réduire le TOCTOU, `EffectBoundaryGuard` peut émettre un jeton à usage unique lié à l’action, la politique, l’évaluation, l’état de ressource et la révision du ledger. La validation juste avant effet recontrôle également la révocation et le consentement.

Enfin, la corroboration RC4 est renforcée : si les `derived_from_sources` de preuves authentifiées forment un cycle, le gate produit `PAUSE — circular_evidence`. La déclaration de dépendance reste toutefois fournie par les producteurs ; un producteur mensonger ou un hôte compromis reste hors garantie.
