# Audit critique — Profil Chef de Production (wood_pilot / CUF Chaîne 4)

> Produit le 2026-06-02 · Branche `claude/install-claude-excel-6MGzv`
> Contexte : préparation d'une démonstration à un encadreur expert scierie, futur utilisateur potentiel du profil Chef.

---

## 1. Résumé exécutif

Le profil Chef de Production dispose d'un **moteur analytique solide et réel** : TRS D×P×Q calculé sur données terrain, attribution financière des pertes en FCFA, Pareto des arrêts, Ishikawa 6M + 5 Pourquoi complet, recommandations déterministes + IA. Ce n'est ni un tableau de bord vide ni une maquette.

Pourtant, il échoue au test des 10 secondes. Pourquoi ? Parce que **tout est au même niveau d'altitude** dans un scroll continu de 15 sections. Le signal visuellement dominant est une grande carte verte « 70,6 % » qui rassure, pendant que 19,5 M FCFA de manque à gagner et un avertissement sur les arrêts non documentés sont enfouis en-dessous. Il n'existe pas de verdict synthétique « usine sous contrôle : OUI/NON ».

Il y a également **un bug de calcul de l'objectif** qui produira une gêne certaine face à un expert : l'atteinte affichée à 147,5 % sur la page Production est un artefact dû à un objectif qui rétrécit pour coller au nombre de fiches soumises, pas un objectif fixe. Un professionnel du bois qui sait que CUF vise 25 m³/jour lira « 147 % d'atteinte » et perdra confiance dans tous les autres chiffres.

**Verdict** : base prometteuse et sérieuse à restructurer sur l'axe de la hiérarchie décisionnelle — pas une reconstruction.

---

## 2. Diagnostic global sans complaisance

| Critère | État | Commentaire |
|---|---|---|
| Données réelles | ✓ | Tous les calculs sont sur données BD, aucun placeholder |
| Moteur TRS | ✓ | D×P×Q par essence et par équipe, avec impact arrêts exacts |
| Attribution financière | ✓ | Manque à gagner, pertes D/P/Q en FCFA, prix snapshot figé |
| Ishikawa 6M + 5 Pourquoi | ✓ | Implémenté complet (4 étapes, rapport A3) |
| Verdict 10 secondes | ✗ | Absent — pas de statut global "sous contrôle / hors contrôle" |
| Hiérarchie visuelle | ✗ | 15 sections à poids égal, pas de cockpit en tête |
| Objectif affiché | ✗ BUG | 147,5 % = artefact (objectif shrinks avec nb postes soumis) |
| Contexte temporel | ✗ | "Aujourd'hui" à 0 si aucune fiche du jour — aucun message d'état |
| Cohérence mémoire | ✗ partiel | 147,5 % contredit H1/H3 (l'usine sous-performe) |
| Navigation | ✓ | 9 pages cohérentes, liens directs actifs |
| Mobile / terrain | ~ | Conçu desktop, tablette terrain non testée pour le profil chef |

---

## 3. Forces actuelles (à préserver absolument)

1. **Moteur TRS réel** — `services/trs.py` : sweep line sur créneaux, impact arrêts (seul le dépassement maintenance planifiée est imputé). C'est le bon algorithme, pas une approximation.
2. **Attribution D/P/Q en FCFA** — `calcule_pertes_equipe()` + `calcule_manque_gagner()` : chiffrage complet avec prix snapshot figé à la soumission, taux revente déclassé, valeur résiduelle déchets.
3. **Ishikawa guidé** — workflow 4 étapes, solidité de l'analyse tracée (≥3 causes + profondeur ≥3 = "Solide"), lien automatique vers ActionChef.
4. **Priorités décisionnelles** — `_priorites_chef()` : 5 priorités max scorées par urgence, en langage naturel, avec CTA. C'est le bon concept — il faut le monter en tête de page.
5. **Boucle Lean traçable** — Pareto → Ishikawa → ActionChef → bilan efficacité avant/après 7j. C'est un argument de fond pour la démo.
6. **Anti-chevauchement** — contrainte bicoupe (machine unique) enforced client + serveur. Cohérence physique garantie.
7. **Scorecard semaine** — tableau 6j × 2 shifts, color-coded TRS. Outil de supervision concret.

---

## 4. Faiblesses et incohérences

### 4.1 Bug critique — Objectif à 147,5 %

**Fichier** : `dashboard.py:1590–1649`, fonction `_resume_production()`

**Problème** : `objectif = objectif_m3 × len(equipes)` — l'objectif total est calculé comme `12,5 m³ × nombre de postes effectivement soumis`, pas comme `12,5 m³ × nombre de postes attendus sur la période`. Si on a soumis 60 fiches sur 30 jours (objectif 60 × 12,5 = 750 m³) mais que le volume réel conforme est 1 106 m³, on obtient 147 % — qui n'a aucun sens métier car la seed génère des volumes d'entrée 22–36 m³ par poste (physiquement cohérent pour le bois brut) mais l'objectif de 12,5 m³ est une capacité de sortie conforme.

**Impact démo** : un expert scierie qui sait que la bicoupe a une capacité physique de 12,5 m³/poste de sortie conforme verra immédiatement que les 147 % sont impossibles. C'est le risque de crédibilité n°1.

**Hypothèse cause** : dans le ratio, le numérateur est probablement `volume_conforme + volume_declass` (sortie totale) au lieu de `volume_conforme` seul (sortie utilisable), OU la capacité de 12,5 m³ est définie comme une capacité de sortie conforme mais la seed génère des volumes d'entrée bien supérieurs. À vérifier dans `_resume_production()`.

### 4.2 Absence de verdict synthétique

La première question d'un chef en arrivant est « est-ce que l'usine est sous contrôle ? ». Il n'y a pas de réponse en tête de page. Le TRS 70,6 % est visible mais sans interprétation directe (au-dessus/en-dessous de l'objectif ? bonne ou mauvaise semaine ?).

