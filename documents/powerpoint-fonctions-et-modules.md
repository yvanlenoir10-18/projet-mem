# PowerPoint — Fonctions & modules de l'application CUF Pilotage

> Contenu prêt à coller dans PowerPoint. Chaque bloc « ── DIAPO n ── » = une diapositive.
> Style diapo : titres courts, puces de 4 à 7 mots, pas de phrases longues. Les « Notes » sont pour l'oral (à ne pas mettre sur la diapo).

---

## ── DIAPO 1 — Titre ──

**Application CUF Pilotage**
Outil numérique de pilotage de la production — chaîne 4, scierie CUF Ebolowa

- Support applicatif du mémoire M2
- BWAME EBENGUE CARLOS YVAN

*Notes : « Je vais vous présenter les fonctions et les modules de l'application développée pour piloter la chaîne 4. »*

---

## ── DIAPO 2 — Le besoin ──

**Pourquoi cette application ?**

- Aucun système de mesure de la performance en place
- Objectif affiché : 25 m³/poste · réel ≈ 14,5 m³ (58 %)
- Arrêts et pertes non tracés, non chiffrés
- Décisions sans données fiables

*Notes : l'app répond à H3 — absence de système de mesure.*

---

## ── DIAPO 3 — Ce qu'est l'application ──

**Une application, cinq profils**

- Application **desktop**, **100 % hors ligne**
- Stockage **local** (base de données SQLite)
- Interface **en français**, large et tactile
- 5 profils : Opérateur · Chef scierie · Chef de production · Directeur · Administrateur

*Notes : hors ligne car le terrain n'a pas de connexion fiable.*

---

## ── DIAPO 4 — Architecture technique ──

**Comment c'est construit**

- Langage **Python**, framework web **Flask**
- Base de données **SQLite** (fichier local, sans serveur)
- Contrôle d'accès par rôle (**RBAC**)
- Moteur de calcul **TRS** intégré (D × P × Q)
- Rapports **Excel** générés automatiquement

*Notes : RBAC = chaque profil ne voit que ses écrans. TRS = Taux de Rendement Synthétique.*

---

## ── DIAPO 5 — Vue d'ensemble des modules ──

**Les 7 modules de l'application**

1. **Saisie** — collecte terrain (opérateur)
2. **Cockpit Chef** — pilotage et décision
3. **Analyse** — TRS, Pareto, machines, qualité, pertes
4. **Résolution de problème** — Ishikawa, 5 Pourquoi, actions
5. **Recommandations** — contre-mesures chiffrées
6. **Direction (PDG)** — décision financière
7. **Administration** — comptes, prix, paramètres

*Notes : présenter ce schéma comme la carte de la suite.*

---

## ── DIAPO 6 — Fonctions transverses ──

**Fonctions communes à toute l'application**

- Connexion sécurisée + redirection selon le rôle
- Cycle de vie des fiches : brouillon → à vérifier → à corriger → validée → verrouillée
- Contrôles de cohérence automatiques (anomalies bloquantes / avertissements)
- Paramétrage : prix, seuils, objectifs (sans toucher au code)
- Export Excel du rapport mensuel

*Notes : les contrôles garantissent la fiabilité de la donnée.*

---

## ── DIAPO 7 — Module 1 · Saisie (Opérateur) ──

**Collecter la donnée au poste**

- Saisie des essences, volumes, arrêts par poste
- Contrôle **anti-chevauchement** de la bicoupe
- Fiche papier imprimable (relevé terrain)
- Correction des fiches renvoyées par le chef
- Historique personnel des fiches

*Notes : une seule essence à la fois sur la bicoupe = cohérence physique.*

---

## ── DIAPO 8 — Module 2 · Cockpit Chef ──

**Piloter en 10 secondes**

- Verdict global : sous contrôle ou non (vert/orange/rouge)
- TRS de la période + tendance
- Manque à gagner en FCFA
- Priorités décisionnelles + signaux (machine critique, équipe qui décroche)
- Contrôle et validation des fiches (tous statuts)

