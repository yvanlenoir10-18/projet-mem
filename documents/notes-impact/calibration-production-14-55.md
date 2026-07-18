# Note d'impact mémoire — Calibration de la production sur 14,55 m³/poste + objectif 25

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-14 (soutenance J-1) · Commit `f71b06e`
> Suite de l'alignement app ↔ mémoire (#3). Calibration de données, aucune fonctionnalité ajoutée.

---

## 1. Ce qui a été implémenté

Deux paramètres alignés sur le mémoire, fixés automatiquement par l'outil d'import :
- **`objectif_m3 = 25`** (mémoire §3.1.1.2 : objectif = 25 m³/poste, confirmé 2× par le chef) ;
- **capacité = 2,473 m³/h**, calée pour une **production réelle ≈ 14,55 m³/poste** (mémoire §3.1.1.2 : « 14,55 m³ par poste-équipe »).

La capacité lue par `calcule_trs` est mise à la **même valeur** que la constante `CAPACITE_H` de la reconstruction, garantissant leur cohérence.

## 2. Lien avec les objectifs du mémoire

- **OS1 / §3.2.1** : le trio de tête du mémoire (« production 14,55 m³/poste, TRS 64 %, capacité réaliste 49/21 ») est désormais reproduit par l'app pour la production et le TRS.
- L'objectif de 25 m³/poste, central au diagnostic (58 % d'atteinte), est le paramètre officiel de l'app.

## 3. Données et calculs mobilisés

Preuve de **neutralité TRS** : à la reconstruction, `volume_sorti = Perf × capacité × temps`. `calcule_trs` recalcule `Perf = volume_sorti / (capacité × temps) = Perf` (identité), tant que la capacité est la même des deux côtés. Donc TRS = 63,3 % **inchangé**, quel que soit le niveau de capacité. Seuls les **volumes absolus** montent (9,2 → 14,55 m³/poste). Le rendement matière (= sorti/entrée) reste **31 %** (entrée = sorti/rendement suit proportionnellement).

## 4. Hypothèses testées ou confirmées

- **Confirmé** : la calibration de capacité déplace la production sans toucher le TRS ni le rendement.
- **Hypothèse assumée** : 2,473 m³/h est une capacité *moyenne effective* calée sur la production réelle ; le mémoire cite des capacités *par essence et par mode* (49/21 m³/poste réalistes), que l'app V1 ne modélise pas finement.

## 5. Ce que ce module permet de montrer dans le mémoire

- L'app affiche la **production réelle du mémoire** (14,55 m³/poste), renforçant la cohérence entre l'outil et le texte défendu.

## 6. Limites actuelles

- **Écran « Production & Objectifs » : 70 %, pas 58 %.** Il agrège l'objectif sur **2 postes/jour** (codé en dur) alors que les données ont **3 postes/jour**, et compare le **conforme** (12,52) et non le **débité** (14,55). L'atteinte *par poste* est pourtant bien 58 % (14,55/25). Correction = ajuster `_resume_production` (objectif × nb postes réels ; base débité) — **non faite** (modif d'affichage, en attente d'accord la veille de soutenance).
- **Manque à gagner ~424 M FCFA** (app, prix locaux 180k/280k) vs **357 M** (mémoire, prix export FOB 407k/446k). Écart de **base de prix**, pré-existant, non corrigé ce soir.

## 7. Vérification de cohérence avec les notes précédentes

- **Cohérent** avec la note d'import (0,17 pt d'écart TRS conservé) et la note rendement (31 % conservé).
- **⚠️ Corrige** une valeur ancienne : l'objectif app passe de 12,5 (hypothèse « V1 provisoire » de CLAUDE.md) à **25** (mémoire). CLAUDE.md indique encore « 12,5 m³/poste » — **à mettre à jour** pour cohérence (le mémoire fait foi : 25 m³/poste).

## 8. Références bibliographiques mobilisées implicitement

- Aucune nouvelle : calibration numérique sur des mesures déjà établies dans le mémoire (Cuflink, chronométrages).

## 9. Prochaines étapes

- **Décision A′/B′** : corriger l'affichage de l'écran Production (→ 58 %) ou s'en tenir aux chiffres de fond alignés.
- Optionnel : passer les prix en FOB export pour rapprocher le manque à gagner de 357 M.
- Mettre CLAUDE.md à jour (objectif 25 m³/poste) pour lever la dernière incohérence documentaire.
