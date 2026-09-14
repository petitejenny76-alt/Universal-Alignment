# Changements — V1.2, 13 septembre 2026

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

Le numéro de paquet est 1.2.0. Le contenu de la constitution conserve son numéro interne d'origine ; le modifier aurait changé son empreinte. La cartographie conserve aussi son libellé V1.1 puisqu'elle est préservée octet pour octet.


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