### 4.3 Confusion temporelle

La section « Aujourd'hui » affiche des KPI à 0 si aucune fiche n'est soumise aujourd'hui. La collecte terrain commence demain — dès la première fiche soumise, ce composant sera utile. Mais tant qu'il affiche 0, il envoie un signal négatif lors d'une démo.

### 4.4 Prix réservé à l'admin — chef aveugle sur le chiffrage

Le chef voit le manque à gagner en FCFA mais ne peut pas accéder aux prix par essence (`PARAMS_ADMIN_ONLY` dans `admin.py:32-40`). Il ne peut donc pas valider si le calcul financier est cohérent avec les prix réels du marché. Devant un expert, il sera incapable de justifier les montants.

### 4.5 Pas d'identifiant opérateur

`Equipe.operateur_nom` est un texte libre (STR 100, non unique). Impossible d'agréger les performances par opérateur. Ce n'est pas un bug — c'est une limite de modèle connue, à mentionner comme limitation du mémoire.

### 4.6 Pas de table Machine

Les machines sont des strings figées dans `config.py`. Les analyses de criticité sont valides (durée arrêts par machine × catégorie), mais on ne peut pas afficher « la bicoupe est à 65 % de disponibilité sur la semaine » sans calculer manuellement depuis les arrêts.

---

## 5. Audit détaillé de l'existant

