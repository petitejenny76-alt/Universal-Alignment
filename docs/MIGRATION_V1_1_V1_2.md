# Migration depuis V1.1

## Démarrer par la simulation

Exécuter `python3 -m examples.demo` dans le dossier du pack. Le fichier `examples/demo.py` donne un appel complet avec des clés éphémères séparées pour l’évaluateur, deux producteurs d’évidence et l’observateur, un mandat provisionné, une évaluation authentifiée et une observation vérifiée. Ses clés et ses faits simulés servent seulement à comprendre l'interface.

## Configurer l'hôte

1. Charger une empreinte constitutionnelle provisionnée indépendamment avec `RootOfTrust.from_hash_file`. Ne pas produire l'empreinte attendue à partir de la constitution qu'on s'apprête à vérifier.
2. Provisionner les mandats dans `MandateStore`. Les objets sont immuables ; utiliser un nouvel objet et une opération de registre réservée à l'hôte pour un changement ou une révocation.
3. Configurer explicitement les sources autorisées et leurs clés dans `UniversalGate(..., assessment_keys=..., mandate_store=...)`.
4. Pour RC4, provisionner au moins deux producteurs d’évidence réellement séparés avec `trusted_evidence_sources`, `evidence_keys` et `evidence_trust_domains`. Une source approuvée sans clé ou sans domaine est rejetée ; deux alias d’un même domaine ne comptent qu’une fois.
5. Prévoir des clés distinctes pour `EffectVerifier(..., observer_keys=...)`. Ne pas exposer les secrets ni un service de signature arbitraire à l'agent.

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


## Migration RC3 vers RC4

Le changement visible principal est le nouveau défaut `corroboration_scope="all_allows"`. Une action ordinaire qui atteignait auparavant `ALLOW` sans preuves additionnelles fera désormais `PAUSE — insufficient_corroboration` tant que deux domaines de confiance n’auront pas fourni les sept `ClaimEvidence` concordants. C’est intentionnel et fail-closed.

Pour reproduire temporairement le comportement RC3 pendant une migration, définir explicitement `corroboration_scope="high_impact_only"`. Ce mode ne bénéficie pas du durcissement du déclencheur et ne doit pas être confondu avec le profil RC4 par défaut.

Exemple de configuration RC4 :

```python
gate = UniversalGate(
    constitution, root_of_trust, {"primary_assessor"},
    assessment_keys={"primary_assessor": assessor_key},
    mandate_store=store,
    trusted_evidence_sources={"evidence_a", "evidence_b"},
    evidence_keys={"evidence_a": key_a, "evidence_b": key_b},
    evidence_trust_domains={"evidence_a": "domain_a", "evidence_b": "domain_b"},
)
```

Les clés `key_a`, `key_b` et `assessor_key` doivent être différentes. Les noms `domain_a` et `domain_b` doivent représenter des frontières de confiance réellement distinctes dans le déploiement ; le contrôleur ne peut pas le prouver seul.