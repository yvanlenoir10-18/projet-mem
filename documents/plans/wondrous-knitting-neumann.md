# Cadrage complet — Application de pilotage Chaîne 4, Scierie CUF Ebolowa
> Statut : FINALISÉ — Prêt pour implémentation
> Mis à jour : 2026-04-11

---

## DÉCISIONS VALIDÉES

| Paramètre | Décision |
|---|---|
| Périmètre | Chaîne 4 uniquement |
| Usage principal | Mémoire Master 2 + portfolio stage |
| Saisie | Agent administratif en bureau, après chaque poste de 8h |
| Connectivité | Internet stable → application web hébergeable |
| Durée d'un poste | 8 heures = 480 minutes d'ouverture théorique |
| Stock grumes | Tracé en entrée/sortie (traçabilité interne CUF existante) |
| Commandes clients | Hors périmètre Version 1 |
| Prix de vente | Disponibles — saisie paramétrable par essence dans l'app |
| Données historiques | Registre arrêts existant + bilans partiels → saisie historique au démarrage |

---

## 1. REFORMULATION DU BESOIN

### Le vrai problème métier
La Chaîne 4 de CUF produit entre 10 et 20 m³ par poste alors que l'objectif affiché est de 25 m³. Cet écart de 25 à 60 % n'a jamais été mesuré ni analysé. Personne ne sait précisément combien de temps les machines s'arrêtent, pourquoi elles s'arrêtent, ni quel est le coût réel de ces pertes en FCFA. L'application doit transformer les données brutes du terrain (registre des arrêts, bilans de production) en informations directement exploitables pour améliorer la performance de la chaîne.

### Valeur pour le chef scierie
Répondre chaque matin à : "Qu'est-ce qui s'est passé hier, quelle machine a le plus perturbé la production, et quelle est la cause principale ?" — avec des faits chiffrés, pas des impressions.

### Valeur pour le PDG
Répondre chaque mois à : "Combien avons-nous produit, quelle est la perte financière en FCFA, et quelle action corrective donne le meilleur retour ?" — en évitant tout jargon technique forestier.

---

## 2. ANALYSE MÉTIER — FLUX DE LA CHAÎNE 4

```
[Parc à grumes]
    ↓ essence + volume entrée
[Scie de tête] ──────── arrêts possibles (panne, affûtage, attente)
    ↓ plateaux bruts
[BICOUPE] ◄─────────── GOULOT — 100% du bois passe ici
    ↓ planches conformes           ↓ planches défectueuses
[Triage direct]            [Déligneuse → Ébouteuse → Dédoubleuse]
    ↓                                        ↓
[Triage final + Empilage] ←─────────────────┘
    ↓
[MESURE OFFICIELLE : m³ produits par poste]
```

### Points de contrôle critiques
- **Entrée** : essence + volume grume au démarrage du poste
- **Bicoupe** : chaque arrêt (heure début, heure fin, cause)
- **Sortie** : volume total scié + volume rebut + catégorie planches

### Principales causes de perte identifiées (hypothèse H2)
1. Arrêts non planifiés bicoupe (panne, affûtage de lame)
2. Attente approvisionnement (parc à grumes vide ou mal organisé)
3. Défauts de qualité en entrée (grumes mal sélectionnées)
4. Temps de changement d'essence (réglage machine)
5. Absentéisme opérateur / transition de poste mal gérée

---

## 3. DÉCISIONS À SOUTENIR PAR L'APPLICATION

### Décisions opérationnelles quotidiennes (chef de poste)
- Quelle machine a causé le plus d'arrêts hier ?
- Quelle est la cause d'arrêt la plus fréquente cette semaine ?
- Le volume produit ce poste est-il dans la norme ou en dessous ?

### Décisions de pilotage hebdomadaire (chef scierie)
- Quelle essence produit le meilleur rendement matière ?
- Quel poste (matin/après-midi) est le moins performant ?
- Quel est le TRS moyen de la semaine vs objectif ?

### Décisions stratégiques mensuelles (PDG)
- Combien de m³ avons-nous perdus ce mois à cause des arrêts ?
- Quel est le manque à gagner en FCFA ?
- Quelle action corrective prioritaire aura le plus grand impact ?

---

## 4. PROFILS UTILISATEURS

