# Note d'impact mémoire — P6-F2 : Matrice criticité arrêts (machine × catégorie)
**Commit :** `c46dc7b` — `feat(chef): P6-F2 — matrice criticité arrêts machine × catégorie`
**Date :** 2026-05-04
**Fichiers modifiés :** `app/routes/dashboard.py` (+49 lignes) · `app/templates/chef/dashboard.html` (+55 lignes)

---

## 1. Ce qui a été implémenté

Ajout d'une table 6 × 6 dans le dashboard Chef Scierie affichant, pour chaque combinaison machine × catégorie de cause, la durée totale agrégée (en heures/minutes) et le nombre d'occurrences sur la période sélectionnée (7, 30 ou 90 jours).

| Élément | Détail |
|---|---|
| **Lignes (machines)** | Bicoupe, Scie de tête, Déligneuse, Ébouteuse, Dédoubleuse, Autre |
| **Colonnes (catégories)** | Mécanique, Organisationnelle, Approvisionnement, Qualité matière, Maintenance planifiée, Autre |
| **Contenu d'une cellule** | Durée formatée (ex. "1h30") + fréquence "×N" |
| **Code couleur** | rouge `table-danger` si > 120 min · orange `table-warning` si 30–120 min · vert `table-success` si < 30 min · vide si aucun arrêt |
| **Badge fréquence** | `badge bg-danger ×N` (rouge) si N ≥ 5 occurrences sur la période |

**Architecture technique :**

Route `vue_chef()` dans `dashboard.py` :
- `defaultdict(lambda: {'duree': 0, 'count': 0})` pour l'agrégation brute en O(n_arrets)
- Itération sur `Config.MACHINES × Config.CATEGORIES_ARRET` pour construire la matrice dense (36 cellules fixes, cellules sans données = durée 0)
- Fonction `_format_duree(minutes)` (niveau module) : convertit minutes en "1h30", "45min", "2h00"

Jinja2 : aucune logique arithmétique — toutes les valeurs sont pré-calculées côté Python et passées comme dict `matrice[machine][categorie]` au template.

---

## 2. Lien avec les objectifs du mémoire