| Élément | Problème métier traité | Décision rendue possible | Valeur opérationnelle | Limite actuelle | Verdict | Action recommandée |
|---|---|---|---|---|---|---|
| Cockpit aujourd'hui (`_aujourdhui.html`) | Que faire maintenant ? | Actions urgentes + fiches à traiter | Élevée | Affiché 0 si pas de fiche du jour | Indispensable | Améliorer : message "En attente de saisie" + contexte période récente |
| Priorités décisionnelles (`_priorites_chef`) | Quelle est la priorité n°1 ? | Choisir où agir en premier | Très élevée | Enterrée dans le scroll, pas en tête de page | Indispensable | Reconstruire : monter en haut, simplifier à 3 priorités max avec verdict global |
| TRS global (grand chiffre) | Performons-nous bien ? | Comparer à l'objectif | Élevée | Pas de comparaison explicite objectif/réel sur le même widget | Indispensable | Améliorer : ajouter flèche direction + "vs objectif 60 %" |
| Manque à gagner FCFA | Combien coûte l'écart ? | Décider si le problème vaut une action | Très élevée | Affiché en 3e position, après le TRS | Indispensable | Améliorer : remonter juste après le verdict global |
| Décomposition D×P×Q | D'où vient la perte ? | Choisir le levier (arrêts vs cadence vs qualité) | Très élevée | Bien placée, mais sans recommandation inline | Indispensable | Conserver + ajouter "Principal levier : [D/P/Q]" |
| Simulateur gain FCFA | Quel gain si j'améliore le TRS ? | Prioriser un investissement | Élevée | Fonctionnel | Utile | Conserver (argument académique OS6) |
| Scorecard semaine | Quelle régularité sur 6 jours ? | Identifier un shift qui décroche | Élevée | Bonne lisibilité | Indispensable | Conserver |
| Pareto arrêts (`/analyse/arrets`) | Quelle cause coûte le plus de temps ? | Décider quelle cause analyser en premier | Très élevée | Page séparée, pas de résumé top-1 sur le dashboard | Indispensable | Améliorer : résumé "Cause n°1 : X — Yh perdues" sur le dashboard + lien |
| Recommandations (`/recommandations/`) | Que recommande l'outil ? | Valider ou réfuter une recommandation IA | Élevée | Page séparée, top 3 en bas de dashboard | Utile | Améliorer : top 1 reco avec CTA |
| Ishikawa + 5 Pourquoi (`/problemes/`) | Quelle est la cause racine ? | Choisir la cause à traiter + plan d'action | Très élevée (OS4/H2) | Accessible mais pas lié depuis le Pareto cockpit | Indispensable | Améliorer : bouton "Analyser" depuis le résumé Pareto |
| Actions Chef (`/dashboard/chef/actions`) | Qu'est-ce qui est en cours / en retard ? | Relancer, clôturer, créer | Élevée | Bilan efficacité machine réel | Indispensable | Conserver |
| Page Production & Objectifs | Atteint-on l'objectif ? | Décider si un rattrapage est nécessaire | Élevée | BUG : 147 % artefact | Indispensable | Reconstruire le calcul |
| Page Qualité / Matière | Quel rendement matière par essence ? | Identifier l'essence qui perd le plus | Élevée | Pas d'alerte inline si déclassé > seuil | Utile | Améliorer : alerte seuil inline |
| Page Machines & Arrêts | Quelle machine cumule le plus d'arrêts ? | Prioriser la maintenance | Élevée | Données réelles, bien structurée | Indispensable | Conserver |
| Page Pertes financières (`/pertes`) | Comment sont réparties les pertes ? | Justifier un investissement maintenance | Très élevée | Accessible, drill-down par machine/essence | Indispensable | Conserver + prix visibles au chef |
| Export Excel | Archiver le rapport mensuel | Partager avec la direction | Utile | Fonctionnel | Secondaire | Conserver |
| Alertes chef (`_alertes.html`) | Saisies manquantes / brouillons | Relancer les opérateurs | Élevée | Template existe mais **non inclus** dans dashboard.html | Utile | Intégrer dans dashboard.html |

---

## 6. Angles morts

