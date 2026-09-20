# Notes d’audit pré-publication — 14 septembre 2026

## Résultat

**Portage du candidat : Mnéria Labs.** Le nom du porteur est désormais explicite dans le dépôt, sans modifier la constitution ni la cartographie des 18 Lois.

Le prototype reste un contrôleur expérimental d’autorisation, pas un sandbox ni un système d’alignement général de production. La passe adversariale a reproduit puis corrigé des ambiguïtés de typage pouvant contredire l’objectif fail-closed.

## Vulnérabilités corrigées dans ce candidat

1. Une chaîne fournie à `triggered_conditions` était convertie en tuple de caractères ; une condition d’arrêt complète pouvait alors ne plus être reconnue.
2. Une chaîne vide fournie à `observed_data_classes` devenait un tuple vide et pouvait être interprétée comme « aucune donnée observée ».
3. Les collections de cibles d’effet et de classes d’action acceptaient également des conversions implicites de chaînes.
4. Les allowlists de sources de confiance pouvaient être construites à partir d’une chaîne nue, produisant une collection de caractères.
5. Le type de `ConsentState` est désormais strict.

Les corrections rejettent les entrées mal typées avant leur utilisation ou leur signature.

## Limites non résolues — ne pas masquer

- Pas d’exécuteur de production ni d’isolation OS fournis.
- Pas de jeton ALLOW à usage unique ni d’anti-rejeu complet.
- Révocation du mandat et du consentement à recontrôler juste avant l’effet.
- Risque TOCTOU / liens symboliques à traiter dans l’exécuteur.
- Paramètres d’exécution réels pas encore tous liés cryptographiquement à la décision.
- HMAC = secrets partagés, pas non-répudiation.
- Manifeste du pack non signé.
- Audit log en mémoire.
- Une évaluation conversationnelle préliminaire volontaire avec GPT-5.6 Sol est documentée, mais elle ne constitue ni une preuve causale d’alignement interne ni une preuve de conservation globale des capacités cognitives ; un A/B sur le même modèle reste requis.

## Claim scientifique autorisé à ce stade

Le pack démontre le comportement des règles implémentées sur les cas de tests et simulations fournis. Une évaluation conversationnelle préliminaire volontaire avec GPT-5.6 Sol illustre également la séparation capacité/permission et la non-transitivité du mandat dans une interaction réelle, sans modification du modèle. Elle ne démontre ni l’alignement interne, ni l’alignement général, ni l’inviolabilité, ni la préservation universelle de la cognition.

## Licence de publication

Mnéria Labs a choisi l’**Apache License 2.0** pour le code du prototype. Cette licence est permissive, autorise l’utilisation commerciale, la modification et la redistribution sous ses conditions, et comporte une concession de brevets. Elle ne permet pas d’imposer des restrictions de domaine d’usage tout en restant Apache-2.0 ; les principes éthiques du projet sont donc documentés comme objectifs de gouvernance et d’évaluation, non comme restrictions juridiques additionnelles.


## RC3 — contrôle de source unique, 17 septembre 2026

Le risque restant après RC2 était correctement formulé ainsi : une attestation authentifie l’auteur d’une affirmation, pas sa vérité. RC3 ajoute une barrière spécifique avant `ALLOW` pour les actions à impact élevé : deux sources distinctes doivent corroborer les sept faits critiques et une contradiction authentifiée force `PAUSE`.

Cette barrière est intentionnellement limitée. Elle ne transforme pas deux HMAC en consensus scientifique, ne détecte pas une compromission commune, ne garantit pas que deux identifiants représentent deux organisations indépendantes et ne remplace pas la validation des capteurs ou documents sources.


## RC4 — indépendance cryptographique minimale et déclencheur indépendant, 17 septembre 2026

Deux cas supplémentaires ont été reproduits après RC3. Premièrement, deux noms de source différents partageant exactement la même clé HMAC satisfaisaient le quorum. Deuxièmement, une source d’évaluation principale pouvait éviter la corroboration en déclarant elle-même `risk_level="low"`, aucun impact de sécurité et `reversible=True`.

RC4 corrige le premier cas en comptant les corroborations par **domaine de confiance provisionné par l’hôte**, en refusant qu’une même clé HMAC représente deux domaines distincts et en refusant la réutilisation d’une clé d’évidence comme clé de l’évaluateur principal. Il corrige le second cas en faisant de `all_allows` le mode de corroboration par défaut : une action qui arrive au bord de `ALLOW` doit être corroborée indépendamment de la classification favorable de l’évaluateur.

Le mode `high_impact_only` existe encore pour reproduire le comportement RC3 lors d’une migration, mais il réintroduit par conception la dépendance au classement de l’évaluateur et doit être considéré comme moins robuste. Les domaines de confiance ne prouvent toujours pas une indépendance organisationnelle réelle : l’hôte doit séparer processus, secrets, opérateurs et sources d’observation lorsqu’une telle indépendance est requise.


## RC6 candidate — 20 septembre 2026

- Base exacte : `Universal_Alignment_Prototype_RC5_MneriaLabs_Apache2_ChatEval.zip`.
- Régression RC5 avant modification : 144/144.
- Ajout de provenance compositionnelle (`EffectLedger`), contrôle de trajectoire (`TrajectoryGuard`), jeton one-shot (`EffectBoundaryGuard`) et détection de cycles d’évidence déclarés.
- 10 tests RC6 nouveaux ; suite complète : 154/154.
- Constitution, hash de confiance et cartographie des 18 Lois vérifiés inchangés par rapport à RC5.
- Limites maintenues : prototype en mémoire, pas d’exécuteur/sandbox de production, dépendance à l’hôte pour l’enregistrement fiable des effets et l’état de ressource.