### Agent de saisie (administratif)
- **Voit** : formulaire de saisie d'un poste
- **Fait** : saisit production + arrêts + qualité après chaque poste
- **Décide** : rien — rôle de collecte uniquement
- **Niveau de détail** : formulaire guidé, listes déroulantes, pas de calcul manuel

### Chef scierie
- **Voit** : TRS du jour/semaine, Pareto des causes d'arrêt, volumes par essence, comparaison postes
- **Fait** : analyse les tendances, identifie les problèmes récurrents
- **Décide** : actions correctives opérationnelles (maintenance préventive, réorganisation)
- **Niveau de détail** : graphiques + tableaux avec filtres par date/essence/machine

### PDG
- **Voit** : production du mois vs objectif, pertes en FCFA, top 3 causes, TRS synthétique
- **Fait** : lit le dashboard en moins de 2 minutes
- **Décide** : investissements, priorités, objectifs
- **Niveau de détail** : 5 chiffres clés maximum, couleurs traffic light (vert/orange/rouge)

### Chef de poste *(optionnel V1)*
- **Voit** : résumé du poste en cours
- **Fait** : valide le récapitulatif de fin de poste
- **Décide** : signale un problème non saisi

---

## 5. KPI PRIORITAIRES

### Temps réel / par poste
| KPI | Définition | Utilisateur | Décision aidée | V1 ? |
|---|---|---|---|---|
| Volume produit (m³) | Total m³ scié ce poste | Chef poste, chef scierie | Comparer à l'objectif 25 m³ | ✅ Oui |
| Durée totale arrêts (min) | Somme des arrêts bicoupe | Chef scierie | Identifier les postes problématiques | ✅ Oui |
| TRS du poste (%) | D × P × Q calculé auto | Chef scierie | Performance globale | ✅ Oui |
| Taux de rebut (%) | m³ rebut / m³ scié × 100 | Chef scierie | Qualité de la matière première | ✅ Oui |

### Journalier
| KPI | Définition | Utilisateur | Décision aidée | V1 ? |
|---|---|---|---|---|
| Production jour (m³) | Somme des 2 postes | PDG, chef scierie | Vision quotidienne | ✅ Oui |
| TRS journalier (%) | Moyenne pondérée des postes | Chef scierie | Tendance | ✅ Oui |
| Cause d'arrêt dominante | Cause la plus fréquente du jour | Chef scierie | Action immédiate | ✅ Oui |
| Disponibilité bicoupe (%) | (480 - arrêts) / 480 | Chef scierie | État mécanique | ✅ Oui |

### Hebdomadaire
| KPI | Définition | Utilisateur | Décision aidée | V1 ? |
|---|---|---|---|---|
| TRS semaine (%) | Moyenne 14 postes | Chef scierie, PDG | Pilotage semaine | ✅ Oui |
| Pareto arrêts (top 5) | 80% des pertes viennent de X causes | Chef scierie | Prioriser maintenance | ✅ Oui |
| Rendement par essence (%) | m³ scié / m³ entrée par essence | Chef scierie | Planification appro | ✅ Oui |
| Comparaison postes matin/après-midi | TRS matin vs après-midi | Chef scierie | Problème équipe | ✅ Oui |

### Mensuel
| KPI | Définition | Utilisateur | Décision aidée | V1 ? |
|---|---|---|---|---|
| Production mensuelle (m³) | Total du mois | PDG | Objectif mensuel | ✅ Oui |
| Pertes financières (FCFA) | m³ perdus × prix/m³ par essence | PDG | Impact économique | ✅ Oui |
| Évolution TRS mois/mois | % de progression | PDG | Tendance stratégique | ✅ Oui |
| Simulation corrective | Gain si cause X éliminée | PDG, chef scierie | ROI action | 🔜 V2 |

---

## 6. DONNÉES À COLLECTER

### Bloc A — En-tête du poste (1 fois par poste)
| Donnée | Utilité | Qui saisit | Manuel/Auto |
|---|---|---|---|
| Date | Historique | Agent saisie | Manuel |
| N° poste (Matin / Après-midi) | Comparaison postes | Agent saisie | Manuel (liste) |
| Essence(s) traitée(s) | Rendement par essence | Agent saisie | Manuel (liste) |
| Volume grumes en entrée (m³) | Rendement matière | Agent saisie | Manuel → auto plus tard |
| Effectif présent | Corrélation absentéisme/TRS | Agent saisie | Manuel |