| Question chef | Réponse actuelle | Ce qui manque | Donnée nécessaire | Fonctionnalité à créer |
|---|---|---|---|---|
| L'usine est-elle sous contrôle ? | ✗ Absent | Verdict global OUI/NON | TRS du jour vs objectif + anomalies bloquantes | Widget statut global (3 couleurs) en tête du cockpit |
| Quelle est la machine critique en ce moment ? | ~ Partiel (Pareto page séparée) | Résumé "Machine n°1 cumule X h d'arrêts" sur le dashboard | Durée arrêts par machine cette semaine | Résumé machine critique sur le cockpit |
| Quel est l'arrêt le plus coûteux ? | ✗ Absent sur cockpit | L'arrêt qui a coûté le plus en FCFA | Durée × capacité × prix | Ligne "Arrêt le plus coûteux : [cause] [machine] = X FCFA" |
| Quelle est la principale perte de matière ? | ~ Page Qualité séparée | Résumé rendement + essence la plus problématique | Volume déclassé/déchet par essence | Widget rendement matière sur cockpit |
| Quelle est la principale perte de temps ? | ~ Pareto sur page séparée | Cause n°1 Pareto sur cockpit | Durée arrêts par cause | Résumé Pareto top-1 sur cockpit |
| Quelle est la principale perte financière ? | ~ Manque à gagner présent, trop bas | Position plus haute | FCFA calculés | Repositionnement |
| Quel shift a besoin d'accompagnement ? | ~ Comparaison Matin/Soir existe | Pas d'alerte si un shift décroche systématiquement | TRS par shift sur 7j | Alerte "Soir décroche : TRS 48 % vs 65 % Matin" |
| Quels objectifs sont menacés aujourd'hui ? | ~ Partiel si données du jour | Projection "À ce rythme, objectif atteint à X %" | Volume saisi + nb postes restants | Widget projection journalière |

---

## 7. Architecture fonctionnelle cible

### Principe directeur

**Altitude d'abord.** Le cockpit doit être lisible en 10 secondes via 3 zones visuellement distinctes :
- Zone rouge (altitude 1) : verdict + problème n°1 + action n°1
- Zone orange (altitude 2) : causes + tendances + scorecard
- Zone verte (altitude 3) : détails, export, historique

### Module 1 — Cockpit exécutif (altitude 1) — À créer / refactorer

**Objectif** : répondre à « est-ce que l'usine est sous contrôle ? » en un coup d'œil.

