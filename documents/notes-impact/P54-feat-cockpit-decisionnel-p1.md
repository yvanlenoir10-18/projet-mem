# Note d'impact mémoire — P54 : Cockpit décisionnel Chef (P1) — verdict global, signaux critiques, boucle Lean
**Commit :** `b750045` — `feat(chef/p1): cockpit décisionnel — verdict global, manque à gagner remonté, signaux critiques, boucle Lean`
**Date :** 2026-06-03
**Fichiers modifiés :** `app/routes/dashboard.py` (+48 lignes) · `app/templates/chef/dashboard.html` (+208 lignes, −61 lignes)

---

## 1. Ce qui a été implémenté

P54 restructure le cockpit du profil Chef de Production autour de cinq modifications complémentaires. **Aucune nouvelle table de base de données n'est créée** — toutes les données affichées étaient déjà en mémoire ou calculées par des fonctions existantes (règle R7).

### P1-1 — Bandeau de verdict global (VERT / ORANGE / ROUGE)

Une nouvelle fonction `_statut_global(trs_moyen, alertes)` est ajoutée dans `dashboard.py` (ligne 1069). Elle calcule un verdict en trois niveaux à partir de deux signaux : le TRS moyen de la période sélectionnée et les alertes existantes (saisies manquantes + fiches avec anomalies).

Règles de classification :
- **ROUGE** : TRS < 50 % OU ≥ 3 saisies manquantes — verdict « HORS CONTRÔLE »
- **ORANGE** : TRS 50–59 % OU au moins une saisie manquante OU au moins une fiche avec anomalie — verdict « À SURVEILLER »
- **VERT** : TRS ≥ 60 % et aucune anomalie — verdict « SOUS CONTRÔLE »

Le bandeau est affiché en tête du cockpit, avant le HERO TRS, sous les boutons de période. Il affiche l'icône correspondante (Bootstrap Icons `bi-check-circle-fill`, `bi-exclamation-circle-fill`, `bi-x-circle-fill`), le label en majuscules, et une ligne de détail précisant la cause (nb saisies manquantes, nb fiches avec anomalies, ou TRS en valeur absolue).

Le seuil 60 % est le benchmark Cameroun documenté dans le mémoire (chapitre Contexte). Le seuil 50 % correspond à la limite sous laquelle le TRS est considéré critique en scierie africaine (benchmarks Nigeria 46–58 %, Ouganda 32 % comme référence basse).

### P1-2 — Card « Signaux critiques 7 jours » (machine critique + Pareto top-1)

La variable `machine_top` est calculée par `_machine_prioritaire_recent(aujourd_hui, jours=7)`, une fonction déjà existante dans `dashboard.py`. Elle retourne la machine qui cumule le plus d'heures d'arrêt sur les 7 derniers jours.

La variable `pareto_chef` est calculée par `pareto_arrets(equipes)[:3]` — les 3 premières entrées du Pareto existant, limitées aux équipes déjà chargées en mémoire pour la période sélectionnée. Seule la première entrée est affichée dans la card cockpit.

La card « Signaux critiques 7j » présente deux blocs côte à côte :
- Machine critique : nom, durée d'arrêt cumulée sur 7j, lien vers la page Machines
- Cause n°1 Pareto : libellé, durée, lien vers la page Analyse arrêts avec un bouton « Analyser (Ishikawa) » qui ouvre la liste des problèmes

### P1-3 — Intégration des alertes opérateur

Le partial `_alertes.html` (développé en P9b) était inclus dans le layout général mais n'était pas intégré dans `chef/dashboard.html`. P54 ajoute `{% include 'chef/_alertes.html' %}` immédiatement après l'inclusion de `_aujourdhui.html`, avant la barre de sélection de période.

Ce partial affiche jusqu'à trois types de bannières : fiches en attente de validation chef (fond vert pâle), saisies manquantes (fond ochre), brouillons oubliés depuis plus de 2 jours (fond sky). Chaque élément est un lien cliquable vers l'action correspondante.

