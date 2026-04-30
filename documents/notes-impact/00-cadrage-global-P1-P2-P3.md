# Note d'impact mémoire — Cadrage global + Phase P3

> Générée le : 2026-04-30
> Phases couvertes : P1 (Saisie), P2 (Analyse pertes), P3 (Workflow statuts)
> Application : CUF Pilotage — Flask/SQLite — Scierie CUF Ebolowa

---

## A. Cadrage global de l'application CUF Pilotage

### Finalité générale

L'application CUF Pilotage est un système de collecte, de traitement et de visualisation des données de production de la chaîne 4 de la scierie industrielle CUF d'Ebolowa. Elle constitue l'outil de pilotage décrit à l'objectif spécifique 6 du mémoire : concevoir un outil adapté aux besoins des différents responsables de CUF pour assurer un suivi continu des performances. L'application est développée en Flask (Python) avec une base SQLite, déployée localement sur le site de l'entreprise.

### Modules implémentés (P1, P2, P3)

| Phase | Module | Statut |
|---|---|---|
| P1 | Saisie des équipes — Modèles Equipe/Production/Arret + calcul TRS automatique + export Excel | Complété |
| P2 | Analyse des pertes financières — filtre mensuel calendaire, drill-down D/P/Q, Pareto | Complété |
| P3 | Workflow statut brouillon → soumis → verrouillé + contrôle d'accès par rôle | Complété |

### Types de données collectées

L'application structure la collecte autour de trois niveaux :

**Niveau équipe (par poste de 8h) :**
- Date, créneau horaire (Matin / Après-midi), effectif présent, notes libres
- Statut de saisie (brouillon, soumis, verrouillé), horodatage de soumission, trace de modification

**Niveau production (une ligne par essence traitée) :**
- Essence parmi : Ayous, Azobé, Iroko, Movingui
- Volume en entrée (grumes, m³)
- Volume conforme (planches satisfaisant les contrats, m³)
- Volume déclassé (planches vendues localement à prix réduit, m³)
- Volume déchets = calculé automatiquement (entree − conforme − déclassé)
- Prix snapshot (figé à la soumission, en FCFA/m³)

**Niveau arrêt machine (un enregistrement par arrêt) :**
- Machine concernée parmi : Bicoupe, Scie de tête, Déligneuse, Ébouteuse, Dédoubleuse, Autre
- Heure début, heure fin, durée calculée automatiquement (en minutes)
- Cause (texte libre), catégorie parmi : Panne mécanique, Panne électrique, Manque matière, Maintenance planifiée, Autre

### Acteurs et rôles

| Rôle | Accès | Responsabilité |
|---|---|---|
| Agent administratif (saisie) | Crée et soumet ses propres équipes | Saisie quotidienne sur le terrain |
| Chef de production (chef) | Modifie les équipes soumises, verrouille, voit les dashboards | Validation et supervision |
| PDG (admin) | Accès total + déverrouillage | Lecture des indicateurs financiers |

### Indicateurs calculés

**TRS (Taux de Rendement Synthétique) :**
- Durée totale théorique : 480 min (poste de 8h)
- Disponibilité = (480 − durée_arrêts_non_planifiés) / 480
- Performance = volume_sorti / (temps_disponible_h × capacité_h), où capacité_h = 1,5625 m³/h (paramètre réglable)
- Qualité = volume_conforme / volume_sorti
- TRS global = D × P × Q × 100

**Pertes financières en FCFA :**
- Perte D = (durée_arrêts/60) × capacité_h × prix_moyen_pondéré
- Perte P = (capacité_disponible_théorique − volume_sorti) × prix_moyen
- Perte Q = volume_déclassé × prix × (1 − taux_revente_30%) + volume_déchets × prix

**Objectif de référence :** 12,5 m³/poste (8h × 1,5625 m³/h) — distinct de l'objectif empirique de 25 m³ affiché par CUF, non encore validé par chronométrage terrain.

### Hypothèses provisoires de l'application