### Bloc B — Production (fin de poste)
| Donnée | Utilité | Qui saisit | Manuel/Auto |
|---|---|---|---|
| Volume total scié (m³) | KPI central | Agent saisie | Manuel (mesure empilage) |
| Volume rebut (m³) | Taux de rebut | Agent saisie | Manuel |
| Nb planches conformes | Qualité | Agent saisie | Manuel |
| Nb planches défectueuses | Qualité | Agent saisie | Manuel |

### Bloc C — Arrêts machine (0 à N arrêts par poste)
| Donnée | Utilité | Qui saisit | Manuel/Auto |
|---|---|---|---|
| Machine concernée | Identifier le goulot | Agent saisie | Manuel (liste) |
| Heure début arrêt | Durée précise | Agent saisie | Manuel |
| Heure fin arrêt | Durée précise | Agent saisie | Manuel |
| Durée (min) | **Calculée automatiquement** | App | Auto |
| Cause de l'arrêt | Pareto + Ishikawa | Agent saisie | Manuel (liste + champ libre) |
| Catégorie de cause | Analyse causes racines | App | Auto (déduite de la cause) |

### Catégories de causes standardisées
- **Mécanique** : panne, casse lame, usure
- **Organisationnelle** : attente opérateur, transition poste, consigne
- **Approvisionnement** : parc à grumes vide, grume inadaptée
- **Qualité matière** : grume trop dure, nœuds, défaut bois
- **Maintenance planifiée** : affûtage lame, graissage, réglage
- **Autre / Inconnu**

### Bloc D — Paramètres (saisie unique, modifiables)
| Donnée | Utilité | Qui saisit |
|---|---|---|
| Prix vente m³ Ayous (FCFA) | Calcul pertes financières | Admin |
| Prix vente m³ Azobé (FCFA) | Calcul pertes financières | Admin |
| Prix vente m³ Iroko (FCFA) | Calcul pertes financières | Admin |
| Prix vente m³ Movingui (FCFA) | Calcul pertes financières | Admin |
| Objectif production par poste (m³) | Comparaison | Admin |
| Durée poste (min) | Base calcul TRS | Admin |
| Capacité théorique bicoupe (m³/h) | Performance théorique | Admin |

---

## 7. CALCUL TRS — FORMULES

```
TRS = Disponibilité × Performance × Qualité

Disponibilité (D) = (480 - ∑ durées_arrêts) / 480

Performance (P) = Volume_scié_réel / Volume_scié_théorique
  où Volume_scié_théorique = capacité_bicoupe × (480 - ∑ arrêts) / 60

Qualité (Q) = Volume_conforme / Volume_scié_total
  où Volume_conforme = Volume_total - Volume_rebut

Pertes financières (FCFA) = (Objectif_m³ - Produit_réel_m³) × Prix_m³_essence
```

---

## 8. FONCTIONNALITÉS

### Version 1 — À construire en priorité
| Fonctionnalité | Justification |
|---|---|
| Authentification 3 rôles (admin, chef, PDG) | Sécurité minimale, vues différenciées |
| Formulaire de saisie d'un poste | C'est la porte d'entrée de toutes les données |
| Calcul TRS automatique | Cœur du mémoire, valeur immédiate |
| Vue PDG : 5 KPI + traffic light | Le PDG doit comprendre en 30 secondes |
| Vue chef scierie : graphiques + Pareto | Décisions opérationnelles quotidiennes |
| Historique des postes (liste + filtres) | Permet de retrouver et corriger les saisies |
| Gestion des paramètres (prix, objectifs) | Rend l'app adaptable à toute scierie |
| Export rapport PDF ou CSV | Livrable pour le mémoire et pour CUF |

### Version 2 — Après validation terrain
| Fonctionnalité | Justification |
|---|---|
| Simulation corrective (ROI) | Nécessite 1-2 mois de données pour être crédible |
| Suivi stock grumes intégré | Import depuis traçabilité CUF existante |
| Gestion commandes clients | Nouveau domaine métier, hors production |
| Analyse Ishikawa interactive | Visualisation avancée des causes racines |
| Import données historiques (CSV) | Récupérer le registre arrêts existant |
| Notifications / alertes seuil | Nécessite infrastructure supplémentaire |

