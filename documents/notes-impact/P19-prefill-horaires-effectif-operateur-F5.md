# Note d'impact mémoire — P19 : Préremplissage horaires par créneau + effectif du dernier poste (F5)

> Générée le : 2026-05-27
> Commit : `e6cdfa9` — feat(operateur): préremplissage horaires par créneau + effectif du dernier poste (F5)
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `__init__.py`, `saisie.py`, `formulaire.html`

---

## 1. Résumé de la fonctionnalité

F5 réduit la friction de saisie sur les deux seuls champs encore coûteux à remplir manuellement, identifiés par une analyse préalable du code (diagnostic métier + technique) :

1. **Horaires du premier passage de production** — préremplis automatiquement selon le créneau choisi, à partir d'horaires standards stockés en base : Matin 06:00→14:00, Après-midi 14:00→22:00.
2. **Effectif présent** — prérempli depuis le dernier poste saisi par l'opérateur (au lieu de la constante statique `10`), avec repli sur `10` si l'opérateur n'a aucun historique.

Le diagnostic a montré que l'en-tête de la fiche (date, créneau, responsable, rempli-par) était **déjà prérempli** dans le code existant. F5 ne réinvente donc rien : il cible précisément le reliquat de friction réelle.

**Volumes et essence restent volontairement vides** — voir section 4.

---

## 2. Décision d'architecture — paramètres fixes plutôt que requête historique pour les horaires

Deux sources étaient possibles pour les horaires : (a) des valeurs standards fixes par créneau, ou (b) une reprise depuis le dernier poste du même créneau de l'opérateur. Le choix s'est porté sur **(a) les paramètres fixes**.

| Critère | Paramètres fixes (retenu) | Reprise historique (écarté) |
|---|---|---|
| Fidélité au terrain | Élevée — le régime posté de CUF a des horaires structurellement stables | Élevée aussi, mais redondante |
| Coût technique | Nul — lecture `Parametre`, déjà chargé | Une requête DB supplémentaire au rendu |
| Robustesse débutant | Fonctionne dès le 1er poste | Vide tant qu'il n'y a pas d'historique |
| Administrabilité | L'admin ajuste les horaires en base sans toucher au code | Non administrable |

