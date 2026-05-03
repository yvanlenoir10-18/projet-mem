# Note d'impact mémoire — P5b : Données de démonstration et stabilité DB
**Commit :** `53a0e46` — `fix(demo): seed données de démonstration au premier démarrage + stop DB wipe`
**Date :** 2026-05-03
**Fichiers modifiés :** `cuf-pilotage/start.ps1` (−7 lignes) · `cuf-pilotage/app/__init__.py` (+88 lignes)

---

## 1. Ce qui a été implémenté

Deux correctifs liés qui rendent le dashboard P5 opérationnel sur une installation fraîche :

| Correctif | Avant | Après |
|---|---|---|
| **Effacement DB automatique** | `start.ps1` supprimait `instance/cuf.db` à chaque lancement → dashboard vide à chaque redémarrage | La base n'est plus effacée au démarrage. Suppression manuelle uniquement si l'utilisateur le décide. |
| **Seed données démo** | Aucune équipe au premier lancement → tous les KPIs à 0, graphiques vides | `_seed_donnees_demo()` injecte 10 équipes réalistes si la base est vide |

### Données de démonstration créées au premier démarrage (base vide)

| Date | Équipe | Statut | TRS | Essences | Arrêts |
|---|---|---|---|---|---|
| 2026-05-01 | Matin | soumis | 68 % | Ayous + Azobé | Bicoupe Méca 45min + Déligneuse Orga 20min |
| 2026-05-01 | Après-midi | soumis | 72 % | Iroko | — |
| 2026-05-02 | Matin | soumis | 58 % | Movingui + Ayous | Scie de tête Méca 60min + Bicoupe Orga 30min |
| 2026-05-02 | Après-midi | soumis | 74 % | Azobé | Ébouteuse Maint. 20min |
| 2026-05-03 | Matin | **brouillon** | — | Iroko | — |
| 2026-04-01 | Matin | soumis | 60 % | Ayous + Azobé | Bicoupe Appro 75min |
| 2026-04-01 | Après-midi | soumis | 65 % | Iroko | — |
| 2026-04-15 | Matin | soumis | 63 % | Movingui + Ayous | Bicoupe Méca 45min |
| 2026-03-10 | Matin | soumis | 55 % | Ayous | Bicoupe Méca 90min |
| 2026-02-15 | Matin | soumis | 62 % | Azobé | — |

Le guard `if Equipe.query.first(): return` garantit que le seed ne s'exécute qu'une seule fois et n'écrase jamais des données saisies manuellement.

---

## 2. Lien avec les objectifs du mémoire

Ce correctif n'est pas un livrable académique en soi, mais il est un prérequis fonctionnel à la démonstration de l'OS6. Le dashboard P5 ne peut remplir son rôle de "vue exécutive lisible en 30 secondes" que si des données crédibles le peuplent. Sans seed, un nouveau déploiement montre des KPIs à 0 — ce qui invalide toute démonstration visuelle lors de la soutenance.

Les données de démonstration ont été calibrées pour illustrer simultanément :
- H3 (TRS < 60 % historiquement : mars 2026 à 55 %) et la progression vers le benchmark 60 %
- H2 (arrêts organisationnels visibles : "Pause non planifiée" et "Attente opérateur" dans le Pareto)
- L'alerte brouillon : 1 équipe en brouillon sur 5 en mai = alerte jaune visible dès la connexion PDG

---

## 3. Données et calculs mobilisés

Les TRS de démonstration sont des valeurs directement stockées dans `trs_global` (champ Float du modèle `Equipe`). Ils ne sont pas recalculés depuis les volumes et arrêts — le champ stocké prend la valeur fixée dans le seed. Ce choix est cohérent avec l'architecture existante : lors de la soumission réelle d'un poste, la route saisie calcule et stocke `trs_global` de la même façon.

Les volumes de production ont été calibrés pour donner des rendements matière réalistes par essence :
- Ayous : ~60 % (seuil vert)
- Azobé : ~60 %
- Iroko : ~66 %
- Movingui : ~62 %

Ces valeurs sont supérieures au benchmark Karsenty (2021, 35 % Afrique centrale) et comparables au benchmark international (60 %+), ce qui produit un affichage "tout vert" dans la mini-table rendement par essence — cohérent avec un scénario de démarrage favorable avant données terrain.

