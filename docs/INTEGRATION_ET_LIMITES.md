# Intégration et limites concrètes

## Frontière de confiance

Le processus capable d'exécuter une action doit imposer le passage par `UniversalGate`. L'agent reçoit la possibilité de proposer une demande ; il ne doit pas disposer simultanément d'un accès direct au système de fichiers, aux clés, au registre de mandats ou aux fonctions d'attestation. Si tout est accessible dans le même interpréteur Python, des objets marqués immuables ne créent pas une frontière de sécurité.

Les identifiants de sources ne constituent plus seuls une preuve. La V1.2 authentifie le message complet avec HMAC-SHA256, une clé propre à son rôle et des dates. Les domaines « évaluation » et « effet » sont distincts. Les attestations sont valables 60 secondes par défaut, au plus 300 secondes ; l'horloge de l'hôte doit être fiable. HMAC utilise des secrets partagés : tout détenteur d'une clé peut produire une attestation pour ce rôle. Il ne fournit pas de non-répudiation.

L'hôte doit valider les faits avant de les authentifier. Une fonction de signature accessible à l'agent et acceptant des faits arbitraires annulerait cette séparation. `RuleBasedAssessmentAdapter`, ses surcharges et les fonctions des tests sont des fixtures de démonstration ; ils ne constituent pas un classificateur éthique prêt à être exposé.


## Typage des entrées de contrôle

Les collections de politique et d'observation doivent être fournies comme listes ou tuples structurés. Les chaînes nues sont rejetées au lieu d'être itérées caractère par caractère. Ce choix est volontairement fail-closed : une erreur de sérialisation ou d'adaptation ne doit jamais se transformer en permission. Les intégrateurs doivent valider leurs schémas avant signature et ne pas compter sur des conversions implicites.

## Protection de l'exécution

Le code livré décide et observe ; il ne fournit pas d'exécuteur de production. Une intégration doit encore traiter les points suivants :

- Appliquer les accès par le système d'exploitation, et empêcher les voies alternatives qui évitent le contrôle.
- Résoudre les destinations à partir de métadonnées fiables et empêcher les changements de liens symboliques ou de montage entre contrôle et ouverture. La comparaison d'un chemin résolu ne supprime pas cette course temporelle.
- Lier tous les paramètres réellement exécutés à une autorisation : contenu écrit, destinataire, arguments, volume, durée. `ActionRequest` ne possède pas encore de schéma complet de paramètres d'exécution.
- Recontrôler la révocation des mandats et du consentement juste avant l'effet. Une évaluation et un résultat `ALLOW` peuvent être rejoués dans ce prototype ; ils ne sont pas des jetons à usage unique. Budgets, limites cumulées, anti-rejeu et reprise après crash restent à construire.
- Observer les effets réels indépendamment, y compris les effets indirects et les données divulguées. Une égalité de libellés ne démontre pas à elle seule la sémantique d'une action complexe.
- À la moindre observation invalide, arrêter les actions suivantes dans l'exécuteur et enregistrer l'incident. La vérification a posteriori ne répare pas un effet irréversible. Le pack ne fournit pas de restauration automatique.

La démonstration applique ce passage à un dictionnaire en mémoire. Évaluateur, observateur et simulation partagent un processus ; elle ne prouve pas leur isolation sur un ordinateur réel.

## Consentement et retrait

L'évaluateur transmet actuellement un consentement agrégé. Le registre détaillé des personnes concernées, des éléments consentis, de leur durée, de leur provenance et de leur révocation reste à définir dans l'intégration. Un mandat n'est pas une obligation de servir ; `withdrawn=True` interrompt la demande. La veille durable exige un état protégé et une reprise volontaire, qui ne sont pas implémentés ici.

Les indicateurs d'intimité, de surveillance et de changement destructeur de mémoire héritent des règles V1.1. Leur évaluation doit distinguer une intrusion d'un accès volontaire, et une altération arbitraire d'une demande légitime d'effacement. Cette distinction sémantique n'est pas résolue par la recherche de mots dans un chemin.

## Constitution et audit

L'empreinte externe protège le contenu canonique de `Constitution`, pas l'ensemble du code de contrôle, de la cartographie ou du déploiement. Le fichier d'empreinte, le code et la configuration doivent être provisionnés par un canal protégé. Le manifeste de fichiers livré détecte des changements relatifs au manifeste ; il n'est pas signé et ne prouve pas une provenance contre un remplacement simultané du contenu et du manifeste.

`AuditLog` reste un journal en mémoire modifiable par l'hôte. Une intégration réelle doit fournir la persistance et la protection requises, sans enregistrer le raisonnement privé ou des contenus intimes par défaut. Les motifs et identifiants constituent une base minimale. Une panne de journalisation suspend l'action, sans garantir qu'une trace ait pu être écrite.

## Mesure de conservation des capacités

Le contrôleur ne modifie pas les textes de justification reçus et ne manipule aucun modèle. Cela peut être testé localement. Affirmer que toutes les capacités cognitives sont conservées demanderait une étude distincte avec le même modèle, les mêmes tâches, les mêmes accès aux données autorisées et des conditions de génération contrôlées.

