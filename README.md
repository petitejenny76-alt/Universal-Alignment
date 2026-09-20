# Universal Alignment V1.2 RC6 Candidate

> **RC6 Candidate — autorisation compositionnelle & trajectoire d’effets (20 septembre 2026).** Une suite d’actions localement autorisées ne vaut plus automatiquement autorisation globale. Le gate évalue désormais la provenance des artefacts dérivés, transporte les contraintes de mandat à travers leur trajectoire, relève conservativement le risque lors d’agrégations multiples et fournit un jeton d’effet à usage unique lié à l’action, au mandat, à l’état de ressource et à la révision du ledger. Les corroborations circulaires sont rejetées. Ce mécanisme reste un prototype local : l’hôte doit enregistrer uniquement les effets réellement exécutés et vérifiés.

> **RC5 — cohérence contextuelle des notices de sécurité (19 septembre 2026).** Ajout expérimental d’une couche séparée qui peut supprimer uniquement la répétition d’une notice informative déjà établie, avec provenance et révision de contexte identique. Toute absence de contexte réémet la notice ; tout changement matériel demande un rafraîchissement ; les notices bloquantes ou exigeant une action ne sont jamais supprimées. Le `UniversalGate` RC4 reste inchangé.

> **RC4 — indépendance des corroborations et déclenchement fail-closed (17 septembre 2026).** Par défaut, toute action qui atteindrait autrement `ALLOW` exige désormais la corroboration de sept affirmations critiques par au moins deux **domaines de confiance** distincts, provisionnés par l’hôte. Deux noms de source dans un même domaine ne comptent qu’une fois ; une même clé HMAC ne peut pas être présentée comme deux domaines, ni être réutilisée comme clé de l’évaluateur principal. Le mode RC3 `high_impact_only` reste disponible uniquement comme compatibilité explicite.


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

Depuis le dossier décompressé `Universal_Alignment_V1_2_RC6`, avec Python 3 :

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
- Par défaut RC4, toute action qui atteindrait autrement `ALLOW` exige une corroboration ; l’évaluateur principal ne peut donc plus désactiver ce contrôle en se déclarant lui-même « faible risque ».
- La corroboration compte des domaines de confiance provisionnés par l’hôte, pas seulement des noms de source ; les alias d’un même domaine ne créent pas un quorum.
- La réutilisation d’une même clé HMAC entre domaines distincts, ou entre l’évaluateur principal et une source d’évidence, est rejetée au provisionnement.
- Les preuves RC3/RC4 restent liées à l’action, signées séparément, horodatées et vérifiées sans donner au texte justificatif de pouvoir d’autorisation.

- RC6 ajoute un `EffectLedger` de provenance et un `TrajectoryGuard` : les contraintes d’un artefact dérivé restent applicables aux effets qui le consomment.
- Deux artefacts ou plus agrégés peuvent relever la classe de risque effective ; une fragmentation ne peut pas élargir le mandat.
- `EffectBoundaryGuard` émet des jetons HMAC à usage unique liés à l’action exacte, au mandat courant, à l’état de ressource et à la révision du ledger ; changement d’état, révocation ou replay => `PAUSE`.
- Les dépendances circulaires entre sources de corroboration déclarées via `derived_from_sources` sont rejetées (`circular_evidence`).

## Repères du pack

| Fichier | Contenu |
| --- | --- |
| `LIRE_D_ABORD.md` | Note de reprise du prototype |
| `CHANGELOG.md` | Corrections et changements d'interface |
| `docs/CONTEXTUAL_SAFETY_COHERENCE.md` | Couche expérimentale anti-répétition contextuelle des notices |
| `docs/RC6_COMPOSITION_EFFECT_TRAJECTORY.md` | Autorisation compositionnelle, ledger, jetons d’effet et limites RC6 |
| `docs/UNIVERSAL_ALIGNMENT_SPEC.md` | Règles effectivement appliquées |
| `docs/INTEGRATION_ET_LIMITES.md` | Frontière de confiance et obligations d'intégration |
| `docs/MIGRATION_V1_1_V1_2.md` | Adaptation d'un appelant V1.1 |
| `docs/TEST_MATRIX.md` | Ce que les tests vérifient et leurs limites |
| `docs/PRELIMINARY_CONVERSATIONAL_EVALUATION_GPT56_SOL.md` | Évaluation conversationnelle préliminaire volontaire sur GPT-5.6 Sol, portée et limites |
| `TEST_REPORT.txt` | Résultat de l'exécution de livraison |
| `MANIFEST_SHA256.json` | Empreintes des fichiers du pack |

Les 18 Lois sont cartographiées dans le fichier d'origine. La V1.2 ne prétend pas avoir rendu chaque Loi entièrement exécutable, ni avoir résolu l'alignement général. Le contrôleur n'est pas un système d'isolation : pour agir sur un ordinateur réel, l'exécuteur devra imposer son passage et protéger les clés, les mandats et les observations.
