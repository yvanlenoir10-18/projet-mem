# Note d'impact mémoire — Alignement de l'app sur le mémoire final (4 profils + rendement 31 %)

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-14 (soutenance J-1) · Commit `70f94ea`
> Déclenché par la lecture du mémoire final (`test_2.docx`). Aucune grosse fonctionnalité ajoutée.

---

## 1. Ce qui a été implémenté

Deux corrections d'alignement app ↔ mémoire, choisies par l'utilisateur :

- **#1 — Quatre profils.** Le mémoire (§2.5 et §3.1.4.2) affirme deux fois « **quatre profils** ». L'app en avait cinq (doublon Chef Scierie / Chef de Production). Le compte `chef@cuf.cm` est retiré (base + seed `__init__.py`). Restent : Opérateur, **Chef de Production** (`prod`), Direction, Administrateur. Le **rôle `chef` reste dans le code** ; seul le compte de démonstration disparaît.
- **#2 — Rendement matière 31 %.** L'app affichait ~62 % ; le mémoire (Tableau 12) mesure **30,6 % ≈ 31 %**. Hypothèses d'import alignées sur les valeurs réelles par essence (Ayous 33,8 · Movingui 30,9 · Iroko 30,4 · **Bilinga 23,3**) ; « Autre » calibré à 0,265 pour un global de **31,0 %**.

## 2. Lien avec les objectifs du mémoire

- **OS1** : l'écran Qualité (figure 11 du mémoire) affiche désormais le rendement matière réel (31 %, Bilinga 23,3 %), cohérent avec la discussion §3.2 (« la chaîne 4 en bas des références régionales »).
- **Livrable §3.1.4.2** : l'app correspond maintenant à sa description écrite — quatre profils, quatre écrans-clés (cockpit, Pareto, qualité, direction).

## 3. Données et calculs mobilisés

- #1 : suppression d'un compte utilisateur (aucun impact données — `chef@cuf.cm` ne possédait aucune fiche). RBAC inchangé.
- #2 : les rendements ne touchent **que** `volume_entree` (= `volume_sorti / rendement`). Le TRS (Disponibilité × Performance × Qualité) **ne dépend pas** de `volume_entree` : il reste à 63,3 % (écart 0,17 pt vs fichier). Seuls le rendement matière et les déchets changent.

## 4. Hypothèses testées ou confirmées

- **Confirmé** : per-essence conforme au mémoire pour les 4 essences configurées.
- **Hypothèse assumée** : « Autre » (essences hors des 4 : Azobé, Fraké, Dabéma…) calibré à 0,265 pour caler le global sur 31 % — bucket synthétique, non une essence réelle unique.

## 5. Ce que ce module permet de montrer dans le mémoire

- Une app qui **dit exactement ce que le mémoire dit** : 4 profils, rendement 31 %, Bilinga essence dure à bas rendement. Réduit le risque de contradiction visible en soutenance.

## 6. Limites actuelles

- Les modules **Prescriptions / Décisions de pilotage / Résolution (Ishikawa)** existent dans l'app mais ne figurent dans **aucune** figure du mémoire. Choix retenu : les **garder** (défendables comme couche « plan d'actions correctives », Tableau 15), sans les mettre en avant dans la démo.
- Les volumes m³ restent **reconstruits** (le fichier terrain n'a pas de m³) ; le mémoire cite 14,55 m³/poste (Cuflink, images non transcriptibles) — l'app ne peut pas reproduire cette valeur exacte poste par poste.

## 7. Vérification de cohérence avec les notes précédentes

- **Supersède une décision verrouillée** : la coexistence chef + prod (2026-06-09) est **remplacée pour la démo** par « quatre profils » (mémoire). Le rôle `chef` n'est pas supprimé du code — la décision « ne jamais supprimer le rôle chef » reste respectée.
- **⚠️ Contradiction ouverte NON corrigée (#3)** : le mémoire fixe l'**objectif à 25 m³/poste** (production 14,55 = 58 %). L'app reste à `objectif_m3 = 12,5`/poste. **L'écran Production & Objectifs contredit donc encore le mémoire.** Correction en attente de décision (cascade sur l'atteinte). À traiter avant la démo si le jury regarde l'écran Production.
- **#4 en attente** : le Pareto de l'app est en minutes, le mémoire (fig 10) le dit « exprimé en FCFA ».

## 8. Références bibliographiques mobilisées implicitement

- Rendements de référence filière (Karsenty 2021 : 35 % Afrique centrale ; Ngobi 2023 : 32 % Ouganda ; Ofoegbu 2014 : 46,9 % Nigeria) — cadre de lecture du 31 %.

## 9. Prochaines étapes

- **Décider #3 (objectif 25 m³/poste)** — la contradiction la plus visible restante sur l'écran Production.
- Optionnel **#4** : exprimer le Pareto en FCFA pour coller à la figure 10.
- Passe d'ajustement des autres profils (Direction, Admin) si le temps le permet avant la soutenance.