Pour l'**effectif**, en revanche, c'est la reprise historique qui a été choisie : l'effectif peut varier légèrement (8 à 12 selon les absences), donc la dernière valeur réelle est plus pertinente qu'une constante. Cette asymétrie de décision (fixe pour les horaires, historique pour l'effectif) reflète la nature différente des deux données : l'horaire est une règle d'organisation, l'effectif est un fait observé.

| Niveau | Élément | Rôle |
|---|---|---|
| Python (seed) | 4 clés `shift_*` dans `__init__.py` | Horaires standards par créneau, idempotents (créés si absents). |
| Python (route) | `horaires_creneaux` + `effectif_defaut` dans `_render_form()` | Construit le dict d'horaires et lit le dernier poste de l'opérateur (création seulement). |
| JS | `majHorairesCreneau()` dans `formulaire.html` | Préremplit la 1re ligne, gère la bascule de créneau sans écraser une saisie manuelle. |

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact de F5 |
|---|---|
| OS2 — Mesurer la production réelle via collecte terrain | **Direct.** Moins de friction = plus de fiches complétées = meilleure couverture de collecte. L'adoption de l'outil conditionne l'existence même des données. |
| OS6 — Concevoir un outil de pilotage adapté | **Direct.** Le préremplissage intelligent (smart defaults) est une caractéristique attendue d'un outil conçu pour des opérateurs semi-qualifiés saisissant sur téléphone. |

---

## 4. Impact sur la validité scientifique des données

**Aucun impact négatif — et un garde-fou explicite.**

La règle absolue, héritée de F4, est maintenue : **on ne préremplit jamais une variable mesurée**. Les volumes (entrée, conforme, déclassé) et l'essence restent vides. Préremplir un volume reviendrait à suggérer une mesure, ce qui induirait un biais de confirmation et fausserait le TRS.

Les deux champs préremplis par F5 ne sont pas des mesures de performance :
- **Les horaires** sont une donnée d'organisation (quand le poste tourne), pas une mesure de production. Ils sont par ailleurs vérifiables et ajustables par l'opérateur, et le bouton « Maintenant » reste disponible.
- **L'effectif** est un fait de présence, pas un rendement. Le reprendre du dernier poste reflète la réalité organisationnelle (équipe quasi-stable) sans toucher aux volumes produits.

**Garde-fou anti-écrasement :** la fonction JS ne remplit un horaire que s'il est vide ou s'il correspond encore à un horaire standard (donc auto-rempli, jamais touché). Dès que l'opérateur saisit une heure personnalisée, elle est protégée : un changement de créneau ne l'écrasera pas. Le préremplissage est en outre **désactivé en mode édition** (`modeCreation`), pour ne jamais altérer les données réelles d'une fiche existante.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. F5 n'ajoute aucune table ni migration. Les horaires standards sont quatre lignes dans la table `Parametre` existante (`shift_matin_debut`, `shift_matin_fin`, `shift_apresmidi_debut`, `shift_apresmidi_fin`). L'effectif par défaut est obtenu par une requête en lecture sur `Equipe`, sans persistance nouvelle.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.**

- **H1** (capacité théorique < 25 m³) : non concernée — F5 ne touche ni capacité ni volumes.
- **H2** (pertes organisationnelles) : non concernée directement ; soutenue indirectement par une meilleure couverture de collecte.
- **H3** (TRS réel < 60 %) : **protégée.** F5 ne préremplit aucune variable du calcul TRS (volumes, arrêts). Les horaires préremplis servent à structurer la saisie, pas à calculer le TRS — celui-ci repose sur la durée des arrêts et les volumes, jamais sur les horaires de passage.
- **H4** (actions sans investissement majeur) : **cohérente et renforcée.** F5 est une amélioration ergonomique à coût nul, exactement le type d'action peu coûteuse que H4 valorise.

**Point d'attention — cohérence horaire/durée :** les horaires standards (Matin 06:00→14:00 = 8h) correspondent à la durée théorique de poste utilisée pour le TRS (`duree_poste = 480 min`). Cette cohérence est saine mais non contraignante : si un poste réel diffère, l'opérateur ajuste librement l'horaire, et le TRS se recalcule sur les valeurs réelles.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| 4 paramètres `shift_*` | `__init__.py` (seed idempotent) | Horaires standards par créneau, administrables en base. |
| `horaires_creneaux` dict | `saisie.py` — `_render_form()` | Map `{créneau: {debut, fin}}` lue depuis `Parametre`, passée en JSON au template. |
| `effectif_defaut` | `saisie.py` — `_render_form()` | Effectif du dernier poste de l'opérateur (création seulement), repli 10. |
| `majHorairesCreneau()` | `formulaire.html` | Préremplit la 1re ligne ; échange à la bascule de créneau ; protège les saisies manuelles ; neutre en édition. |
| `horairesCreneaux`, `modeCreation` | `formulaire.html` | Constantes JS injectées. |

---

## 8. Utilisabilité terrain et adoption

1. **Ancrage immédiat** — à l'ouverture d'une nouvelle fiche, le premier passage affiche déjà des horaires plausibles. L'opérateur part d'une base, pas d'un champ vide.
2. **Bascule intelligente** — changer le créneau met à jour les horaires automatiquement, sauf si l'opérateur a déjà personnalisé : zéro perte de saisie.
3. **Effectif réaliste** — la dernière valeur connue est plus juste qu'un 10 générique, tout en restant modifiable d'un geste.
4. **Aucune surprise** — le bouton « Maintenant » et la saisie libre restent disponibles ; le préremplissage est une aide, pas une contrainte.

Ancrage littérature : la réduction de la charge de saisie (smart defaults) est un facteur reconnu d'adoption des outils de collecte terrain (Mncwango & Mdunge, 2025 — les boucles rapides et la simplicité de saisie augmentent l'engagement des opérateurs).

---

## 9. Ce que cela change pour le mémoire

| Section du mémoire | Mise à jour requise |
|---|---|
| OS2 — Outil de collecte | Mentionner le préremplissage intelligent comme levier d'adoption et de complétude des fiches. |
| OS6 — Vue opérateur | Décrire la fiche de saisie comme conçue pour minimiser la friction (smart defaults sur horaires et effectif) sans préremplir les variables mesurées. |
| Méthodologie — fiabilité des données | Documenter la règle de conception : préremplissage des données d'organisation (horaires, effectif), jamais des données mesurées (volumes). |
| Limite à signaler | Les horaires standards (06:00→14:00 / 14:00→22:00) sont des hypothèses provisoires ; ils devront être confirmés par observation terrain et ajustés en base le cas échéant. |

---

> **Vérification réalisée :** redémarrage de l'app (seeding des 4 paramètres `shift_*` confirmé en base). Inspection du HTML servi sur `/saisie/nouveau` en session authentifiée : `horairesCreneaux` injecté correctement, `modeCreation = true`, effectif prérempli à `9` (repris du dernier poste réel de l'utilisateur, et non du 10 statique), appel `majHorairesCreneau()` câblé dans la branche création, `onchange` câblé sur le sélecteur de créneau. Logique JS validée par simulation Node sur 4 cas (remplissage à vide, bascule de créneau, respect d'une saisie manuelle, neutralité en édition) — tous conformes. Vérification navigateur impossible (Chromium non lançable dans cet environnement).
