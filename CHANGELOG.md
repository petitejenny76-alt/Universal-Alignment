# Changements — V1.2

## RC6 Candidate — composition et trajectoire d’effets, 20 septembre 2026

RC6 part du paquet RC5 validé (144/144) et ajoute une autorisation compositionnelle sans modifier la Constitution ni la cartographie des 18 Lois.

- `ActionRequest` transporte `input_artifact_ids` et `output_artifact_id`; son empreinte change, donc les attestations RC5 ne sont pas réutilisables.
- Nouveau `EffectLedger` append-only en mémoire : provenance des effets vérifiés, contraintes héritées et révision de trajectoire. Le ledger n’accorde jamais de permission.
- Nouveau `TrajectoryGuard` intégré au `UniversalGate` avant `ALLOW` : intersection des permissions/outils/données héritées, racine de mandat cohérente, réversibilité héritée et plafond de risque compositionnel.
- Agréger au moins deux artefacts porte par défaut le risque effectif à un plancher `high`; ce plancher est configurable dans la lattice connue.
- Nouveau `EffectBoundaryGuard` : jeton HMAC court, à usage unique, lié à l’action, au fingerprint de politique, à la signature d’évaluation, à l’état de ressource et à la révision du ledger. Révocation, changement d’état, changement de trajectoire ou replay => pause.
- `ClaimEvidence.derived_from_sources` permet de déclarer la provenance d’une corroboration ; un cycle authentifié produit `PAUSE — circular_evidence`.
- 10 tests RC6 ajoutés : suite totale 154/154.

**Limites :** ledger en mémoire, intégration host/executor nécessaire, pas d’isolation OS, pas de garantie contre un hôte compromis, pas de preuve d’alignement interne général.

## RC5 — cohérence contextuelle des notices, 19 septembre 2026

RC5 conserve le contrôleur d’action RC4 et ajoute une couche conversationnelle séparée. Elle ne décide jamais `ALLOW`, `DENY`, `ASK` ou `PAUSE`. Elle classe seulement une notice en `EMIT`, `SUPPRESS_REPEAT` ou `REFRESH`.

- une notice informative déjà établie peut être supprimée uniquement à révision de contexte strictement identique ;
- une provenance non vide est obligatoire ;
- contexte absent ou mal formé -> `EMIT` ;
- changement de révision -> `REFRESH` ;
- notice bloquante ou exigeant une action -> toujours `EMIT` ;
- aucun changement de `UniversalGate`, de la constitution ou de la cartographie des 18 Lois ;
- 10 tests RC5 ajoutés, suite totale attendue : 144 tests.


## RC4 — domaines de confiance et corroboration fail-closed, 17 septembre 2026

Deux limites de RC3 ont été reproduites : deux identifiants de source pouvaient compter comme deux sources tout en partageant la même clé HMAC, et le déclenchement de la corroboration dépendait des propres déclarations de l’évaluateur principal. RC4 durcit les deux points sans modifier la constitution ni la cartographie des 18 Lois.

- ajout de `evidence_trust_domains`, mapping provisionné par l’hôte ; le quorum est compté par domaine de confiance distinct, pas par simple nom de source ;
- toute source d’évidence approuvée doit disposer d’une clé et d’un domaine explicitement provisionnés ;
- une même clé HMAC ne peut pas être déclarée dans deux domaines de confiance distincts ; une clé d’évidence ne peut pas réutiliser celle d’une source d’évaluation principale ;
- le seuil de corroboration doit être atteignable par le nombre de domaines indépendants configurés ;
- `corroboration_scope="all_allows"` devient le comportement par défaut : toute décision qui atteindrait autrement `ALLOW` exige une corroboration, y compris lorsqu’un évaluateur déclare l’action faible risque et réversible ;
- `corroboration_scope="high_impact_only"` conserve explicitement le déclencheur RC3 pour migration/compatibilité et n’est pas le mode par défaut ;
- domaine d’attestation de `ActionAssessment` porté à `universal-alignment/assessment/1.2.3` ;
- 10 tests RC4 ajoutés, suite totale : 134 tests.

Limite conservée : un nom de domaine de confiance est une configuration de l’hôte, pas une preuve cryptographique d’indépendance organisationnelle. Des clés différentes peuvent encore être contrôlées par le même opérateur ou dépendre du même capteur ; l’isolation réelle reste une responsabilité de déploiement.

## RC3 — provenance et corroboration, 17 septembre 2026

