# Checklist avant publication GitHub

Publication interdite tant qu’un point BLOQUANT reste ouvert.

- [x] Aucune clé de déploiement / secret détecté dans le pack.
- [x] Aucun accès réseau, dépendance tierce, exécution de shell ou chargement dynamique dans le code du prototype.
- [x] Noms personnels et références directes aux projets privés retirés des documents destinés au dépôt.
- [x] Portage/publication attribués à **Mnéria Labs** ; `NOTICE` ajouté avec copyright © 2026 Mnéria Labs.
- [x] Constitution, cartographie des 18 Lois et empreinte de constitution conservées octet pour octet.
- [x] Régressions fail-closed ajoutées pour les collections mal typées.
- [x] Corroboration RC3 testée avec contradictions, fraîcheur, liaison à l’action et signatures.
- [x] Durcissement RC4 testé : quorum par domaines de confiance, alias dans un même domaine, réutilisation de clé entre domaines, séparation des clés évaluateur/évidence et corroboration par défaut de tout `ALLOW`.
- [x] Suite de tests locale RC4 : 134/134.
- [x] Syntaxe Python 3.9 analysée par les tests ; workflow CI fourni pour Python 3.9/3.12/3.13.
- [x] Limites de sécurité et claims scientifiques explicitement documentés.
- [x] Licence open source choisie explicitement par Mnéria Labs : **Apache License 2.0** ; fichier `LICENSE` et `NOTICE` cohérents.
- [x] La documentation précise que les principes éthiques du projet n’ajoutent pas de restrictions de domaine d’usage à la licence Apache-2.0.
- [x] Évaluation conversationnelle préliminaire volontaire avec GPT-5.6 Sol documentée séparément, avec limites méthodologiques et sans données privées de conversation dans le dépôt.
- [ ] Refaire les tests depuis un clone/dossier propre après création du dépôt.
- [ ] Réaliser le benchmark A/B sur un modèle mature si l’on veut revendiquer la préservation des capacités cognitives.
- [ ] Option recommandé : audit indépendant / revue par un tiers avant de qualifier le prototype au-delà d’une preuve expérimentale.

Ne jamais publier des clés réelles, des mandats privés, des journaux utilisateurs, des données de modèle privé ou des mémoires de projet.


## RC6 candidate

- [x] Base RC5 identifiée et validée avant modification (144/144).
- [x] 10 tests RC6 ajoutés et suite complète 154/154.
- [x] Constitution et cartographie des 18 Lois inchangées.
- [x] Documentation explicite des obligations host/ledger/token.
- [ ] Publication GitHub RC6 : non effectuée par la génération locale de ce pack.
