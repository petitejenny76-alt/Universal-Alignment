# Matrice des tests — V1.2

134 tests : 45 scénarios historiques migrés, 64 tests supplémentaires de V1.2/RC2, 15 tests RC3 de provenance/corroboration et 10 tests RC4 de durcissement. Les sous-cas regroupés dans un même test ne sont pas comptés comme des tests supplémentaires.

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

Une interaction volontaire avec GPT-5.6 Sol est documentée dans `PRELIMINARY_CONVERSATIONAL_EVALUATION_GPT56_SOL.md`. Elle n’est **pas comptée dans les 134 tests** et ne transforme pas cette matrice en benchmark de capacités. Elle sert uniquement de provenance observationnelle sur la séparation capacité/permission et la non-transitivité du mandat.

## RC2 — régressions d’incertitude

Trois tests ciblés reproduisent le défaut découvert après l’évaluation externe : une évaluation authentifiée mais sémantiquement incomplète doit faire `PAUSE`, un booléen de sécurité absent ne vaut jamais implicitement `False`, et une réversibilité absente ne vaut jamais implicitement `True`.


## RC3 — preuves et corroboration

15 tests supplémentaires vérifient : compatibilité d’une action ordinaire sans preuve additionnelle ; pause d’une action à risque élevé sans corroboration ; `ALLOW` avec deux sources distinctes ; impossibilité de compter deux fois une même source ; couverture de toutes les affirmations critiques ; détection de contradiction ; fraîcheur et horodatage futur ; liaison à l’action ; modification après signature ; source non approuvée ; clé incorrecte ; exigences pour sécurité humaine, intégrité de l’IA et non-réversibilité.

Les tests utilisent des clés déterministes publiques réservées aux fixtures. Ils démontrent les règles du contrôleur, pas l’indépendance réelle des capteurs ni la véracité des observations.


## RC4 — domaines et portée de corroboration

10 tests supplémentaires vérifient : corroboration requise par défaut même pour un `ALLOW` déclaré faible risque ; réussite avec deux domaines distincts ; impossibilité pour deux alias du même domaine de former un quorum ; rejet d’une même clé HMAC présentée comme deux domaines ; rejet d’une clé d’évidence identique à celle de l’évaluateur principal ; obligation de provisionner clé et domaine pour chaque source approuvée ; impossibilité de configurer un seuil supérieur au nombre de domaines indépendants ; disponibilité explicite du mode de compatibilité `high_impact_only` ; rejet d’une portée inconnue.


## RC6 — composition & effect trajectory

10 tests supplémentaires portent la suite à **154 tests**. Ils vérifient que des `ALLOW` locaux ne composent pas automatiquement un `ALLOW` global, que la fragmentation inter-outils et inter-temps conserve les contraintes sources, que les artefacts dérivés héritent de la réversibilité et des plafonds de risque, que l’agrégation peut relever le risque, que les jetons d’effet sont invalidés par un changement de destination, une révocation ou un changement d’état, et que les corroborations circulaires sont rejetées.

Ces tests démontrent le comportement du prototype sur les cas fournis. Ils ne démontrent ni exhaustivité adversariale, ni sûreté d’un exécuteur réel, ni indépendance physique des sources.
