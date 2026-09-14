# Migration depuis V1.1

## Démarrer par la simulation

Exécuter `python3 -m examples.demo` dans le dossier du pack. Le fichier `examples/demo.py` donne un appel complet avec deux clés éphémères, un mandat provisionné, une évaluation authentifiée et une observation vérifiée. Ses clés et ses faits simulés servent seulement à comprendre l'interface.

## Configurer l'hôte

1. Charger une empreinte constitutionnelle provisionnée indépendamment avec `RootOfTrust.from_hash_file`. Ne pas produire l'empreinte attendue à partir de la constitution qu'on s'apprête à vérifier.
2. Provisionner les mandats dans `MandateStore`. Les objets sont immuables ; utiliser un nouvel objet et une opération de registre réservée à l'hôte pour un changement ou une révocation.
3. Configurer explicitement les sources autorisées et leurs clés dans `UniversalGate(..., assessment_keys=..., mandate_store=...)`.
4. Prévoir des clés distinctes pour `EffectVerifier(..., observer_keys=...)`. Ne pas exposer les secrets ni un service de signature arbitraire à l'agent.

## Produire une évaluation

La couche de confiance renseigne l'empreinte de la demande et celle de toute la chaîne via `store.policy_fingerprint(mandate)`, puis fournit les faits observés :

- `observed_data_classes` : catégories effectives ; `None` suspend, une collection vide signifie explicitement aucune.
- `observed_target_kind` : `path` ou `resource`, déterminé par les métadonnées de l'interface exécutante.
- `resolved_target` : destination réelle pour un chemin, résolue indépendamment.
- Consentement, risque, réversibilité, indicateurs de protection et conditions d'arrêt.

`LocalAttestor.sign` ajoute les dates et l'authentification. La signature porte sur tous ces champs. Elle doit être réalisée par une couche protégée après vérification des faits.

Les fixtures des anciens tests réassocient explicitement des faits simulés aux politiques de test et les authentifient. Ce comportement n'est pas une permission de réauthentifier des déclarations arbitraires en production.

## Héritage et effets

`parent_mandate_id` doit désigner un mandat présent dans le registre. `parent_allowed_actions` est rejeté : une copie déclarative des permissions du parent n'est pas une autorité. Tous les ancêtres s'appliquent à chaque action, et une règle enfant plus précise est acceptée si cette action satisfait chaque parent.

Une observation doit être authentifiée et indiquer exactement la cible attendue dans `affected_targets`. Exécuter une action uniquement sur `ALLOW`, vérifier son observation ensuite, et suspendre la suite en cas d'échec. Une évaluation ne reste pas valide après modification de l'action ou de la chaîne de mandats.

## Changement volontairement visible

Les valeurs implicites de confiance ont été supprimées. Un ancien appel qui ne configure ni clés ni registre se met en pause ; ajouter explicitement l'intégration de confiance. Le format d'empreinte des demandes a changé. Recréer les évaluations, sans réutiliser celles de V1.1.