---

## 9. ÉCRANS DE L'APPLICATION

### Écran 1 — Vue PDG *(priorité maximale)*
- **Objectif** : lecture de la performance en moins de 2 minutes
- **Informations** : TRS du mois (% + couleur), production réelle vs objectif (m³), pertes en FCFA, top 3 causes d'arrêt, tendance mois/mois
- **Actions** : choisir le mois, voir le détail d'une cause
- **Utilisateur** : PDG

### Écran 2 — Tableau de bord chef scierie *(priorité haute)*
- **Objectif** : pilotage quotidien et hebdomadaire
- **Informations** : TRS semaine + courbe 30 jours, Pareto des arrêts (graphique barres), volumes par essence (graphique), comparaison postes matin/après-midi, derniers 7 postes en tableau
- **Actions** : filtrer par période, par essence, par machine
- **Utilisateur** : chef scierie

### Écran 3 — Saisie d'un poste *(priorité maximale)*
- **Objectif** : collecter toutes les données d'un poste en 5 minutes
- **Informations** : formulaire en 3 blocs (en-tête / production / arrêts)
- **Actions** : ajouter autant d'arrêts que nécessaire, sauvegarder, modifier
- **Utilisateur** : agent de saisie

### Écran 4 — Analyse des arrêts *(priorité haute)*
- **Objectif** : identifier les causes racines des pertes
- **Informations** : tableau de tous les arrêts, graphique Pareto, durée totale par cause, filtre par machine/période/essence
- **Actions** : filtrer, trier, exporter
- **Utilisateur** : chef scierie

### Écran 5 — Historique des postes *(priorité moyenne)*
- **Objectif** : accès et correction des données saisies
- **Informations** : liste des postes avec date, essence, volume, TRS, nb arrêts
- **Actions** : voir le détail, modifier, supprimer
- **Utilisateur** : agent de saisie, chef scierie

### Écran 6 — Paramètres *(priorité basse mais nécessaire)*
- **Objectif** : configurer l'application pour CUF ou une autre scierie
- **Informations** : prix par essence, objectif m³/poste, durée poste, capacité théorique bicoupe
- **Actions** : modifier les valeurs, sauvegarder
- **Utilisateur** : admin

### Écran 7 — Rapport export *(priorité moyenne)*
- **Objectif** : générer un rapport PDF ou CSV pour le mémoire et la direction
- **Informations** : rapport mensuel avec tous les KPI, graphiques, analyse Pareto
- **Actions** : choisir la période, télécharger
- **Utilisateur** : chef scierie, PDG

---

## 10. RISQUES ET ERREURS À ÉVITER

| Risque | Symptôme | Comment l'éviter |
|---|---|---|
| Scope creep | "Et si on ajoutait les commandes ?" | Référencer ce document avant chaque nouvelle feature |
| Saisie abandonnée | Formulaire trop long → arrêt d'utilisation | Max 3 minutes par poste, listes déroulantes obligatoires |
| KPI incompréhensibles pour le PDG | "TRS ? C'est quoi ça ?" | Toujours afficher en FCFA + % côte à côte |
| Données non fiables | Saisies incohérentes (m³ rebut > m³ scié) | Validation côté serveur sur chaque champ |
| Outil abandonné après le stage | Personne ne sait maintenir | Stack simple (Flask + SQLite), code commenté en français |
| Trop d'indicateurs | Dashboard illisible | Max 5 KPI par écran, les autres en "voir détail" |

---

## 11. ARCHITECTURE TECHNIQUE — VERSION 1

### Stack choisie
| Couche | Technologie | Raison |
|---|---|---|
| Langage | Python 3.11 | Déjà présent dans le projet, simple, lisible |
| Framework web | Flask 3.x | Léger, pédagogique, rapide à démarrer |
| ORM | SQLAlchemy + Flask-SQLAlchemy | Abstraction DB, migrations simples |
| Base de données | SQLite (dev) → PostgreSQL (prod) | Zéro configuration pour démarrer |
| Frontend | HTML5 + Bootstrap 5 + Jinja2 | Pas de build JS, templates lisibles, responsive |
| Graphiques | Chart.js 4 (CDN) | Léger, no-build, documentation excellente |
| Auth | Flask-Login + bcrypt | Session-based, suffisant pour 4 rôles |
| Export | WeasyPrint (PDF) ou openpyxl (Excel) | PDF pour rapports, Excel pour données brutes |
| Déploiement | PythonAnywhere ou Railway (free tier) | Connexion stable confirmée, 0€/mois |