### P1-4 — Repositionnement du manque à gagner

Le bloc de chiffrage financier (manque à gagner FCFA + décomposition pertes D/P/Q) était positionné après la section « Anomalies P12 » dans le scroll. P54 le remonte en altitude 2, immédiatement après le HERO TRS et avant les anomalies. La donnée financière devient ainsi la deuxième information visible après le verdict, ce qui correspond à sa priorité décisionnelle réelle.

### P1-5 — Card « Boucle Lean active »

La card « Problèmes ouverts » (qui affichait uniquement un compteur) est remplacée par une card « Boucle Lean active » qui présente trois indicateurs sur la même ligne : nombre de problèmes analysés (Ishikawa), nombre d'actions en cours, nombre d'actions clôturées efficaces ce mois. Un lien « Voir les actions » renvoie vers la page Actions Chef.

---

## 2. Lien avec les objectifs du mémoire

**OS4 (Amélioration continue — Ishikawa + Actions)** : le bouton « Analyser (Ishikawa) » dans la card Signaux critiques ferme la boucle Pareto → Ishikawa directement depuis le cockpit. Avant P54, le chef devait naviguer manuellement : dashboard → Analyse arrêts → choisir une cause → créer un problème. Avec P54, le chemin est réduit à deux clics.

**OS6 (Outil de pilotage adapté au terrain)** : le bandeau VERT/ORANGE/ROUGE répond directement à l'argument OS6 sur la lisibilité en situation terrain. Un chef de production qui arrive en début de poste peut lire le statut de l'usine sans déchiffrer les KPI. Ce principe de « management visuel quotidien » est documenté dans Kankkunen & Holopainen (2024) pour les scieries nordiques.

**OS1 (Mesure de la performance — TRS)** : le verdict est ancré sur le TRS avec les seuils du mémoire (60 % cible Cameroun, 50 % seuil critique). Le bandeau traduit visuellement l'hypothèse H3 (TRS réel < 60 %) : si H3 est vérifiée sur les données terrain, le bandeau sera systématiquement ORANGE ou ROUGE — ce qui est une preuve visuelle de l'hypothèse.

---

## 3. Données et calculs mobilisés

**`_statut_global(trs_moyen, alertes)` :** `trs_moyen` est calculé à la ligne 2141 de `dashboard.py` comme la moyenne des TRS valides parmi les équipes de la période (`trs_valeurs`). `alertes` est le dict retourné par `_alertes_chef()` déjà en mémoire — P54 n'ajoute aucune requête SQL.

**`machine_top` :** retourné par `_machine_prioritaire_recent(aujourd_hui, jours=7)`. Cette fonction interroge la base uniquement sur les 7 derniers jours (fenêtre fixe, indépendante de la période sélectionnée dans le sélecteur 7j/30j/90j), ce qui garantit que la card « Signaux critiques » reflète toujours la semaine courante.

**`pareto_chef` :** `pareto_arrets(equipes)[:3]`. `pareto_arrets` est une fonction existante qui agrège les arrêts par catégorie depuis la liste `equipes` déjà en mémoire — zéro requête SQL supplémentaire.

**Boucle Lean :** `nb_problemes_ouverts` et `stats_actions_chef` étaient déjà calculés et injectés dans le template avant P54 — P54 les réutilise dans la nouvelle card sans modification.

---

## 4. Hypothèses testées ou confirmées