| Hypothèse | Statut | Remarque |
|---|---|---|
| H1 : capacité théorique < 25 m³/poste | Confirmée par paramètre | La capacité_h = 1,5625 m³/h donne 12,5 m³/8h — à valider terrain |
| H3 : TRS réel < 60% | Mesurable dès les premières saisies | |
| Arrêts partagés sur toute l'équipe | Décision de conception | La bicoupe est le goulot commun |
| Prix par essence stable dans le temps | Simplifié par le snapshot | Variations saisonnières ignorées |
| 2 créneaux seulement (Matin/Après-midi) | Décision de conception | Pas de poste de nuit actuellement |

### Limites actuelles du système

1. **Capacité théorique non encore validée** — le paramètre `capacite_equipe_h = 1,5625 m³/h` est provisoire, non issu d'un chronométrage réel.
2. **Prix par essence non encore renseignés** — les snapshots seront NULL tant que les prix ne sont pas saisis dans les Parametre.
3. **Aucune donnée réelle** — l'application est développée mais pas encore alimentée avec des données terrain.
4. **Pas de gestion des essences mixtes sur une même passe** — une ligne de production = une essence.
5. **Pas de traçabilité des grumes individuelles** — seuls les volumes agrégés par équipe sont saisis.

### Conséquences sur la fiche de collecte

Champs obligatoires côté fiche :
- Date + créneau (Matin/Après-midi), effectif présent
- Pour chaque essence traitée : volume entrée (m³), volume conforme (m³), volume déclassé (m³)
- Pour chaque arrêt : machine, heure début, heure fin, cause, catégorie

Champs calculés automatiquement (ne pas mettre sur la fiche) :
- Volume déchets, durée arrêt, TRS, pertes FCFA

Contraintes de saisie terrain :
- Les volumes doivent être mesurés ou estimés en m³
- Les heures d'arrêt doivent être notées au moment de l'arrêt
- Le volume en entrée (grumes) doit être évalué avant transformation

---

## B. Impact spécifique — Phase P3 : Workflow brouillon → soumis → verrouillé

### 1. Contexte global

Avant P3, l'application n'avait qu'un seul statut implicite pour les équipes : une fois saisie, une équipe existait dans la base sans distinction entre données provisoires et données validées. Les dashboards et exports incluaient donc potentiellement des données incomplètes. P3 introduit un cycle de vie explicite pour chaque enregistrement, transformant l'application d'un simple formulaire de saisie en un système de gestion documentaire avec contrôle qualité des données.

### 2. Résumé de la fonctionnalité

P3 instaure trois états pour chaque équipe :

- **Brouillon** : données provisoires, modifiables par l'auteur uniquement. Non visible dans les analyses.
- **Soumis** : données validées par l'agent. Prix figés à cet instant (prix_snapshot). Modifiable par le chef/admin. Visible dans les analyses.
- **Verrouillé** : données définitives, non modifiables sauf déverrouillage admin. Automatique après 3 jours ou manuel par le chef.

Le contrôle d'accès est centralisé dans deux helpers (_peut_modifier, _peut_soumettre) et les dashboards filtrent systématiquement sur _STATUTS_ANALYSES = ('soumis', 'verrouille').

### 3. Impact sur la collecte des données

**Données rendues nécessaires :**
L'effectif, les volumes et les arrêts doivent tous être renseignés avant la soumission, car celle-ci fige les prix et déclenche le calcul définitif du TRS.

**Données désormais estimées :**
Le prix_snapshot est figé depuis la table Parametre au moment de la soumission. Si les prix ne sont pas renseignés avant la première soumission, toutes les pertes FCFA seront nulles. **Contrainte terrain critique : les prix par essence doivent être saisis dans le système avant le début de la collecte.**

**Contraintes terrain nouvelles :**
- Le délai entre la fin du poste et la soumission devient un paramètre de qualité.
- Une soumission tardive (après 3 jours) verrouille automatiquement, empêchant toute correction ultérieure.
- L'agent ne peut pas modifier une équipe déjà soumise — il doit vérifier ses données avant de soumettre.

### 4. Impact sur la fiche de collecte

La fiche de collecte doit être structurée pour permettre une vérification complète avant soumission numérique.

Ajouts à envisager :
- Une case "Vérification finale" à cocher par l'agent avant transmission
- Une colonne "Heure de fin de saisie" pour tracer le délai terrain → système

Pas de changement structurel : les champs à collecter restent les mêmes qu'avant P3.

### 5. Impact sur la méthodologie du mémoire