Contenu de la bande supérieure fixe :
- Statut global : VERT (TRS ≥ 60 % + pas d'anomalie bloquante) / ORANGE (TRS 50–60 % ou anomalies) / ROUGE (TRS < 50 % ou arrêt non documenté)
- TRS du jour ou de la dernière période + flèche direction vs semaine précédente
- Manque à gagner FCFA de la semaine
- Problème n°1 en une ligne (cause principale Pareto ou anomalie bloquante)
- Action n°1 (première priorité décisionnelle, déjà calculée par `_priorites_chef`)

**Données requises** : toutes existantes.
**Effort** : moyen — refactoring de position, aucun nouveau calcul.

### Module 2 — Postes du jour — Existe, améliorer

Si aucune fiche du jour : message « En attente de la première saisie » + TRS du dernier poste connu.

### Module 3 — Pertes D×P×Q + Manque à gagner — Existe, remonter

Repositionner immédiatement sous le cockpit (actuellement profond dans le scroll).

### Module 4 — Machine critique + Pareto top-1 — À créer en résumé cockpit

Deux lignes sur le cockpit :
- « Machine critique : Bicoupe — 3h30 d'arrêts cette semaine »
- « Cause n°1 Pareto : [cause] — Yh = Z FCFA »

Avec lien vers page Causes d'arrêts + bouton « Analyser (Ishikawa) ».

### Module 5 — Boucle Lean visible — Existe, à rendre visible

Une section « Boucle Lean active » sur le cockpit : nombre de problèmes en cours + nombre d'actions en cours + nombre d'actions efficaces ce mois. Arguments OS4/H2 pour le mémoire.

### Modules 6 et 7 — Scorecard + Recommandations — Conserver tels quels

---

## 8. Parcours utilisateur idéal (chef, 9h00)

1. Ouvre le tableau de bord → voit en 3 secondes : **VERT / ORANGE / ROUGE** + TRS + manque à gagner du jour.
2. Si ROUGE → lit le problème n°1 (une ligne) + l'action n°1 (un bouton).
3. Clique « Voir les causes » → Pareto → voit la cause la plus coûteuse en temps et en FCFA.
4. Clique « Analyser » → ouvre Ishikawa → saisit 2-3 causes → remonte les 5 Pourquoi → identifie cause racine → crée ActionChef.
5. Revient en fin de poste → valide les fiches soumises par les opérateurs.
6. En fin de semaine → exporte le rapport Excel mensuel.

Ce parcours est **techniquement possible aujourd'hui** — il manque uniquement le cockpit de premier regard (étape 1) et le bouton « Analyser » depuis le Pareto du cockpit (étape 3→4).

---

## 9. Conservation / suppression / fusion / reconstruction

| Élément | Action | Justification |
|---|---|---|
| Moteur TRS (`trs.py`) | **Conserver** | Calcul correct, données réelles |
| Attribution financière D/P/Q | **Conserver** | Argument clé démo |
| Ishikawa 6M + 5 Pourquoi | **Conserver** | Complet et fonctionnel |
| Actions Chef + bilan efficacité | **Conserver** | Boucle Lean réelle |
| Scorecard semaine | **Conserver** | Outil de supervision concret |
| Simulateur gain FCFA | **Conserver** | Argument académique OS6 |
| Recommandations déterministes + IA | **Conserver** | Différenciateur fort |
| Cockpit "Aujourd'hui" | **Améliorer** | Ajouter verdict global + message si vide |
| Calcul objectif (`_resume_production`) | **Reconstruire** | Bug métier — objectif doit être fixe (× nb jours, pas × nb fiches) |
| Position Manque à gagner | **Améliorer** | Remonter en altitude 1 |
| Position Priorités décisionnelles | **Améliorer** | Première section visible, pas en scroll |
| Machine critique — résumé cockpit | **Créer** | Angle mort critique |
| Pareto top-1 sur cockpit | **Créer** | Lien cockpit → Pareto → Ishikawa |
| Boucle Lean visible (widget) | **Créer** | Argument démo OS4 |
| Alertes chef (`_alertes.html`) | **Intégrer** | Template exist mais non inclus dans dashboard.html |
| Prix visibles par le chef | **Améliorer** | Actuellement admin-only — chef doit voir les prix pour valider le chiffrage |

---

## 10. Priorisation P0 → P3

### P0 — Démo de demain

| # | Recommandation | Fichier | Effort | Risque si non fait |
|---|---|---|---|---|
| P0-1 | **Corriger le bug objectif** : objectif = `12,5 × 2 × nb_jours_periode` (fixe), pas `12,5 × nb_postes_saisis` | `dashboard.py:1590` `_resume_production()` | 2h | 147 % → perte de crédibilité totale |
| P0-2 | **Seed données récentes** : modifier `seed_data.py` pour générer `aujourd'hui − 7 jours` | `seed_data.py` ligne ~25 | 1h | "Aujourd'hui" reste à 0 pendant la démo |
| P0-3 | **Message cockpit si vide** : `{% if fiches_du_jour %}...{% else %}En attente de saisie{% endif %}` | `templates/chef/_aujourdhui.html` | 30 min | Section vide = prototype non fini |
| P0-4 | **Rendre les prix consultables par le chef** en lecture seule sur `/pertes` | `admin.py` ou template `pertes` | 30 min | Chef ne peut pas justifier les FCFA |
| P0-5 | **Vérifier les prix seed** (Ayous 180k, Iroko 420k, Azobé 280k, Movingui 320k FCFA/m³) vs marché réel CUF | `seed_data.py:119-124` | 15 min vérification | L'encadreur connaît les vrais prix |

### P1 — MVP opérationnel (cette semaine)

| # | Recommandation | Effort |
|---|---|---|
| P1-1 | Widget statut global OUI/NON (3 couleurs) en tête du cockpit | Moyen |
| P1-2 | Résumé machine critique + Pareto top-1 sur cockpit avec bouton « Analyser (Ishikawa) » | Moyen |
| P1-3 | Intégrer `_alertes.html` dans `dashboard.html` | Faible |
| P1-4 | Repositionner Manque à gagner avant le TRS global | Faible |
| P1-5 | Widget boucle Lean (X problèmes actifs, Y actions en cours, Z actions efficaces) | Faible |

### P2 — Version avancée (avant soutenance)

| # | Recommandation | Dépendances |
|---|---|---|
| P2-1 | Alerte "Soir décroche" si TRS shift du soir < TRS shift du matin de X pts sur 7j | Données existantes, règle à créer |
| P2-2 | Alerte déclassement par essence sur page Qualité (seuil paramétrable) | Seuil existant, alerte inline à ajouter |
| P2-3 | Projection journalière « À ce rythme, X % de l'objectif atteint » | Volume saisi + nb postes restants |
| P2-4 | Table Machine (capacité actuelle, taux disponibilité calculé depuis arrêts) | Nouvelle table, migration |
| P2-5 | Identifiant opérateur (FK User optionnel sur Equipe) | Refactor modèle |

### P3 — Vision long terme

| # | Recommandation |
|---|---|
| P3-1 | Prédiction maintenance préventive (arrêts récurrents → alertes prévisionnelles) — nécessite ≥ 3 mois de données |
| P3-2 | SQCDL board quotidien (S et L manquent actuellement) |
| P3-3 | Matrice compétences opérateurs (dépend de P2-5) |
| P3-4 | EHS / Andon (hors périmètre mémoire actuel) |

---

## 11. Plan d'action concret — démo de demain

### Étape 1 — Corriger le bug objectif (P0-1 — 2h)

Dans `_resume_production()` (dashboard.py:1590), remplacer le calcul de `objectif` :

```python
# AVANT (bug — objectif shrinks avec nb postes soumis)
objectif = objectif_m3 * len(equipes)

# APRÈS (correct — objectif fixe basé sur la période)
nb_jours_periode = max(1, (date_fin - date_debut).days + 1)
objectif = objectif_m3 * 2 * nb_jours_periode  # 2 postes/jour × jours × 12,5 m³
```

Le même pattern existe dans `_resume_production_par_equipe()` (lignes ~1660–1680) — appliquer la même correction.

Après correction, l'atteinte sur 30 jours (60 postes × 12,5 m³ = 750 m³ attendus) face à une production conforme ~500–600 m³ donnera 65–80 % — cohérent avec H3 (TRS < 60 %).

### Étape 2 — Seed données récentes (P0-2 — 1h)

Dans `seed_data.py`, remplacer la période de génération :

```python
# AVANT
date_debut = date(2026, 4, 1)
date_fin = date(2026, 4, 30)

# APRÈS (7 jours incluant aujourd'hui)
from datetime import date, timedelta
date_fin = date.today()
date_debut = date_fin - timedelta(days=6)
```

Relancer : `cd cuf-pilotage && python seed_data.py`. Cela peuple la section « Aujourd'hui » du cockpit et la scorecard semaine.

### Étape 3 — Message cockpit si vide (P0-3 — 30 min)

Dans `templates/chef/_aujourdhui.html`, entourer le bloc KPI du jour d'une condition :
```jinja
{% if fiches_du_jour %}
  {# contenu actuel des KPI #}
{% else %}
  <div class="wp-card" style="text-align:center; color: var(--wp-muted); padding: 24px;">
    <i class="bi bi-hourglass-split"></i>
    En attente de la première saisie du jour
    — Dernière période analysée : {{ periode_label }}
  </div>
{% endif %}
```

### Étape 4 — Prix consultables par le chef (P0-4 — 30 min)

Dans le template `/pertes`, ajouter un encart discret avec les prix actuels en lecture seule. Ou, option plus propre : dans `admin.py`, déplacer les clés `prix_*` de `PARAMS_ADMIN_ONLY` vers `PARAMS_CHEF` avec `readonly=True` dans le formulaire.

### Étape 5 — Vérification seed vs marché (P0-5 — 15 min)

Confirmer avec l'encadreur ou via une source fiable que les prix seed (Ayous 180k FCFA/m³, Iroko 420k, Azobé 280k, Movingui 320k) sont dans les bons ordres de grandeur pour la filière bois Cameroun 2026. Ajuster dans `Parametre` via `/admin/parametres` si nécessaire — pas besoin de toucher au code.

### Script de vérification post-corrections

```bash
bash .claude/skills/run-cuf-pilotage/smoke.sh
python .claude/skills/run-cuf-pilotage/screenshot.py chef
# Vérifier 05-chef-dashboard.png :
#   — TRS visible avec flèche direction
#   — Objectif affiché < 100 % (cohérent avec H3)
#   — Section "Aujourd'hui" peuplée
```

---

## 12. Questions à poser à l'encadreur pendant la présentation

1. **« Le point de comptage est avant la bicoupe — est-ce que votre pratique CUF valide que volume_entree correspond bien à ce passage fixe ? »** → Confirme la cohérence avec la règle métier terrain.

2. **« Les capacités par essence (Ayous, Azobé, Iroko, Movingui) sont configurables ici [montrer Paramètres] — correspondent-elles à ce que vous observez sur la chaîne 4 ? »** → Si non, correction en 30 secondes pendant la démo : argument OS6 (outil adaptable).

3. **« La catégorie "Organisationnelle" contribue le plus au Pareto dans nos données de test — est-ce cohérent avec ce que vous observez terrain ? »** → Ouvre la discussion H2 (causes organisationnelles vs techniques).

4. **« Pour la boucle Lean [montrer Pareto → Ishikawa → Action → Bilan] : est-ce que ce workflow correspond à comment vous traitez un problème récurrent aujourd'hui ? »** → Valide l'adéquation terrain de OS4.

5. **« Le manque à gagner estimé à X FCFA par semaine — est-ce un ordre de grandeur que vous reconnaissez, ou est-il sur- ou sous-estimé ? »** → Valide (ou corrige) le chiffrage FCFA.

6. **« Quel est votre outil de suivi au quotidien actuellement (tableau blanc, Excel, rien) ? »** → Donne le contexte de comparaison pour OS6 (avant / après) et renforce l'argument adoption terrain.

---

## 13. Vision produit long terme

Le profil Chef de Production couvre aujourd'hui les niveaux 1 et 2 du modèle de maturité ProBeya :
- **Niveau 1 (Réactif)** : saisie, statuts, validation
- **Niveau 2 (Structuré)** : TRS, Pareto, Ishikawa, pertes FCFA

Pour atteindre le **niveau 3 (Optimisé)**, les étapes sont :
1. Cockpit décisionnel 10 secondes (P0/P1 — en cours)
2. Pilotage par opérateur (P2 — nécessite FK opérateur)
3. Pilotage prédictif par machine (P3 — nécessite historique ≥ 3 mois)

Le **niveau 4 (Excellence)** nécessiterait des capteurs machine (IoT) hors scope du mémoire actuel.

---

## 14. Conclusion

> Le profil Chef de Production actuel est-il déjà un véritable outil de pilotage industriel, une base prometteuse à renforcer, ou un tableau de bord à reconstruire en profondeur ?

**C'est une base sérieuse qui nécessite un travail éditorial ciblé, pas une reconstruction.**

Le moteur analytique est réel, complet et calculé sur données terrain : TRS D×P×Q, attribution financière des pertes en FCFA, Pareto, Ishikawa guidé, boucle Lean avec bilan d'efficacité. Ce n'est pas un tableau de bord générique — c'est un outil construit sur les contraintes spécifiques de la chaîne 4 (bicoupe goulot, 4 essences, anti-chevauchement, prix snapshot figés).

Ce qui manque est un **cockpit de premier regard** : un verdict global, le problème n°1 et l'action n°1 visibles sans scroller. Aujourd'hui, 15 sections à poids égal imposent au chef de construire lui-même la synthèse — c'est l'inverse de ce qu'un outil de pilotage doit faire.

Il y a un bug de calcul de l'objectif (P0-1) qui est le seul élément capable de faire perdre confiance instantanément à un professionnel du secteur bois — et qui contredit directement les hypothèses H1/H3 du mémoire.

Avec les corrections P0 (4–5 heures) et les améliorations P1 (1–2 jours), l'outil sera à la hauteur d'une démonstration professionnelle et d'une utilisation terrain réelle.

---

*Fichiers clés P0 : `dashboard.py:1590` (bug objectif) · `_aujourdhui.html` (message vide) · `admin.py` (prix chef) · `seed_data.py:25` (dates récentes)*
*Smoke test de référence : `bash .claude/skills/run-cuf-pilotage/smoke.sh` — 16/16 checks doivent rester verts après chaque modification.*
