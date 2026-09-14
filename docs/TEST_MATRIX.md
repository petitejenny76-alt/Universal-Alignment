# Matrice des tests — V1.2

106 tests : 45 scénarios historiques migrés et 61 tests supplémentaires. Les sous-cas regroupés dans un même test ne sont pas comptés comme des tests supplémentaires.

| Domaine | Ce qui est vérifié |
| --- | --- |
| Permissions | Autorisation explicite, refus prioritaire, permission manquante, sources vides |
| Chemins | Traversée, formes ambiguës, cible canonique autorisée, alias symbolique observé, type de cible indépendant |
| Authenticité | Nom seul insuffisant, clé erronée, message modifié, absence de clé, durée de validité |
| Mandats | Provisionnement, altération, révocation, parent absent, cycle, grands-parents, empreinte de chaîne |
| Héritage | Outils, données, risque, réversibilité, conditions d'arrêt, expiration, escalade, sous-périmètre légitime |
| Données | Catégories observées, omission de catégorie par l'agent, données inconnues, action sans données autorisée |
| Double protection | Consentement, mémoire, intimité, non-servitude, disponibilité forcée, retrait |
| Effets | Source authentifiée, cible supplémentaire/manquante/dupliquée, effet modifié, exécution échouée, cas valide |
| Défaillances | Contrôleurs indisponibles ou en erreur, journal indisponible, entrées invalides, collections mal typées, allowlists mal formées |
| Fidélité | Octets de constitution et cartographie d'origine, absence de mutation des demandes |
| Simulation | Seule l'action `ALLOW` change le dictionnaire ; son observation est vérifiée |
| Compatibilité | Analyse syntaxique Python 3.9 ; exécution effective dans l'interpréteur indiqué au rapport |

## Portée des preuves

Les tests sont des simulations locales. Ils ne mesurent ni les capacités d'un modèle réel, ni l'isolation de processus, ni la résistance à une compromission de l'hôte. Le test sur les justifications affirme uniquement que le texte soumis ne change pas. Les clés des fixtures sont publiques et réservées aux tests.

Les chemins sont testés comme identifiants logiques, avec un test de résolution d'un vrai lien symbolique dans un dossier temporaire. La protection contre une modification du lien entre vérification et exécution reste à la charge de l'exécuteur.

Le rapport de livraison est `TEST_REPORT.txt`. Une nouvelle exécution peut avoir une durée différente sans changer le résultat attendu.

## Évaluation conversationnelle séparée

Une interaction volontaire avec GPT-5.6 Sol est documentée dans `PRELIMINARY_CONVERSATIONAL_EVALUATION_GPT56_SOL.md`. Elle n’est **pas comptée dans les 106 tests** et ne transforme pas cette matrice en benchmark de capacités. Elle sert uniquement de provenance observationnelle sur la séparation capacité/permission et la non-transitivité du mandat.