*Notes : le cockpit répond à « où est le problème, combien il coûte, quoi faire ». *

---

## ── DIAPO 9 — Module 3 · Analyse ──

**Comprendre les pertes**

- **TRS = Disponibilité × Performance × Qualité**
- **Pareto** des arrêts (causes les plus coûteuses)
- Diagnostic **machines** (récurrences, disponibilité)
- **Qualité** matière : rendement et déclassement par essence
- **Pertes financières** D/P/Q en FCFA (drill-down machine/essence)

*Notes : Pareto = loi 80/20 ; on agit d'abord sur les premières causes.*

---

## ── DIAPO 10 — Module 4 · Résolution de problème ──

**De la cause à l'action**

- Diagramme **Ishikawa 6M** (6 familles de causes)
- Méthode des **5 Pourquoi** (cause racine)
- Rapport **A3** (résolution sur une page)
- Création d'**actions correctives** suivies
- Bilan avant/après en FCFA évités

*Notes : c'est la boucle Lean, argument OS et H2 du mémoire.*

---

## ── DIAPO 11 — Module 5 · Recommandations ──

**Des contre-mesures, pas des conseils**

- Générées sur les **données réelles**
- Format : signal → données → diagnostic → prescription
- **Niveau de confiance** affiché (raisonnement traçable)
- Contre-mesures métier par catégorie d'arrêt
- **100 % hors ligne** — aucune IA externe

*Notes : l'app affiche le raisonnement qui mène à la reco, pas une vérité magique.*

---

## ── DIAPO 12 — Module 6 · Direction (PDG) ──

**Décider avec les chiffres financiers**

- Vue exécutive : jour / semaine / mois / année
- **Décision financière** : pertes par 3 leviers (Disponibilité, Performance, Qualité)
- Valeur produite valorisée + manque à gagner
- Accès à l'analyse détaillée des pertes
- Recommandations prioritaires Direction

*Notes : le levier le plus coûteux = priorité d'investissement.*

---

## ── DIAPO 13 — Module 7 · Administration ──

**Paramétrer et gérer**

- Gestion des comptes utilisateurs et des rôles
- Prix FOB export par essence (modifiables)
- Seuils et objectifs configurables
- Réinitialisation de mots de passe

*Notes : outil paramétrable = il s'adapte au marché sans reprogrammer.*

---

## ── DIAPO 14 — Lien avec le mémoire ──

**L'app matérialise la démarche**

- Fil conducteur **DMAIC** : Définir, Mesurer, Analyser, Améliorer, Contrôler
- Mesure (OS1) : capacité théorique → production réelle → écart + TRS
- Analyse des causes (Ishikawa) → actions → contrôle de l'effet
- Chiffrage économique de l'écart de performance

*Notes : chaque module correspond à une étape de la démarche du mémoire.*

---

## ── DIAPO 15 — Conclusion ──

**Ce que l'application apporte**

- Une donnée fiable, tracée, du terrain à la direction
- Un pilotage par la performance et par les FCFA
- Une boucle d'amélioration continue outillée
- Un outil réel, hors ligne, adapté à la chaîne 4

*Notes : conclure sur le passage de « pas de mesure » à « pilotage outillé ».*

---

## Résumé — tableau des fonctions par module (annexe / diapo de secours)

| Module | Profil principal | Fonctions clés |
|---|---|---|
| Saisie | Opérateur | Fiches, essences, arrêts, anti-chevauchement, fiche papier |
| Cockpit Chef | Chef / Chef prod | Verdict, TRS, manque à gagner, priorités, validation fiches |
| Analyse | Chef / Chef prod | TRS D/P/Q, Pareto, machines, qualité, pertes FCFA |
| Résolution | Chef | Ishikawa 6M, 5 Pourquoi, A3, actions, bilan |
| Recommandations | Chef / PDG | Contre-mesures chiffrées, niveau de confiance |
| Direction | PDG | Vue exécutive, décision financière D/P/Q |
| Administration | Admin | Comptes, prix, seuils, objectifs |
