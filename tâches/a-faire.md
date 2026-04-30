# CUF Pilotage — Plan vivant des tâches

> Projet : Application Flask de pilotage Chaîne 4, Scierie CUF Ebolowa
> Mis à jour : 2026-04-30

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

## 🔄 PHASE 2 — Analyse des pertes (EN COURS)

Cadrage validé par l'utilisateur :
- Accès : chef de production + PDG uniquement
- Filtre : mois calendaire (pas 7/30/90 jours)
- Tableau de bord avec KPIs D/P/Q + drill-down sur clic
- Perte P ventilée par équipe (Matin vs Après-midi)
- Pareto des arrêts centralisé ici (retiré du dashboard Chef)

### Étapes :
- [ ] Supprimer Pareto du dashboard Chef
- [ ] Reconstruire route `/dashboard/pertes` avec filtre mensuel
- [ ] Créer template `pertes.html` (KPIs + drill-down + Pareto)
- [ ] Tester avec données réelles

---

## ⏳ PHASES SUIVANTES (backlog)

- [ ] **Phase 3** — Workflow statut : brouillon → soumis → verrouillé
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