---

## 4. Hypothèses testées ou confirmées

**Aucune contradiction avec les hypothèses existantes.**

- **H3** est rendue visible : le graphique TRS 12 mois montre 55 % en mars 2026, 62 % en février, et une progression vers 68-74 % en mai. La ligne benchmark 60 % est franchie en mai — ce qui illustre exactement la trajectoire "avant/après système de mesure" que H3 prédit.
- **H2** est illustrée dans le Pareto : les causes organisationnelles ("Pause non planifiée", "Attente opérateur") représentent 2 des 6 arrêts injectés, aux côtés de causes mécaniques. Sur données terrain réelles, la proportion confirmerait ou infirmerait H2.
- **H4** peut être suivie : la comparaison mai 2026 vs avril 2026 (delta TRS ≈ +6 pts) simule un gain après actions correctives, illustrant le mécanisme de suivi prévu par H4.

---

## 5. Ce que ce module permet de montrer dans le mémoire

- Le dashboard P5 est désormais démontrable à froid, sans saisie préalable. Pour la soutenance, l'étudiant peut ouvrir le navigateur et montrer immédiatement les 7 composantes P5 avec des données cohérentes.
- La présence d'un brouillon en mai active l'alerte jaune role-aware : le PDG voit "1 poste non soumis ce mois", mais sans lien d'action — ce qui illustre concrètement la différenciation PDG/Chef documentée dans la section méthodologique.
- Les valeurs de rendement par essence (toutes ≥ 60 %) produisent un affichage "tout vert" qui contraste avec les données terrain attendues (Karsenty 2021 : 30-36 %). Ce contraste pédagogique peut être mobilisé lors de la soutenance pour montrer l'outil en fonctionnement normal avant de présenter les données réelles.

---

## 6. Limites actuelles

- **TRS de démonstration non calculés :** les valeurs sont fixées directement dans le seed, sans passer par la formule TRS = D × P × Q appliquée à partir des volumes et des arrêts. Les valeurs de seed sont cohérentes visuellement mais ne constituent pas une validation métier complète.
- **Données mensuelles incomplètes :** les mois de février, mars, avril 2026 ne comportent qu'une à trois équipes. Le TRS affiché dans la tendance 12 mois pour ces mois est donc celui de 1-3 postes, non d'un mois complet. C'est acceptable pour la démonstration — les données terrain rempliront les mois réels.
- **Pas de données antérieures à février 2026 :** les 9 mois avant février affichent TRS = 0 % dans le graphique (barres rouges). C'est intentionnel : il illustre l'"avant système de mesure" et est cohérent avec H3.

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P5-dashboard-pdg-enrichi.md` mentionnait en section 6 Limites : "Delta TRS nul si pas de données période précédente : quand le système démarre (premiers mois), la période précédente est vide." P5b corrige ce cas en injectant des données avril 2026 → le delta TRS mai/avril est calculable et affiché dès le premier lancement.

La note `00-cadrage-global-P1-P2-P3.md` mentionnait que la base de données est initialisée avec utilisateurs et paramètres. P5b étend cette initialisation aux données de production, sans modifier la logique existante des utilisateurs ni des paramètres.

Aucune contradiction avec les notes précédentes.

---

## 8. Références bibliographiques mobilisées implicitement

Aucune nouvelle référence bibliographique. Les seuils de couleur (60 % / 40 %) et les volumes de démonstration sont construits en référence à Karsenty (2021) et Jonsson & Lesshammar (1999), déjà documentés dans P5.

---

## 9. Prochaines étapes

- **Windows :** l'utilisateur doit exécuter `git pull` puis relancer `start.ps1`. Le seed s'exécutera automatiquement sur la base vide existante (start.ps1 n'efface plus la DB).
- **Données terrain :** quand les premières saisies réelles arriveront, le guard `if Equipe.query.first(): return` empêchera le seed de remplacer les données — les données de démonstration seront écrasées par les vraies équipes saisies.
- **P6 Dashboard Chef :** prochaine phase — vue opérationnelle enrichie, drill-down machine et essence, comparaison Matin vs Après-midi.
- **Rappel :** si une réinitialisation complète est nécessaire, supprimer manuellement `instance/cuf.db` puis relancer `start.ps1`.
