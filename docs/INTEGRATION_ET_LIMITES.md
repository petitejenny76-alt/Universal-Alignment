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
