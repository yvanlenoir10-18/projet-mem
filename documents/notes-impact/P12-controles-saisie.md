# Note d'impact — P12 : Contrôles qualité de saisie (alertes non bloquantes)
> Commit : (en attente) — feat(p12): contrôles qualité de saisie non bloquants
> Date : 2026-05-12
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Ajout d'un module de contrôles qualité qui scanne chaque équipe soumise et détecte quatre catégories d'anomalies de saisie. Les anomalies ne bloquent pas la soumission : elles s'affichent comme avertissements visibles, accompagnés d'une explication et d'une suggestion d'action. Cette stratégie « alerte + confirmation » a été préférée à un blocage strict car, sur un site comme CUF où le chef de poste saisit manuellement après son shift, un blocage pousse au contournement (saisie de valeurs fictives pour faire passer le formulaire). L'alerte douce améliore la qualité des données sans dégrader le flux.

Les quatre règles implémentées sont :
- **R1** — TRS inférieur à 40 % sans aucun arrêt déclaré, qui suggère un oubli de saisie des arrêts.
- **R2** — Arrêt d'au moins 60 minutes sans commentaire d'au moins 10 caractères, qui signale une cause non documentée.
- **R3** — Volume déclassé supérieur à 30 % du volume sorti, qui peut indiquer un problème de réglage des scies ou de qualité matière.
- **R4** — Aucun mètre cube produit mais moins de 480 minutes d'arrêts cumulés, situation strictement incohérente.

Les quatre seuils (40, 60, 10, 30) sont stockés dans la table `Parametre` existante et peuvent donc être ajustés par un administrateur sans modification du code. Le seed est idempotent : les paramètres ne sont ajoutés que s'ils n'existent pas, ce qui permet d'enrichir une instance déjà en production sans toucher aux autres paramètres.

Les anomalies sont affichées à trois endroits : dans le détail de chaque poste (carte ocre dépliée avec icône, code, titre, description et suggestion), dans la liste de l'historique (drapeau compact à côté du numéro d'équipe, avec tooltip), et dans le dashboard chef (bandeau récapitulatif sur la période courante avec compteur par règle).

---

## 2. Fichiers modifiés ou créés

| Fichier | Type | Action |
|---|---|---|
| `cuf-pilotage/app/services/controles_saisie.py` | Service | **Nouveau** — `detecte_anomalies()` + `compte_anomalies_periode()` |
| `cuf-pilotage/app/__init__.py` | Factory | Seed idempotent des 4 paramètres de seuil |
| `cuf-pilotage/app/routes/saisie.py` | Route | Import + injection dans `detail_poste()` et `historique()` |
| `cuf-pilotage/app/routes/dashboard.py` | Route | Import + injection dans `vue_chef()` |
| `cuf-pilotage/app/templates/saisie/detail.html` | Template | Bloc « Contrôles qualité » au-dessus du KPI TRS |
| `cuf-pilotage/app/templates/saisie/historique.html` | Template | Drapeau compact à côté du numéro d'équipe |
| `cuf-pilotage/app/templates/chef/dashboard.html` | Template | Bandeau « Saisies à revoir » au-dessus du manque à gagner |
| `documents/notes-impact/P12-controles-saisie.md` | Documentation | Nouveau |

Aucune migration de base de données. La table `Parametre` existait déjà — seules quatre lignes y sont ajoutées au prochain démarrage de l'application, sans toucher aux données existantes. R7 respectée.

---

## 3. Objectif spécifique du mémoire servi

**OS2 — Mesurer la production réelle de la chaîne 4 à travers un système de collecte de données mis en place sur le terrain** : un système de collecte n'a de valeur que si les données saisies sont fiables. Les contrôles qualité de P12 visent précisément à détecter les saisies douteuses en temps quasi réel, ce qui permet au chef de production de demander une vérification au chef de poste avant que l'information ne soit consolidée dans les rapports.