**Ce que P3 rend possible :**
- Distinguer les données validées des données provisoires dans toutes les analyses — garantie d'intégrité méthodologique.
- Tracer les modifications post-soumission — permet d'identifier les erreurs de saisie systématiques.
- Calculer des indicateurs de qualité de la collecte (délai moyen soumission, taux de modification).

**Ce que P3 empêche ou limite :**
- Une équipe verrouillée ne peut plus être corrigée sans intervention admin. Toute erreur non détectée avant verrouillage restera dans la base — limite à mentionner dans le mémoire.

**Hypothèses confirmées :**
- H2 (pertes principalement organisationnelles) : le système peut désormais distinguer les arrêts non planifiés des maintenances planifiées, permettant de valider H2 sur données réelles.

**Hypothèses à nuancer :**
- L'hypothèse implicite d'une saisie quotidienne est maintenant une contrainte fonctionnelle : si l'agent ne soumet pas, les données ne seront jamais visibles dans les analyses.

### 6. Impact sur l'interprétation des résultats

Les dashboards et l'export Excel ne voient que les équipes soumises ou verrouillées. Le TRS calculé sera un TRS des équipes effectivement saisies et validées, pas un TRS exhaustif de toutes les équipes produites. Si certains postes ne sont jamais saisis, le TRS affiché sera biaisé. Cette limite doit apparaître dans la section "Limites de l'outil de collecte".

### 7. Ce qu'il faut probablement mettre à jour dans le mémoire

| Section | Mise à jour suggérée |
|---|---|
| Méthodologie — outil de collecte | Décrire le workflow comme mécanisme de contrôle qualité des données |
| Méthodologie — variables | Préciser que prix_snapshot est figé à la soumission, pas à la production |
| Limites | Ajouter : risque de biais si certains postes ne sont pas saisis ; données verrouillées non corrigeables |
| Fiche de collecte | Ajouter une étape de vérification finale avant soumission numérique |
| Définition des indicateurs | Préciser que TRS et pertes FCFA sont calculés uniquement sur les équipes soumises/verrouillées |

### 8. Distinction acquis / provisoire

**Acquis et stables :**
- Structure des trois statuts et leurs transitions
- Filtrage _STATUTS_ANALYSES dans tous les calculs
- Prix figés à la soumission (irréversible sauf modification chef)
- Verrouillage automatique à 3 jours

**Provisoires (dépendent d'une validation terrain) :**
- La valeur capacite_equipe_h = 1,5625 m³/h — à confirmer par chronométrage réel
- Les prix par essence — à renseigner avant le début de la collecte
- Le délai réaliste de soumission — à observer sur le terrain

**Décision à prendre :**
- Faut-il alerter l'agent si un brouillon n'est pas soumis dans les 24h ? (fonctionnalité non implémentée)

### 9. Texte réutilisable dans le mémoire

L'outil de pilotage développé dans le cadre de ce travail intègre un mécanisme de contrôle de la qualité des données reposant sur un cycle de vie en trois états. Chaque enregistrement d'équipe suit un parcours défini : il est d'abord créé en mode brouillon, état provisoire dans lequel les données restent modifiables par l'agent de saisie ; il est ensuite soumis par cet agent une fois les informations vérifiées, ce qui fige les prix au cours du marché à cette date et déclenche le calcul définitif du Taux de Rendement Synthétique ; il est enfin verrouillé, soit manuellement par le chef de production, soit automatiquement au terme d'un délai de soixante-douze heures, rendant les données immuables.

Ce mécanisme présente deux avantages méthodologiques. D'une part, il garantit que les tableaux de bord et les analyses financières ne s'appuient que sur des données validées, en excluant systématiquement les enregistrements à l'état brouillon. D'autre part, la traçabilité des modifications post-soumission, assurée par les champs modifié_par et modifié_le, permet d'identifier d'éventuelles corrections tardives et d'en évaluer la fréquence comme indicateur de qualité du processus de saisie.

Cette architecture implique cependant une dépendance organisationnelle : si un agent ne soumet pas ses données dans les délais, les équipes correspondantes n'apparaissent dans aucune analyse. Le taux de couverture de la collecte — défini comme le rapport entre le nombre d'équipes soumises et le nombre d'équipes réellement travaillées — constitue ainsi une limite à considérer dans l'interprétation des résultats.
