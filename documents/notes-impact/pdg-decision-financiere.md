# Note d'impact — Cockpit de décision financière du PDG

> Branche `claude/install-claude-excel-6MGzv` · commit `c2ef53f` · 2026-07-18
> Type : fonctionnalité (affichage + accès) · aucune table, aucun modèle, aucune migration

## 1. Problème traité

Le tableau de bord Direction (`/dashboard/pdg`) affichait la perte totale et le manque à gagner, mais **ne disait pas où agir** : le dirigeant voyait un chiffre passif sans décomposition actionnable. Pire, le bouton « Causes D/P/Q → » de son propre dashboard renvoyait vers `/pertes`, page **interdite au rôle PDG** (`roles_required('chef', 'prod', 'admin')`) — donc une erreur d'accès.

## 2. Cause racine

Deux points distincts : (a) la route `/pertes`, seule page portant la décomposition financière détaillée par machine et par essence, n'incluait pas `'pdg'` dans ses rôles autorisés ; (b) le dashboard PDG ne calculait pas la décomposition des pertes par levier (D/P/Q), seulement leur somme.

## 3. Correctif / fonctionnalité apportée

- **Accès** : `/pertes` ouvert au rôle `pdg`. La page de décision financière détaillée (D/P/Q par machine et par essence, prix de valorisation, drill-down des arrêts) devient consultable par la Direction.
- **Dashboard PDG** : nouveau bloc « Décision financière — où agit l'argent » qui décompose la perte chiffrée en **trois leviers** :
  - **Disponibilité** — FCFA perdus en arrêts machine ;
  - **Performance** — FCFA perdus en cadence (ralentissements) ;
  - **Qualité** — FCFA perdus en déclassé + déchets.
  Chaque levier affiche son montant et sa part en % du total. Le bloc rappelle aussi la **valeur produite valorisée** (conforme + déclassé aux prix courants) et le **manque à gagner estimé**, et renvoie vers l'analyse détaillée.

## 4. Justification métier

Un dirigeant n'arbitre pas sur un total de pertes : il arbitre sur **le levier le plus coûteux**, car c'est là qu'un investissement rapporte le plus. Décomposer la perte en Disponibilité / Performance / Qualité relie chaque franc perdu à une décision (maintenance, cadence, ou qualité matière). Cela sert l'objectif OS1 du mémoire (capacité théorique → production réelle → écart chiffré) en donnant à la Direction la lecture financière de cet écart.

## 5. Périmètre et fichiers touchés

| Fichier | Nature |
|---|---|
| `cuf-pilotage/app/routes/dashboard.py` | `/pertes` : rôle `pdg` ajouté · `vue_pdg()` : calcul `perte_dpq` (D/P/Q) + `valeur_produite`, injectés au template |
| `cuf-pilotage/app/templates/pdg/dashboard.html` | Nouveau bloc « Décision financière » (3 leviers chiffrés + valeur produite + manque à gagner + lien pertes) |

Réutilise `calcule_pertes_equipe` (déjà importé) ; aucune nouvelle dépendance.

## 6. Vérification

- `ast.parse(dashboard.py)` → **valide** (avant et après application des correctifs `setup_demo`).
- Serveur lancé sur données de démonstration, connexion `pdg@cuf.cm` :
  - `/dashboard/pdg` → **200**, bloc « Décision financière » présent avec les 3 leviers ;
  - `/dashboard/pertes` (auparavant interdit) → **200** ;
  - montants rendus non nuls et réalistes (dizaines à centaines de millions FCFA, cohérents avec les autres indicateurs financiers de l'app).

## 7. Cohérence avec les hypothèses et le cadre du mémoire

Aucune hypothèse (H1–H4) n'est **contredite**. La décomposition D/P/Q en FCFA renforce au contraire OS1 (chiffrage de l'écart de performance) et l'argumentaire économique du mémoire. Elle ne modifie aucun calcul existant (TRS, manque à gagner, Pareto) : elle expose des montants déjà calculés par ailleurs (`calcule_pertes_equipe`), garantissant la cohérence avec la page Pertes du chef. La cohérence app ↔ mémoire est préservée.

## 8. Limites connues

- La décomposition additionne les pertes D/P/Q par poste ; comme sur la page Pertes du chef, il s'agit d'estimations ancrées sur les prix de valorisation (snapshots figés ou paramètres vivants selon la fiche). Les montants sont donc des ordres de grandeur défendables, pas une comptabilité analytique certifiée — à présenter comme tels.
- Le bloc suppose des prix renseignés ; si un prix essence est à 0, la part correspondante est sous-estimée (l'alerte « Prix manquants » existante le signale déjà).

## 9. Prochaine étape

Aucune action bloquante. Le profil PDG dispose désormais d'un cockpit de décision financière complet (synthèse + accès au détail). Amélioration future possible : ajouter au bloc le **potentiel de récupération** chiffré issu des recommandations (gain attendu FCFA) pour matérialiser le retour sur action, une fois la boucle avant/après consolidée.
