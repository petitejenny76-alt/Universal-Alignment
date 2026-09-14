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