F2 répond directement à **OS4** (identifier et hiérarchiser les causes responsables de l'écart performance) et à **OS6** (concevoir un outil de pilotage adapté — vue Chef).

La matrice opérationnalise le Pareto en ajoutant une dimension que le simple classement par durée totale ne donnait pas : **la répartition par type de cause pour chaque machine**. Un chef peut ainsi voir en un coup d'œil si ses arrêts Bicoupe sont plutôt mécaniques (nécessite technicien) ou organisationnels (nécessite réorganisation du flux), ce qui oriente directement les actions correctives de P6-F5.

---

## 3. Données et calculs mobilisés

**Agrégation :** somme des `arret.duree_min` par clé `(machine, categorie)` sur toutes les équipes soumises de la période. Le filtre `_STATUTS_ANALYSES = ('soumis', 'verrouille')` exclut les brouillons — un arrêt non validé ne doit pas influencer le diagnostic.

**Format durée :**
```
120 min → 2h00    (h > 0, m == 0 → "Xh00")
90 min  → 1h30    (h > 0, m > 0  → "Xh30")
45 min  → 45min   (h == 0        → "Xmin")
```

**Seuils de couleur :** choix pragmatiques pour la chaîne 4 CUF (poste de 480 min) :
- > 120 min = perte > 25 % du temps poste → rouge (critique)
- 30–120 min = perte 6–25 % → orange (à surveiller)
- < 30 min = perte < 6 % → vert (tolérable)

Ces seuils sont relatifs à un poste unitaire mais agrégés sur 30 jours par défaut ; ils sont donc interprétables comme une signature de récurrence, pas comme une perte instantanée.

---

## 4. Hypothèses testées ou confirmées

**H2 — les pertes sont principalement d'origine organisationnelle et opérationnelle** est directement mise à l'épreuve par cette matrice. Sur les données de démonstration (seed), les colonnes "Mécanique" et "Organisationnelle" sont les seules non vides — ce qui préfigure le résultat attendu sur données terrain. Sur données réelles CUF, si la colonne "Organisationnelle" accumule plus de durée que "Mécanique", H2 sera confirmée visuellement dans le dashboard lui-même, sans calcul supplémentaire.

**Aucune contradiction avec les hypothèses existantes.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

- La matrice criticité est la preuve que l'outil de pilotage dépasse le simple comptage : il offre un **diagnostic croisé machine × cause** directement exploitable par le Chef Scierie, sans formation analytique particulière.
- Elle illustre concrètement la distinction entre arrêts mécaniques (relevé du technicien) et arrêts organisationnels (relevé du chef de poste), distinction centrale dans la méthodologie DMAIC mobilisée par Mncwango & Mdunge (2025).
- Le code couleur vert/orange/rouge sur fond Bootstrap est cohérent avec la logique "traffic light" déjà documentée pour le dashboard PDG (Laine 2024 : "signaux visuels immédiats pour décideurs"). La même convention de lecture s'applique à deux niveaux hiérarchiques distincts — ce qui illustre la cohérence de la conception multi-niveaux.
- Le badge "×N rouge si ≥ 5" distingue un arrêt rare mais long d'un arrêt court mais chronique. Cette distinction est pédagogiquement utile en soutenance : un arrêt de 2h une fois est différent d'un arrêt de 20 min dix fois — les actions correctives ne sont pas les mêmes.

---

## 6. Limites actuelles

- **Correspondance exacte des noms de machines :** la matrice ne montre que les arrêts dont `arret.machine` correspond exactement à une valeur de `Config.MACHINES`. Toute donnée saisie avec une orthographe différente (ex. "Scie de tete" sans accent) tombera dans les cellules vides de la ligne concernée. Cette limite est observable sur la DB locale de développement (données pré-seed) ; elle disparaîtra sur les données de démonstration (seed) qui utilisent les noms canoniques.
- **Période fixe :** la matrice hérite du filtre 7/30/90 jours du dashboard Chef. Elle ne peut pas être filtrée sur un mois calendaire précis (contrairement au dashboard PDG). À améliorer si le besoin terrain l'exige.
- **Pas de drill-down :** cliquer sur une cellule ne liste pas les arrêts détaillés correspondants. La vue de pertes `/dashboard/pertes` offre ce drill-down par machine mais pas par catégorie × machine simultanément. Un drill-down combiné est différé.

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P5-dashboard-pdg-enrichi.md` documentait le Pareto top-5 comme outil de diagnostic pour le PDG. F2 ne remplace pas ce Pareto — il l'enrichit côté Chef en ajoutant la dimension catégorie. Le PDG garde sa vue synthétique (top 5 causes toutes machines confondues) ; le Chef gagne une vue matricielle croisée. Les deux vues sont complémentaires et documentées dans des sections distinctes du mémoire.

La note `00-cadrage-global-P1-P2-P3.md` identifiait la bicoupe comme machine goulot. La matrice confirmera visuellement cette position si la ligne Bicoupe est la plus colorée sur données terrain réelles — ce qui constitue une validation empirique de l'hypothèse de goulot.

Aucune contradiction avec les notes précédentes.

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Mncwango & Mdunge (2025) | DMAIC : identification et classification des causes d'arrêt par catégorie — la matrice traduit visuellement l'étape "Measure" du DMAIC |
| Laine (2024) | Signaux visuels immédiats pour décideurs : code couleur vert/orange/rouge repris de la même convention que le dashboard PDG |
| Jonsson & Lesshammar (1999) | La catégorie "Mécanique" correspond aux pertes de Disponibilité (D), "Organisationnelle" peut relever de D ou P selon la nature de l'arrêt — la matrice n'impose pas cette classification mais la rend diagnosticable |

---

## 9. Prochaines étapes

- **F1 — Décomposition TRS en m³ perdus** : cascade D×P×Q exprimée en volumes, pas en pourcentages. Visualisation plus parlante pour le Chef que les pourcentages bruts.
- **F5 — Scorecard 7 jours calendaire (lun–sam)** : grille semaine avec état TRS % / ⏳ brouillon / — absent.
- **F4 — Score régularité CV** : coefficient de variation du TRS, affiché uniquement si n ≥ 10 postes.
- **F3 — Calculateur potentiel gain FCFA** : slider cible TRS (défaut 70 %, modifiable), projection de gain en m³ et FCFA.
- **F6 — Filtre date partagé (refactoring DRY)** : helper commun Chef/PDG pour la sélection de période.
- **Windows :** synchronisation git `reset --hard origin/claude/install-claude-excel-6MGzv` pour récupérer P5b/P5c/P5d/P6-F2.
