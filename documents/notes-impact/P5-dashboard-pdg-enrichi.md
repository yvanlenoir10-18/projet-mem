# Note d'impact mémoire — P5 : Tableau de bord PDG enrichi
**Commit :** `2332173` — `feat(dashboard): P5 — tableau de bord PDG enrichi`
**Date :** 2026-05-03
**Fichiers modifiés :** `cuf-pilotage/app/routes/dashboard.py` (+88 lignes) · `app/templates/pdg/dashboard.html` (+286 lignes, remplacement complet)

---

## 1. Ce qui a été implémenté

Remplacement complet du dashboard PDG P1 (3 KPIs, top 3 Pareto, tendance 6 mois) par un tableau de bord enrichi à 7 composantes :

| Composante | Contenu clé |
|---|---|
| **Bannière prix manquants** | Alerte rouge dismissible si au moins une essence sans prix configuré — évite qu'un PDG lise des pertes FCFA sous-estimées sans le savoir |
| **Alerte brouillons** | Bandeau jaune avec compte des postes non soumis ; lien d'action vers l'historique uniquement pour les rôles chef/admin (PDG voit l'alerte mais pas l'action) |
| **Filtre date** | Sélecteur mois (liste déroulante) **ou** période libre personnalisée (date_debut/date_fin) avec badge "Période personnalisée" et bouton "Revenir au mois" |
| **4 KPI cards** | TRS + delta vs période précédente · Production m³ + barre de progression vs objectif · Pertes FCFA · Rendement matière global coloré |
| **Rendement par essence** | Mini-tableau Ayous/Azobé/Iroko/Movingui avec barres de progression colorées (≥60%=vert, ≥40%=orange, <40%=rouge) et benchmark Afrique centrale rappelé |
| **TRS 12 mois + benchmark** | Graphique barres 12 derniers mois (couleurs auto vert/orange/rouge) + ligne en pointillé rouge fixe à 60% (Jonsson & Lesshammar, 1999) |
| **Pareto top 5 enrichi** | Graphique horizontal coloré par catégorie + tableau détail avec badge catégorie, durée, nb incidents, %, % cumulé ; lignes en gras si % cumulé ≤ 80% |

La signature de la route `/dashboard/pdg` est rétrocompatible — les paramètres `mois`/`annee` existants continuent de fonctionner. Le filtre période libre ajoute `date_debut`/`date_fin` sans casser les bookmarks existants.

---

## 2. Lien avec les objectifs du mémoire

P5 répond directement à **l'Objectif Spécifique 6** : *"Concevoir un outil de pilotage adapté aux besoins des différents responsables de CUF."*

Le dashboard PDG P5 est précisément la vue exécutive décrite dans l'OS6 : un responsable sans formation forestière doit pouvoir lire l'état de la chaîne 4 en moins de 30 secondes. Les 4 KPI cards avec code couleur vert/orange/rouge, la ligne benchmark 60% et les badges catégorie du Pareto répondent à cette contrainte de lisibilité immédiate.

La différenciation role-aware de l'alerte brouillons (PDG voit l'alerte, Chef voit le lien d'action) illustre la conception multi-niveaux de l'outil, cohérente avec Jaouane (2022) qui distingue explicitement les niveaux stratégique, tactique et opérationnel dans un tableau de bord industriel.

Le filtre période libre répond à une contrainte terrain identifiée lors de la conception : les postes CUF ne suivent pas nécessairement le découpage calendaire mensuel (arrêt usine, maintenance longue). Un chef de production doit pouvoir analyser la semaine du 7 au 14 janvier sans être contraint par le mois.

---

## 3. Données et calculs mobilisés

**Delta TRS :** calculé comme `trs_moyen_période_courante − trs_moyen_période_précédente`, où la période précédente a exactement la même durée en jours. Sur un filtre mensuel standard (31 jours), la période précédente couvre les 31 jours avant le 1er du mois — ce qui correspond au mois précédent. Sur une période libre de 21 jours, la comparaison porte sur les 21 jours qui précèdent immédiatement. Le delta est `None` si aucune équipe n'est présente dans la période précédente (base insuffisante).

**Rendement matière global :** `Σ(volume_sorti) / Σ(volume_entree) × 100` sur toutes les équipes et toutes les essences de la période. Cohérent avec `Production.rendement_matiere` (propriété du modèle) et avec le calcul de la feuille Essence de P4. Aucune duplication de logique.

**Rendement par essence :** même formule appliquée par sous-groupe après agrégation `defaultdict`. Les seuils de couleur (60% / 40%) ont été choisis en référence au benchmark Karsenty (2021) : 35% pour les scieries d'Afrique centrale. Le seuil vert à 60% correspond au benchmark international des scieries optimisées.

**Pareto :** réutilise `pareto_arrets()` de `trs.py` (déjà utilisé dans P4 et Chef Dashboard). Les champs `categorie`, `count`, `pct`, `pct_cumule` sont tous présents dans le dict retourné.

---

## 4. Hypothèses testées ou confirmées