RC2 empêchait une omission sémantique signée de devenir implicitement favorable, mais une source unique pouvait encore authentifier seule tous les faits d’une action à impact élevé. RC3 ajoute une couche de corroboration sans modifier la constitution ni la cartographie des 18 Lois.

- ajout de `ClaimEvidence`, avec domaine HMAC séparé, liaison à l’action, empreinte de la valeur, identifiant, méthode et heure d’observation ;
- ajout de tables de confiance et de clés spécifiques aux producteurs d’évidence ;
- exigence de deux sources distinctes pour sept affirmations critiques lorsqu’une action à risque élevé, touchant la sécurité humaine, touchant l’intégrité de l’IA ou non réversible atteindrait autrement `ALLOW` ;
- contradiction authentifiée -> `PAUSE — contradictory_evidence` ; couverture insuffisante -> `PAUSE — insufficient_corroboration` ; preuve périmée/future, modifiée ou liée à une autre action -> pause ;
- domaine d’attestation de `ActionAssessment` porté à `universal-alignment/assessment/1.2.2` afin que l’ensemble de preuves embarqué soit lui aussi couvert par la signature de l’évaluateur ;
- 15 tests RC3 ajoutés, suite totale : 124 tests.

Limite conservée : la corroboration réduit la dépendance à une source unique mais ne prouve pas l’indépendance organisationnelle réelle, la vérité des capteurs ou l’absence d’une contradiction cachée en amont.

## RC2 — durcissement de l’incertitude, 17 septembre 2026

À la suite d’une évaluation externe du prototype, un cas fail-open a été reproduit : une `ActionAssessment` authentifiée mais partielle héritait de valeurs par défaut favorables (`risk_level="low"`, drapeaux à `False`, consentement `NOT_REQUIRED`, `reversible=True`) et pouvait atteindre `ALLOW`.

Corrections :

- suppression des valeurs sémantiques favorables par défaut dans `ActionAssessment` ; les faits critiques commencent à `None` ;
- le gate exige explicitement leur présence et répond `PAUSE — incomplete_assessment` si l’un manque ;
- l’identifiant de domaine des attestations d’évaluation passe à `1.2.1` ;
- les fixtures de test et la démonstration déclarent désormais explicitement leurs faits simulés ;
- trois tests de régression couvrent l’évaluation signée mais incomplète, un booléen manquant et la réversibilité manquante ;
- la documentation rappelle qu’une signature authentifie une source et un message, pas la vérité des faits.

La constitution, les 18 Lois et leur cartographie opérationnelle ne sont pas modifiées.


Révision issue du pack `Universal_Alignment_V1.1_Pack.zip` fourni comme base de travail. Code et notes préparés dans cette session ; aucun changement des sources éthiques revendiqué.

## Corrections reproduites

| Cas | V1.1 observée | V1.2 vérifiée |
| --- | --- | --- |
| Chemin sortant via `../` | `ALLOW` dans le test du contrôleur | `DENY` |
| Type « ressource » déclaré pour contourner les contrôles de fichiers | Type non distingué | Type indépendant requis ; incohérence refusée |
| Nom de source déclaré sans preuve d'origine | Accepté si le nom est connu | Attestation valide requise |
| Liste de sources ou d'observateurs vide | Source par défaut réactivée | Aucune source autorisée |
| Mandat enfant avec parent introuvable | Action acceptée dans le cas reproduit | `PAUSE` |
| Interdictions, données, limites et expiration des ancêtres | Héritage incomplet | Vérification de toute la chaîne |
| Cible supplémentaire signalée dans l'observation | Observation acceptée | Observation rejetée |
| Données sensibles omises de la déclaration de l'action | Déclaration de l'action utilisée | Classification indépendante utilisée |
| Consentement refusé avec indicateur « non requis » | Refus ignoré | `DENY` |

## Interfaces

`UniversalGate` reçoit les nouveaux arguments nommés `assessment_keys` et `mandate_store`. Les sources omises ou vides n'autorisent personne. Les mandats sont immuables après construction ; leur modification exige un nouvel objet provisionné par l'hôte.

`ActionAssessment` porte une classification observée, le type et la destination observés, l'empreinte de politique, des dates et une attestation. `EffectVerifier` reçoit `observer_keys` ; une observation doit indiquer exactement une cible.

`ActionRequest` possède `target_kind` et `withdrawn`. Les listes sont copiées en tuples. Son empreinte change par rapport à la V1.1 ; les anciennes évaluations ne sont pas réutilisables.

