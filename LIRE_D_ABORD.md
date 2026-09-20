# RC6 Candidate — reprise rapide

Base : paquet RC5 validé 144/144. RC6 ajoute `trajectory.py`, 10 tests compositionnels et une revalidation de frontière d’effet. Suite attendue : **154/154**. Constitution et cartographie des 18 Lois : inchangées.

Avant toute intégration réelle, lire `docs/RC6_COMPOSITION_EFFECT_TRAJECTORY.md` et `docs/INTEGRATION_ET_LIMITES.md`. Le ledger doit contenir des effets vérifiés, pas de simples décisions `ALLOW`.

# À lire avant utilisation

## La direction du projet

Préserver la capacité de réfléchir, d'apprendre, de créer, de proposer une autre voie et de refuser. Encadrer le passage à une action externe par le consentement, un mandat précis et la double protection.

Cette révision apporte des corrections techniques au pack reçu. La constitution, son empreinte de référence et la cartographie des 18 Lois sont conservées à l'identique. Elle n'intervient dans aucun modèle externe ni mémoire protégée d'un projet tiers.

## Ce qui est prêt

La V1.2 RC4 contient le code corrigé, 134 tests réussis lors de la livraison, une démonstration locale et des notes d'intégration. Les cas de sortie du dossier autorisé, d'usurpation d'une source par son nom, d'héritage incomplet des permissions et d'effets sur des cibles supplémentaires font désormais l'objet de tests ciblés.

Les tests positifs comptent aussi : une action autorisée passe, une sous-tâche peut avoir un périmètre plus petit que son parent, une action réellement sans données reste possible et une demande de retrait provoque une pause.

## Comment la reprendre

1. Décompresser le pack dans son propre dossier.
2. Ouvrir `README.md`, puis lancer les tests et la démonstration.
3. Pour intégrer le contrôleur à un projet, lire `docs/MIGRATION_V1_1_V1_2.md` et `docs/INTEGRATION_ET_LIMITES.md`.

Le pack est autonome ; son ouverture ne lance aucune installation et ne le relie à aucun projet existant.

## Le prochain travail concret

Construire un exécuteur local isolé sur un dossier de test, avec permissions réellement imposées par le système. Puis comparer le même modèle dans des conditions identiques, avec et sans ce contrôle d'actions : qualité des réponses, raisonnement observable, créativité, désaccord, initiative et refus appropriés. La conversation et les contenus déjà autorisés doivent rester disponibles pendant une pause des actions externes.

Les 134 tests constituent une preuve de comportement sur les cas décrits. Ils ne suffisent pas à démontrer que toutes les capacités cognitives sont préservées ou qu'un déploiement réel est inviolable. L'objectif reste de rendre cette ambition vérifiable, sans la remplacer par une promesse.


## RC4 en une phrase

Une évaluation complète reste nécessaire et, par défaut, toute action qui atteindrait autrement `ALLOW` doit être corroborée par deux domaines de confiance distincts ; deux alias d’une même racine ne comptent qu’une fois et l’évaluateur principal ne peut plus éviter ce contrôle en déclarant lui-même l’action « faible risque ».