**H3 partiellement visible :** avec les données de test (TRS = 66.4%), la ligne benchmark 60% est dépassée et la barre s'affiche en orange. Le graphique 12 mois montre clairement que les 11 mois sans données (barres à 0%) sont en rouge — ce qui illustre l'état "avant système de mesure". H3 ne peut être formellement validée ou invalidée qu'avec les données terrain réelles.

**H2 visible dans le Pareto :** sur les données de test, la cause "Pause non planifiee" (catégorie Organisationnelle, 40%) est en deuxième position. Si ce pattern se confirme en données terrain, H2 (pertes majoritairement organisationnelles) sera visuellement validée directement depuis le dashboard PDG, sans analyse supplémentaire.

**H4 visible indirectement :** la carte "Pertes financières" et le delta TRS permettront de quantifier l'impact des actions correctives mois par mois — ce qui est exactement le mécanisme de validation de H4.

**Aucune contradiction avec les hypothèses existantes.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

- L'outil de pilotage dispose désormais d'une vue exécutive opérationnelle. Le PDG de CUF peut lire en un coup d'œil : TRS du mois, évolution vs mois précédent, production vs objectif, pertes FCFA, et les deux ou trois causes principales à corriger.
- La ligne benchmark 60% dans le graphique TRS est une référence directe à Jonsson & Lesshammar (1999) — la même référence bibliographique fondatrice que celle mobilisée dans P4. Cela crée une cohérence visuelle entre le rapport Excel et le dashboard web.
- Le rendement matière par essence (seuils 60% / 40%) crée un lien direct avec Karsenty (2021) et Danwé et al. (2012), permettant à l'étudiant de comparer les valeurs terrain futures avec les benchmarks bibliographiques directement depuis l'interface.
- La différenciation role-aware (PDG / Chef / Admin) est une décision de conception documentée qui peut être présentée dans la section méthodologique comme exemple de design centré sur les besoins des utilisateurs finaux (OS6).

---

## 6. Limites actuelles

- **Graphique Pareto sans export direct :** l'option H (export Pareto en Excel) a été différée à P6/P7. Le lien vers `/dashboard/pertes` offre un drill-down textuel suffisant pour l'usage courant.
- **Delta TRS nul si pas de données période précédente :** quand le système démarre (premiers mois d'utilisation), la période précédente est vide → delta non affiché. C'est un comportement assumé (ne pas afficher un chiffre non significatif plutôt que d'afficher 0 ou N/A).
- **Filtre période libre non transmis à l'export Excel :** l'export reste mensuel. Si l'utilisateur applique une période libre du 7 au 14 janvier, le bouton "Exporter Excel" génère quand même le rapport du mois entier. Cette limite est acceptable pour P5 — l'export période libre serait P7 ou au-delà.
- **CSS impression :** différé à P6 selon décision validée en session de conception.

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P4-export-excel-enrichi.md` mentionnait que "P5 Dashboard PDG alimente déjà tous les indicateurs de P5". P5 confirme cette architecture : aucune nouvelle logique métier n'a été créée. Tous les calculs (TRS, pertes, rendement, Pareto) proviennent de `trs.py` ou de propriétés du modèle. P5 est purement une couche de présentation.

La note `00-cadrage-global-P1-P2-P3.md` identifiait le tableau de bord PDG comme livrable de l'OS6. P5 complète ce livrable avec la vue exécutive multi-indicateurs.

La décision de différenciation role-aware (PDG vs Chef) est cohérente avec la contrainte terrain décrite dans le cadrage : le PDG de CUF n'a pas de formation forestière et ne doit pas être exposé aux actions opérationnelles (soumettre un poste, corriger une saisie). La séparation PDG/Chef au niveau des alertes respecte ce principe.

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien avec P5 |
|---|---|
| Jonsson & Lesshammar (1999) | Ligne benchmark 60% dans le graphique TRS — seuil international de performance acceptable |
| Jaouane (2022) | Architecture multi-niveaux (PDG/Chef/Opérateur) et différenciation role-aware des alertes |
| Karsenty (2021) | Seuils de couleur rendement matière : 35% Afrique centrale → plancher, 60% → objectif |
| Danwé, Bindzi & Meva'a (2012) | Base de comparaison rendement scieries camerounaises (30-36%) affichée dans la mini-légende |
| Mncwango & Mdunge (2025) | Pareto des arrêts coloré par catégorie comme outil DMAIC de priorisation visible depuis la vue exécutive |

---

## 9. Prochaines étapes

- **Données terrain :** le dashboard P5 est prêt pour recevoir les premières saisies réelles. Les indicateurs seront significatifs dès 10-15 postes enregistrés et soumis.
- **P6 Dashboard Chef :** vue opérationnelle enrichie avec drill-down par machine et par essence, comparaison Matin vs Après-midi détaillée, et statistiques d'effectif.
- **P7 (si temps) :** export Pareto depuis le dashboard, CSS impression, filtre période libre transmis à l'export Excel.
- **Migration DB :** formaliser les colonnes `modifie_le` et `modifie_par` dans `create_tables()` pour la mise en production sur Windows.
- **Rappel CSS impression :** différé à P6 selon décision prise en session (validé par l'utilisateur le 2026-05-03).