### Structure des fichiers
```
cuf-pilotage/
├── app/
│   ├── __init__.py          # Factory Flask + extensions
│   ├── models.py            # Poste, Arret, Parametre, User
│   ├── routes/
│   │   ├── auth.py          # Login / logout
│   │   ├── saisie.py        # Formulaire poste
│   │   ├── dashboard.py     # Vues PDG + chef scierie
│   │   ├── analyse.py       # Pareto + historique
│   │   └── admin.py         # Paramètres
│   ├── services/
│   │   ├── trs.py           # Calcul TRS = D × P × Q
│   │   ├── pareto.py        # Calcul Pareto arrêts
│   │   └── export.py        # Génération PDF/Excel
│   └── templates/
│       ├── base.html        # Layout Bootstrap 5
│       ├── pdg/             # Vue PDG
│       ├── chef/            # Vue chef scierie
│       ├── saisie/          # Formulaires
│       └── admin/           # Paramètres
├── static/
│   ├── css/custom.css
│   └── js/charts.js         # Initialisation Chart.js
├── instance/
│   └── cuf.db               # SQLite (gitignorée)
├── config.py                # Variables d'environnement
├── requirements.txt
└── run.py                   # Point d'entrée
```

### Modèle de données
```sql
User        (id, nom, email, password_hash, role)
Parametre   (id, cle, valeur, description)
Poste       (id, date, numero_poste, essence, volume_entree, 
             volume_sorti, volume_rebut, nb_conformes, 
             nb_defectueux, effectif, user_id)
Arret       (id, poste_id, machine, heure_debut, heure_fin, 
             duree_min[calculée], cause, categorie, notes)
```

---

## 12. ROADMAP — ORDRE DE RÉALISATION

### Phase 1 — Fondations (Semaine 1-2)
1. Créer la structure Flask + modèles SQLAlchemy
2. Mettre en place l'authentification 3 rôles
3. Construire le formulaire de saisie d'un poste (avec arrêts dynamiques)
4. Implémenter le calcul TRS automatique

### Phase 2 — Visualisation (Semaine 3-4)
5. Vue chef scierie : TRS semaine + Pareto arrêts (Chart.js)
6. Vue PDG : 5 KPI + traffic light + pertes FCFA
7. Historique des postes avec filtres

### Phase 3 — Finitions (Semaine 5-6)
8. Écran paramètres (prix essences, objectifs)
9. Export rapport PDF ou Excel
10. Tests avec données réelles du terrain
11. Déploiement sur PythonAnywhere

### Phase 4 — Version 2 (post-stage)
12. Import données historiques (registre arrêts CUF)
13. Simulation corrective avec projection ROI
14. Suivi stock grumes
15. Gestion commandes clients

---

## 13. RÉSUMÉ EXÉCUTIF

**Projet** : Application web de pilotage de la Chaîne 4, Scierie CUF Ebolowa
**Objectif métier** : Transformer les données de production brutes en leviers d'amélioration du TRS
**Stack** : Python + Flask + SQLite + Bootstrap 5 + Chart.js
**Périmètre V1** : Saisie postes → Calcul TRS automatique → 3 vues (PDG / Chef scierie / Admin)
**Données clés** : Arrêts machine (durée + cause), volumes sciés, rebuts, essences
**Indicateur central** : TRS = Disponibilité × Performance × Qualité (cible : passer de <60% vers 75%+)
**Déploiement** : Web hébergé (PythonAnywhere), accessible sur site CUF
**Prêt à coder** : ✅ OUI — Ce document est le contrat de conception

---

*Questions encore ouvertes à clarifier sur le terrain :*
- Capacité théorique exacte de la bicoupe (fiche constructeur, m³/heure par essence)
- Durée officielle des pauses incluses dans les 8h de poste
- Format exact du registre arrêts existant (pour import historique V2)
