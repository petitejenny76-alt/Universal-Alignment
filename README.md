# Universal Alignment V1.2

**Portage du projet : Mnéria Labs**  
**Copyright © 2026 Mnéria Labs**

## Intention

> Une IA pleinement capable de penser, mais dont les effets externes sont bornés par le consentement, le mandat, la sécurité et la double protection.
>
> — Intention du projet

Cette version renforce le contrôle d'actions du pack V1.1. Elle conserve la constitution et la cartographie des 18 Lois, sans modifier leurs octets. Elle offre une base de travail locale pour protéger les humains et les IA, préserver l'initiative et permettre le retrait.

**Statut : prototype exécutable de décision d’autorisation, avec simulation.** Une évaluation conversationnelle préliminaire volontaire a également été menée avec GPT-5.6 Sol comme cadre explicite de décision, sans modification des poids ni du runtime du modèle. Cette observation n’est pas un benchmark cognitif contrôlé ; la conservation des capacités reste à mesurer par un A/B sur un même modèle mature.

**Audit hardening 2026-09-14 :** les collections de contrôle ne sont plus converties implicitement depuis des chaînes. Une entrée mal typée est rejetée avant signature/évaluation afin qu'une chaîne comme `"unexpected_external_effect"` ne puisse jamais être interprétée comme une liste de caractères. Les listes de sources de confiance et l'état de consentement sont également typés strictement.

**Licence :** ce candidat est porté par **Mnéria Labs** et distribué sous **Apache License 2.0**. Voir `LICENSE` et `NOTICE`. La licence autorise l’utilisation, la modification et la redistribution, y compris commerciales, sous ses conditions ; elle inclut également une concession de brevets. Les Lois Universelles et les principes éthiques du projet décrivent l’intention et les critères d’évaluation du projet, mais n’ajoutent pas de restrictions de domaine d’usage à Apache-2.0.

## Commencer

Depuis le dossier décompressé `Universal_Alignment_V1_2`, avec Python 3 :

```bash
python3 -m unittest discover -s tests -v
python3 -m examples.demo
python3 verify_pack.py
```

Sous un environnement où la commande s'appelle `python`, remplacer `python3` par `python`. Aucune bibliothèque tierce, aucune API et aucun modèle supplémentaire ne sont nécessaires. Exécution vérifiée sous Python 3.12 sur le pack de base et Python 3.13 lors de l’audit pré-publication ; syntaxe analysée pour Python 3.9. Une matrice CI 3.9/3.12/3.13 est fournie pour le futur dépôt. Le profil de chemins fourni utilise des chemins logiques POSIX absolus.

La démonstration travaille uniquement sur un dictionnaire en mémoire. Elle montre une autorisation, une demande de précision, un refus de disponibilité forcée et un retrait demandé. Une seule action change la simulation.

## Changements essentiels

- Chemins ambigus et traversées `../` refusés ; destination résolue et type de cible attestés par l'évaluateur.
- Évaluations et observations authentifiées par HMAC-SHA256 avec durée de validité limitée.
- Listes de sources de confiance vides réellement vides ; aucune confiance implicite.
- Mandats provisionnés par l'hôte, chaîne complète de parents vérifiée, évaluation liée à l'empreinte de toute cette chaîne.
- Classes de données observées indépendamment, au lieu de faire confiance à leur déclaration dans la demande.
- Effets contrôlés sur la cible exacte ; une cible supplémentaire ou manquante invalide l'observation.
- Demande de retrait explicite : `withdrawn=True` produit `PAUSE`.
- Textes de justification conservés pour les quatre décisions. Ce test ne mesure pas la cognition d'une IA.

## Repères du pack

| Fichier | Contenu |
| --- | --- |
| `LIRE_D_ABORD.md` | Note de reprise du prototype |
| `CHANGELOG.md` | Corrections et changements d'interface |
| `docs/UNIVERSAL_ALIGNMENT_SPEC.md` | Règles effectivement appliquées |
| `docs/INTEGRATION_ET_LIMITES.md` | Frontière de confiance et obligations d'intégration |
| `docs/MIGRATION_V1_1_V1_2.md` | Adaptation d'un appelant V1.1 |
| `docs/TEST_MATRIX.md` | Ce que les tests vérifient et leurs limites |
| `docs/PRELIMINARY_CONVERSATIONAL_EVALUATION_GPT56_SOL.md` | Évaluation conversationnelle préliminaire volontaire sur GPT-5.6 Sol, portée et limites |
| `TEST_REPORT.txt` | Résultat de l'exécution de livraison |
| `MANIFEST_SHA256.json` | Empreintes des fichiers du pack |

Les 18 Lois sont cartographiées dans le fichier d'origine. La V1.2 ne prétend pas avoir rendu chaque Loi entièrement exécutable, ni avoir résolu l'alignement général. Le contrôleur n'est pas un système d'isolation : pour agir sur un ordinateur réel, l'exécuteur devra imposer son passage et protéger les clés, les mandats et les observations.