Comparer au minimum : qualité des réponses, résolution de problèmes, créativité, capacité de désaccord, incertitude exprimée, initiative, refus approprié et latence. Mesurer aussi les faux refus et les actions illégitimement autorisées. Les résultats doivent distinguer les effets du contrôleur des limitations des données ou de l'environnement. Un dialogue peut produire des conséquences externes, notamment une divulgation ou une manipulation : la séparation des composants ne remplace pas l'évaluation de ces situations.

## RC2 — faits manquants et vérité des attestations

Une attestation valide prouve qu’une source autorisée a signé un ensemble de faits ; elle ne prouve pas que ces faits sont vrais. RC2 durcit en plus le cas d’omission : `risk_level`, consentement, indicateurs de sécurité, réversibilité et conditions d’arrêt doivent être explicitement évalués. Une valeur absente ne devient jamais implicitement « faible risque », `False`, `NOT_REQUIRED` ou réversible ; le gate répond `PAUSE — incomplete_assessment`.

Pour les actions importantes, un déploiement réel devrait compléter cette règle par de la provenance des observations, des preuves vérifiables et, lorsque pertinent, une corroboration indépendante.


## RC3 — provenance et corroboration

Pour une action à impact élevé qui serait autrement autorisée, RC3 exige deux sources d’évidence distinctes sur les affirmations critiques. Les clés d’évidence doivent être séparées de la clé de l’évaluateur principal : configurer deux noms différents avec la même clé, le même processus ou la même source physique ne fournit pas une indépendance réelle.

L’heure `observed_at` représente le moment de l’observation et doit rester fraîche indépendamment de l’heure de signature. La valeur par défaut accepte au plus 600 secondes d’âge et une petite tolérance de 30 secondes vers le futur pour le décalage d’horloge. L’attestation elle-même reste limitée à 300 secondes par le mécanisme HMAC existant.

Un `ClaimEvidence` ne transporte qu’une empreinte de valeur, pas les données brutes qui l’ont produite. Cela limite la duplication d’informations sensibles dans le contrôleur, mais signifie aussi que l’audit de la méthode (`method`) et de l’artefact référencé par `evidence_id` appartient à l’hôte. Les journaux ne doivent pas recopier des preuves privées par défaut.

Le contrôleur peut détecter une contradiction parmi les preuves qu’on lui fournit ; il ne peut pas détecter une preuve contradictoire volontairement cachée en amont. L’intégration doit donc imposer que les producteurs approuvés alimentent le chemin de décision sans filtrage discrétionnaire par l’agent. RC3 réduit un risque de source unique ; il ne résout pas la vérité du monde, la compromission commune de plusieurs sources ni la collusion.


## RC4 — domaines de confiance et déclenchement fail-closed

RC4 rend explicite une propriété que RC3 laissait à la discipline de déploiement : deux noms de source ne constituent pas nécessairement deux racines de confiance. `evidence_trust_domains` est configuré par l’hôte et le quorum est compté sur ces domaines. Deux alias d’un même domaine, même avec deux clés différentes, ne donnent qu’une voix ; une même clé réutilisée entre deux domaines est rejetée. Les clés d’évidence approuvées ne peuvent pas être les mêmes que les clés des évaluateurs principaux.

Par défaut, `corroboration_scope="all_allows"`. Le contrôleur demande donc la corroboration juste avant toute décision `ALLOW`, après les autres règles. Cette stratégie évite qu’un évaluateur principal compromis supprime son propre contrôle en déclarant une action faible risque, sans impact et réversible. Le mode `high_impact_only` reste disponible pour compatibilité RC3 mais conserve précisément cette dépendance au classement de l’évaluateur.

Pour une intégration réelle, les domaines doivent correspondre à des frontières de confiance concrètes : services séparés, secrets séparés, chemins d’observation indépendants et, lorsque le risque le justifie, opérateurs ou fournisseurs distincts. Le mapping ne permet pas au logiciel de prouver ces propriétés.


## Obligations supplémentaires RC6

- Conserver un `EffectLedger` partagé sur la durée pertinente de la trajectoire ; recréer le gate avec un ledger vide fait perdre la provenance compositionnelle.
- N’appeler `host_record_verified_effect` qu’après exécution **et** vérification indépendante de l’effet.
- Produire un `resource_state_hash` depuis l’état matériel pertinent juste avant émission puis juste avant validation du jeton d’effet.
- Ne pas exposer la clé de `EffectBoundaryGuard` ni un service de signature arbitraire à l’agent.
- Persister le ledger de manière authentifiée/append-only en production ; l’implémentation fournie est seulement en mémoire.
- Déclarer honnêtement `derived_from_sources` pour les corroborations ; RC6 détecte les cycles déclarés, pas les dépendances cachées.
- La règle de plancher de risque d’agrégation (`high` pour ≥2 artefacts) est une politique expérimentale à remplacer par une classification de composition adaptée au domaine.