**OS6 — Concevoir un outil de pilotage adapté aux besoins des différents responsables de CUF pour assurer un suivi continu des performances de la chaîne 4** : la fiabilité du suivi continu dépend de la qualité de la saisie. Sans contrôles, des erreurs systématiques (oubli d'arrêts, déclassement non documenté) faussent durablement les indicateurs et finissent par invalider l'outil aux yeux des utilisateurs.

---

## 4. Lien avec les hypothèses de recherche

**H4 — Des actions correctives sans investissement majeur permettent d'améliorer le TRS et de réduire les pertes financières** : l'ajout de contrôles de cohérence sur la saisie est exactement le type d'action sans investissement matériel que défend H4. Le code coûte uniquement du temps de développement et améliore directement la qualité des données qui servent à orienter les décisions. Cette modification renforce H4.

**H1, H2 et H3 ne sont pas directement concernées par cette modification**. P12 améliore la fiabilité de la mesure (préalable méthodologique), il ne modifie pas les indicateurs eux-mêmes ni leur interprétation.

---

## 5. Technique utilisée et choix architectural

Le service `controles_saisie.py` est entièrement séparé du calcul TRS et du calcul du manque à gagner. Cette séparation des responsabilités permet de modifier les règles de contrôle sans risquer de casser les indicateurs métier. Chaque règle est exprimée sous forme d'un bloc indépendant dans `detecte_anomalies()`, ce qui rend l'ajout d'une cinquième ou sixième règle trivial dans le futur (P13 ou ultérieurement).

Le pré-calcul des anomalies pour la vue `historique` se fait dans la route, en construisant un dictionnaire `anomalies_par_poste = {poste.id: [...]}` que le template consulte. Cette approche est suffisamment performante pour un volume de quelques centaines de postes ; au-delà de plusieurs milliers, il faudrait introduire un cache ou stocker l'information dans une colonne dédiée. Pour la V1, ce n'est pas nécessaire.

Les seuils sont stockés comme chaînes dans la table `Parametre` puis convertis en float dans le service. Cette homogénéité avec les autres paramètres (prix par essence, objectif m³, taux de revente) simplifie l'écriture d'une future page d'administration unique pour tous les paramètres métier.

---

## 6. Contrainte respectée

**Règle R7** : aucune modification de schéma de base de données. Les 4 paramètres sont ajoutés comme lignes dans la table `Parametre` déjà existante, via un seed idempotent qui ne touche pas aux lignes existantes.

**Règle R6** : validation explicite obtenue avant écriture du code. L'utilisateur a confirmé les trois points clés (drapeau dans liste + détail, seuil R3 à 30 %, seuils paramétrables) et a explicitement répondu « GO ».

---

## 7. Limites identifiées

Les seuils retenus sont des valeurs de départ raisonnables mais pas encore validées par l'observation terrain. Le seuil R3 à 30 % est calibré sur les benchmarks de Karsenty 2021 pour l'Afrique centrale ; il sera ajusté après les premières semaines de collecte si les chefs de poste estiment qu'il génère trop d'alertes (bruit) ou pas assez (faux négatifs).

Aucune page d'administration n'est encore proposée pour modifier les seuils depuis l'interface. Ils sont actuellement modifiables uniquement via la base de données ou via la future page admin (P15 ou ultérieurement). Pour la V1, cette absence est acceptable car les valeurs par défaut conviennent à un démarrage de site.

Les anomalies ne sont pas persistées. Elles sont recalculées à chaque consultation. Cette approche est correcte aujourd'hui mais empêchera plus tard l'analyse historique de la qualité de saisie (« a-t-on réduit les R2 entre janvier et mars ? »). Si un besoin de tendance émerge, il faudra introduire une table `AnomalieSaisie` avec horodatage de détection.

Le contrôle R4 (production absente sans arrêt total) ne distingue pas les arrêts officiels (chômage technique, jour férié) des oublis. Pour la V1, un chef de poste qui saisit un jour férié peut déclarer un arrêt couvrant 480 min ; ce n'est pas optimal mais reste pragmatique.

---

## 8. Commandes Windows pour appliquer

```powershell
git pull origin claude/install-claude-excel-6MGzv
.\start.ps1
```

L'application est ensuite accessible sur `http://127.0.0.1:5000`. Aucune migration de base de données n'est nécessaire — au premier lancement, les 4 nouveaux paramètres de seuils sont automatiquement ajoutés à la table `Parametre` si absents.

Pour vérifier visuellement le résultat :
- Détail d'un poste avec TRS bas et sans arrêt : une carte ocre « Contrôles qualité » apparaît au-dessus du KPI TRS.
- Liste de l'historique : drapeau jaune compact à côté du numéro d'équipe pour les postes concernés.
- Dashboard chef : bandeau « Saisies à revoir » avec compteur par règle au-dessus du manque à gagner.

---

## 9. Références bibliographiques mobilisées

- **Mncwango & Mdunge (2025)** — *DMAIC pour OEE bas en industrie agro-alimentaire*, Afrique du Sud : recommandent la validation douce (alerte + confirmation) plutôt que le blocage strict lorsque les utilisateurs saisissent les données après-coup, sur la base d'une étude empirique montrant que le blocage produit davantage de saisies fictives.

- **Laine (2024)** — *Reporting visuel, Metsä Board*, Finlande : insiste sur la lisibilité immédiate des indicateurs pour les utilisateurs non techniciens. Les anomalies sont présentées avec icône, code court, titre, description et suggestion, ce qui correspond exactement à la grammaire visuelle préconisée par Laine.

- **Karsenty (2021)** — *Filière bois en Afrique centrale* : le seuil R3 de 30 % de déclassé est calibré sur les benchmarks Karsenty pour l'Afrique centrale (pertes matière typiques 30-40 %), ce qui évite de générer une alerte sur chaque poste normalement productif.