**H3 (TRS réel < 60 % en l'absence de système de mesure)** : le bandeau de statut est directement sensible à H3. Avec les données seed (TRS ~70 %, période correctement peuplée), le bandeau affiche VERT. Sur données terrain réelles CUF, si H3 est confirmée (TRS < 60 %), le bandeau affichera ORANGE ou ROUGE. Le cockpit devient ainsi un instrument de vérification visuelle de H3 pendant la démonstration.

**H2 (causes organisationnelles prépondérantes)** : la card Pareto top-1 affiche la cause la plus coûteuse en temps. Si les données terrain confirment H2, la cause « Organisationnelle » apparaîtra en position 1 — visible directement sur le cockpit, sans navigation vers la page Analyse arrêts.

**H1 (écart entre capacité théorique et production réelle)** : le manque à gagner FCFA repositionné en altitude 2 quantifie cet écart en termes financiers, immédiatement après le verdict. La combinaison bandeau + FCFA traduit H1 en langage opérationnel.

**H4 (actions correctives sans investissement majeur)** : la card Boucle Lean active comptabilise les actions en cours et clôturées efficaces. Si des actions à coût nul (réorganisation, ajustement procédure) apparaissent comme efficaces dans les données, la card les rend visibles — argument direct pour H4.

---

## 5. Ce que ce module permet de montrer dans le mémoire

**Section OS6 — Test des 10 secondes :**

Le bandeau VERT/ORANGE/ROUGE peut être présenté comme la réponse opérationnelle au critère des 10 secondes. Une capture avant/après (cockpit P0 vs cockpit P54) montre concrètement la différence entre « 15 sections à poids égal » et « verdict + cause + action en tête de page ». Ce contraste est un argument de conception pour la section Résultats de l'OS6.

**Section OS4 — Boucle Lean visible :**

La card « Boucle Lean active » peut être citée dans la section OS4 pour montrer que l'outil ne se contente pas de mesurer (OS1) ou d'analyser (OS2-3) — il rend visible le cycle d'amélioration continue. Les trois indicateurs (problèmes analysés / actions en cours / actions efficaces) correspondent exactement aux trois étapes du PDCA instrumentées dans l'application.

**Section Méthodologie — Seuils de classification :**

Les seuils VERT/ORANGE/ROUGE (60 % / 50 %) peuvent être explicitement rattachés aux benchmarks du mémoire. Le mémoire cite le 60 % comme cible Cameroun et les références africaines (Ouganda 32 %, Nigeria 46–58 %) comme référence basse. Ces seuils ne sont pas arbitraires — ils sont documentés et défensibles devant un jury.

---

## 6. Limites actuelles

**Verdict non réactif à la période sélectionnée pour `machine_top` :** le sélecteur de période (7j / 30j / 90j) change `trs_moyen` et donc le bandeau, mais `machine_top` est toujours calculé sur les 7 derniers jours fixes. Si le chef sélectionne 90j, le bandeau reflète 90j de TRS mais la machine critique affiche 7j. Ce décalage est mineur en pratique (la machine la plus problématique sur 7j est généralement cohérente avec 90j) mais devrait être documenté dans le mémoire comme limitation connue.

**Seuil 50 % hard-codé :** les seuils de classification (50 % pour ROUGE, 60 % pour ORANGE) sont des constantes dans `_statut_global`. Ils ne sont pas paramétrables via `/admin/parametres`. Un chef qui voudrait ajuster les seuils à 55 % / 45 % devra modifier le code source. Acceptable dans le contexte d'un prototype de mémoire.

**`pareto_chef` lié à la période affichée :** contrairement à `machine_top` (7j fixes), `pareto_chef` est calculé sur `equipes` — la liste de la période sélectionnée. Si le chef sélectionne 90j, la cause n°1 reflète 90j d'arrêts, pas la semaine en cours. Cohérent, mais à noter.

**Bandeau absent sur la vue « pas de données » :** quand aucune équipe n'existe pour la période (code `if not equipes: return render_template(...)` en ligne ~2130), `statut_global` est injecté à `None`. Le template protège ce cas avec `{% if statut_global %}`, mais le chef voit le cockpit sans verdict — acceptable car le cas « zéro fiche sur 30j » ne devrait pas survenir en usage terrain.

---

## 7. Vérification de cohérence avec les notes précédentes

**Note P9b-templates-restants.md :** P9b avait documenté `_alertes.html` comme partial inclus dans le layout général. P54 intègre ce partial directement dans `chef/dashboard.html` pour garantir sa visibilité en tête de cockpit. L'intégration utilise `{% include 'chef/_alertes.html' %}` sans modification du partial — **cohérence confirmée, point en suspens de P9b résolu**.

**Note P7-alertes-validations.md :** P54 utilise `alertes.saisies_manquantes` et `alertes.fiches_a_verifier` dans `_statut_global` — exactement les structures documentées dans P7. Les comptages `len(alertes.get('saisies_manquantes', []))` et `f.get('nb_anomalies', 0)` sont cohérents avec les dicts retournés par `_alertes_chef()`. **Cohérence confirmée.**

**Note P46-boucle-amelioration-actions-chef.md :** la card « Boucle Lean active » réutilise `nb_problemes_ouverts` et `stats_actions_chef` documentés dans P46. Aucun nouveau calcul — P54 réarrange la présentation de données déjà calculées. **Cohérence confirmée.**

**Note P49-fix-seed-volumes-realistes-atteinte-objectif.md :** avec le seed actuel (TRS ~70–87 %), le bandeau affiche VERT sur les données de démonstration. Ce comportement est cohérent avec P49 qui avait ajusté les volumes pour des TRS réalistes mais légèrement optimistes. Sur données terrain réelles (H3 : TRS < 60 %), le bandeau sera ORANGE. **Cohérence confirmée.**

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien avec P54 |
|---|---|
| Kankkunen & Holopainen (2024) — Daily management, UPM Plywood | Le bandeau VERT/ORANGE/ROUGE est la traduction technique du principe de « management visuel quotidien » : un signal de couleur visible sans lire de chiffres. Kankkunen documente ce pattern dans les scieries finlandaises comme critère d'adoption terrain. |
| Jaouane (2022) — Tableau de bord, Général Emballage, Algérie | La restructuration « verdict en tête → cause → action » reproduit la hiérarchie décisionnelle décrite par Jaouane comme optimale pour un tableau de bord de pilotage industriel : synthèse d'abord, détail ensuite. |
| Nakajima (1988) — Introduction to TPM | Les seuils 60 % (objectif) et 50 % (critique) sont cohérents avec les niveaux de TRS définis par Nakajima dans le cadre TPM : TRS < 50 % = situation d'urgence nécessitant une intervention immédiate. |
| Steenkamp et al. (2017) — VMS open-source, Afrique du Sud | La card « Signaux critiques » reproduit le principe du « quick drill-down » du VMS de Steenkamp : une vue agrégée (machine + cause) avec un lien vers l'analyse détaillée, adaptée aux contraintes de temps d'un chef de production en milieu African. |

---

## 9. Prochaines étapes

- **Validation terrain P0 + P1 :** avec P50–P54 en place, l'outil est prêt pour une démonstration complète. Les 5 points P0 (objectif, traçabilité, Aujourd'hui, prix, paramètres) et les 5 points P1 (verdict, machine critique, alertes, repositionnement FCFA, boucle Lean) forment un cockpit cohérent.
- **Ajuster les seuils si nécessaire :** si lors de la démonstration l'encadreur juge que le seuil ORANGE à 60 % est trop bas ou trop haut pour CUF Chaîne 4, modifier les constantes dans `_statut_global` — intervention de 2 lignes.
- **Paramétrage des seuils (P2 potentiel) :** ajouter les seuils VERT/ORANGE/ROUGE dans `/admin/parametres` permettrait au chef de les ajuster sans toucher au code. Ce serait l'argument OS6 ultime (outil adaptable terrain).
- **Captures d'écran pour le mémoire :** la capture `05-chef-dashboard.png` prise le 2026-06-03 montre le cockpit avec bandeau VERT (TRS 70,7 %), manque à gagner 1 324 260 FCFA, card signaux critiques et boucle Lean. Elle peut être utilisée comme illustration dans la section Résultats OS6.
- **Test Windows complet post-P54 :** vérifier que les 5 regards P0 + les 5 éléments P1 sont visibles sur la machine terrain Windows. La liste de vérification est : bandeau statut visible, machine critique peuplée, alertes affichées, manque à gagner en altitude 2, boucle Lean active.