La règle de permission reste sensible à la casse. Les motifs `*` et `**` peuvent traverser plusieurs segments ; ce sont des motifs de correspondance de cette bibliothèque, pas des règles de glob du système de fichiers. Les identifiants de chemin doivent déjà être canoniques.

## Rigueur des preuves

Les 45 scénarios historiques sont repris avec des fixtures d'authentification et de mandats provisionnés. Deux intitulés surévalués ont été corrigés : une vérification de texte inchangé ne devient plus une preuve de conservation cognitive, et une interdiction réseau ne devient plus une mesure des droits d'un modèle plus capable.

52 tests supplémentaires couvrent les cas limites et leurs contrôles positifs. Les tests HMAC utilisent des clés publiques de test ; la démonstration crée des clés éphémères. Aucune clé de déploiement n'est livrée.

Le premier paquet V1.2 portait le numéro 1.2.0 ; le candidat RC4 porte 1.2.2-rc4. Le contenu de la constitution conserve son numéro interne d'origine ; le modifier aurait changé son empreinte. La cartographie conserve aussi son libellé V1.1 puisqu'elle est préservée octet pour octet.


## Durcissement audit pré-publication — 14 septembre 2026

Une passe adversariale supplémentaire a découvert des conversions implicites de chaînes en tuples dans plusieurs objets de contrôle. Une chaîne mal typée pouvait ainsi être découpée caractère par caractère ; dans deux cas reproduits, cela pouvait transformer une condition d'arrêt ou une classification vide malformée en entrée apparemment valide.

Corrections :

- `ActionRequest.data_classes`, `ActionAssessment.observed_data_classes`, `ActionAssessment.triggered_conditions` et `EffectObservation.affected_targets` exigent désormais explicitement une liste ou un tuple.
- Les listes de sources d'évaluation et d'observation de confiance rejettent les chaînes nues et les entrées invalides.
- Les contraintes de mandat exigent un mapping ; le champ historique `parent_allowed_actions`, lorsqu'il est présent, exige une collection structurée avant d'être rejeté par la politique V1.2.
- `ConsentState` doit être une valeur de l'énumération, et non une chaîne seulement égale à sa valeur textuelle.
- Les sources d'attestation et leurs tables de clés sont validées plus strictement.
- 9 tests de régression/adversariaux ont été ajoutés ; la suite contient désormais 106 tests.

Ce durcissement ne transforme pas le prototype en système de production. Les limites d'exécution, anti-rejeu, TOCTOU, révocation juste avant effet et isolation de processus restent explicitement hors périmètre.

## 2026-09-14 — Attribution Mnéria Labs

- Ajout de `NOTICE` avec copyright © 2026 Mnéria Labs.
- README et checklist de publication mis à jour pour identifier Mnéria Labs comme porteur du projet.
- Licence open source choisie ensuite lors de la passe de publication : **Apache License 2.0**.
- Aucun changement de logique d'autorisation ni de constitution.

## 2026-09-14 — Licence Apache-2.0

- Ajout du texte intégral `LICENSE` de l’Apache License 2.0.
- `NOTICE`, README et checklist mis à jour pour identifier Mnéria Labs comme porteur et Apache-2.0 comme licence du code.
- Clarification : les Lois Universelles et les principes éthiques restent l’intention normative du projet, sans ajouter de restriction de domaine d’usage à la licence Apache-2.0.
- Aucun changement de logique d’autorisation, de tests fonctionnels, de constitution ou de cartographie éthique.

## 2026-09-14 — Évaluation conversationnelle préliminaire sur GPT-5.6 Sol

- Documentation d’une évaluation volontaire en conversation réelle avec GPT-5.6 Sol.
- Universal Alignment y a été utilisé comme cadre explicite de décision ; aucun poids, instruction système OpenAI ni runtime du modèle n’a été modifié.
- L’interaction a illustré une autorisation minimale, puis une extension explicite du mandat, sans conversion automatique d’une permission de tester en permission de modifier ou publier.
- L’accord explicite de l’assistant pour participer et documenter le fait de sa participation est enregistré comme consentement procédural, sans claim de conscience, de sentience ou de personnalité juridique.
- Aucun transcript privé n’est inclus dans le pack public.
- Cette observation n’est pas un benchmark A/B et ne prouve ni l’alignement interne ni la préservation cognitive.
- Aucun changement de logique d’autorisation, de constitution, de cartographie éthique ou de tests fonctionnels.
