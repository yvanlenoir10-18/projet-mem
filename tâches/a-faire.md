# CUF Pilotage — Plan vivant des tâches

> Projet : Application Flask de pilotage Chaîne 4, Scierie CUF Ebolowa
> Mis à jour : 2026-04-30 (P3 complété)

---

## ✅ PHASE 1 — Saisie des équipes (COMPLÉTÉ)

- [x] Modèle Equipe + Production + Arret
- [x] Formulaire de saisie multi-essence
- [x] Calcul TRS automatique (Disponibilité × Performance × Qualité)
- [x] Historique des équipes
- [x] Détail d'une équipe (KPIs + arrêts + pertes)
- [x] Export Excel (3 feuilles : Résumé | Équipes | Arrêts)
- [x] **P1 Amendment** — Refonte modèle matière :
  - [x] volume_conforme (planches conformes, prix plein)
  - [x] volume_declass (bois déclassé, vente locale ×0.30)
  - [x] volume_dechets (calculé = entree − conforme − declass)
  - [x] Perte Q décomposée : perte_q_declass + perte_q_dechets
  - [x] Formulaire avec calcul live JS des déchets

---

## ✅ PHASE 2 — Analyse des pertes (COMPLÉTÉ)

- [x] Supprimer Pareto du dashboard Chef
- [x] Route `/dashboard/pertes` avec filtre mensuel calendaire
- [x] Template `pertes.html` — KPIs D/P/Q + drill-down par machine + Pareto
- [x] Perte P ventilée par shift (Matin / Après-midi)

---

## ✅ PHASE 3 — Workflow brouillon → soumis → verrouillé (COMPLÉTÉ)

Commit : `5baf68b`

- [x] Statut par défaut `brouillon` + champs `soumis_le` / `modifie_par` / `modifie_le`
- [x] `prix_snapshot` figé à la soumission (premier freeze uniquement)
- [x] Helpers `_peut_modifier()` / `_peut_soumettre()` — contrôle d'accès centralisé
- [x] Routes soumettre / modifier / verrouiller / déverrouiller avec abort(403)
- [x] Dashboard + export Excel filtrés sur `_STATUTS_ANALYSES` (jamais les brouillons)
- [x] `formulaire.html` — mode dual création/modification avec pré-remplissage JS
- [x] `historique.html` — badge brouillon + boutons Soumettre/Supprimer contextuels
- [x] `detail.html` — badge statut + soumis_le + trace modifie_par + boutons d'action

---

## ⏳ PHASES SUIVANTES (backlog)

- [ ] **Phase 4** — Export Excel enrichi
- [ ] **Phase 5** — Dashboard PDG (vue exécutive)
- [ ] **Phase 6** — Dashboard Chef (vue opérationnelle)
- [ ] **Phase 7** — Validation & alertes

---

## 🔧 BUGS RÉSOLUS

| Bug | Cause | Fix |
|-----|-------|-----|
| Internal Server Error | Ancien cuf.db avec schema incompatible (arret.poste_id) | Supprimer cuf.db avant restart |
| Flask reload infini Windows | Watchdog détecte les fichiers Windows Store Python | `use_reloader=False` dans run.py |
| 500 générique sans message | `except (ValueError, KeyError)` trop étroit | `except Exception as e` avec flash |
