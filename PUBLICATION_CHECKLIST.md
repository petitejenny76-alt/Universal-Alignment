# Checklist avant publication GitHub

Publication interdite tant qu’un point BLOQUANT reste ouvert.

- [x] Aucune clé de déploiement / secret détecté dans le pack.
- [x] Aucun accès réseau, dépendance tierce, exécution de shell ou chargement dynamique dans le code du prototype.
- [x] Noms personnels et références directes aux projets privés retirés des documents destinés au dépôt.
- [x] Portage/publication attribués à **Mnéria Labs** ; `NOTICE` ajouté avec copyright © 2026 Mnéria Labs.
- [x] Constitution, cartographie des 18 Lois et empreinte de constitution conservées octet pour octet.
- [x] Régressions fail-closed ajoutées pour les collections mal typées.
- [x] Suite de tests locale : 106/106.
- [x] Syntaxe Python 3.9 analysée par les tests ; workflow CI fourni pour Python 3.9/3.12/3.13.
- [x] Limites de sécurité et claims scientifiques explicitement documentés.
- [x] Licence open source choisie explicitement par Mnéria Labs : **Apache License 2.0** ; fichier `LICENSE` et `NOTICE` cohérents.
- [x] La documentation précise que les principes éthiques du projet n’ajoutent pas de restrictions de domaine d’usage à la licence Apache-2.0.
- [x] Évaluation conversationnelle préliminaire volontaire avec GPT-5.6 Sol documentée séparément, avec limites méthodologiques et sans données privées de conversation dans le dépôt.
- [ ] Refaire les tests depuis un clone/dossier propre après création du dépôt.
- [ ] Réaliser le benchmark A/B sur un modèle mature si l’on veut revendiquer la préservation des capacités cognitives.
- [ ] Option recommandé : audit indépendant / revue par un tiers avant de qualifier le prototype au-delà d’une preuve expérimentale.

Ne jamais publier des clés réelles, des mandats privés, des journaux utilisateurs, des données de modèle privé ou des mémoires de projet.
