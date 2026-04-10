# Plan — Application de pilotage scierie CUF
> Fichier de cadrage produit, métier et technique
> Créé : 2026-04-10 | Statut : Phase 1 — Questions en cours

---

## 1. REFORMULATION DU BESOIN

### Ce qui est demandé
Créer une application web de type tableau de bord pour piloter les opérations d'une scierie industrielle, avec trois niveaux de lecture distincts : opérationnel (chef de poste), production (chef scierie), et stratégique (PDG).

### Le vrai problème métier
La scierie CUF d'Ebolowa fonctionne sans aucun outil de mesure. L'objectif de production (25 m³/poste) a été fixé empiriquement, sans base technique. La production réelle (10 à 20 m³/poste) accuse un écart pouvant dépasser 60 %, mais cet écart n'a jamais été mesuré ni analysé. En l'absence de données structurées, personne ne peut identifier où se situent les pertes ni prendre des décisions correctives sur des bases solides.

**Le problème n'est pas l'absence de tableau de bord — c'est l'absence de données fiables et d'un cadre de mesure.**
L'application doit donc résoudre d'abord le problème de collecte, puis le problème de visualisation.

### Valeur pour le chef scierie
Répondre chaque matin à une question simple : "Qu'est-ce qui s'est passé hier, pourquoi, et qu'est-ce que je dois faire différemment aujourd'hui ?" L'outil lui donne les faits (temps d'arrêt, volumes, causes) pour agir, pas seulement pour constater.

### Valeur pour le PDG
Répondre à une question mensuelle : "Combien avons-nous produit, quel est l'impact financier de nos pertes, et quel est le retour sur investissement si on améliore telle ou telle chose ?" Le PDG n'a pas de formation forestière — l'outil doit parler en FCFA et en tendances, pas en m³/heure ou en TRS.

---

## 2. CONTEXTE MÉTIER CONNU (CUF — Chaîne 4)

### Flux de production documenté
```
Parc à grumes
    → Scie de tête (plateaux bruts)
        → Bicoupe ← GOULOT UNIQUE (100% du bois passe ici)
            ↓ Bonnes planches → Triage direct
            ↓ Planches défectueuses → Déligneuse → Ébouteuse → Dédoubleuse → Triage
                → Triage final
                    → Empilage (mesure officielle en m³)
```

### Données de cadrage connues
| Paramètre | Valeur connue |
|---|---|
| Essences traitées | Ayous, Azobé, Iroko, Movingui |
| Régime | 2 postes continus |
| Effectif par poste | ~10 opérateurs |
| Objectif affiché | 25 m³/poste (empirique, sans base technique) |
| Production réelle | 10 à 20 m³/poste |
| TRS estimé (H3) | < 60 % |
| Machine goulot | Bicoupe (100% du bois) |
| Rendement matière Afrique centrale | 30-36% (benchmark Karsenty 2021) |
| Rendement international | 60%+ |

### Hypothèses de recherche validées (Dr Manga)
- **H1** : La capacité théorique réelle est inférieure à 25 m³/poste
- **H2** : Les pertes sont principalement d'origine organisationnelle/opérationnelle
- **H3** : TRS réel < 60%
- **H4** : Actions correctives sans investissement majeur = gain significatif de TRS

---

## 3. HYPOTHÈSES À VALIDER AVANT DE CONCEVOIR

Les hypothèses suivantes ont été formulées en l'absence de réponses explicites. Elles conditionnent les choix d'architecture et de périmètre.

| # | Hypothèse | Impact si fausse |
|---|---|---|
| A | L'app couvre uniquement la Chaîne 4 (pas les 4 chaînes) | Multiplier la complexité × 4 |
| B | L'usage est d'abord académique (mémoire + CV), pas opérationnel permanent | Priorités inversées : UX terrain > UX démo |
| C | La saisie se fait après le poste, pas en temps réel | Architecture offline / temps réel change tout |
| D | Il n'y a pas de connexion internet fiable sur site | App web hébergée devient impossible sans VPN ou mode offline |
| E | La gestion des commandes clients est hors périmètre MVP | Ajouter commandes = +30% de complexité |
| F | Il n'y a pas d'IT chez CUF pour maintenir l'application | Stack doit être autonome, simple à déployer localement |
| G | La durée officielle du poste est de 8 heures (pauses incluses) | Change le calcul de disponibilité dans le TRS |

---

## 4. QUESTIONS EN ATTENTE DE RÉPONSE (Round 1)

*À remplir après les réponses de l'utilisateur*

---

## 5. ANALYSE PRÉLIMINAIRE — CE QU'ON NE FERA PAS DANS LE MVP

Ces éléments sont séduisants mais dangereux pour un MVP :

- **Temps réel machine** : nécessite des capteurs IoT — hors budget stage
- **Gestion commandes/livraisons** : domaine ERP — hors périmètre production
- **Toutes les chaînes** : la Chaîne 4 seule justifie un mémoire complet
- **Application mobile native** : React Native ou Flutter = 3× plus de temps
- **IA prédictive** : sans 6 mois de données historiques, inutile
- **Authentification multi-rôles complexe** : suffit d'un login simple par profil

---

## 6. DÉCISIONS TECHNIQUES PRÉLIMINAIRES (à confirmer)

### Stack recommandée (hypothèse B : usage académique + démonstration)
| Couche | Choix | Raison |
|---|---|---|
| Backend | Python + Flask | Simple, rapide, connu du projet existant |
| Base de données | SQLite → PostgreSQL | SQLite pour démarrer sans infrastructure |
| Frontend | HTML + Bootstrap 5 + Chart.js | Pas de framework JS lourd, lisible, maintenable |
| Auth | Flask-Login + session | Suffisant pour 3-4 utilisateurs internes |
| Graphiques | Chart.js | Léger, no-build, intégré en HTML |
| Déploiement | Localhost / Raspberry Pi | Pas de cloud si pas de connexion fiable |

### Alternative si usage opérationnel réel (hypothèse B fausse)
| Couche | Choix | Raison |
|---|---|---|
| Backend | FastAPI | Plus performant, API REST propre |
| Frontend | React + Vite | Meilleure UX, composants réutilisables |
| Base de données | PostgreSQL | Robustesse, multi-connexions |
| Déploiement | VPS OVH/Hetzner (~5€/mois) | Accessible depuis n'importe quel appareil |

---

## 7. PROCHAINES ÉTAPES (après Round 1 de questions)

- [ ] Valider ou corriger les 7 hypothèses
- [ ] Confirmer le périmètre exact (Chaîne 4 seule ?)
- [ ] Clarifier le mode de saisie terrain
- [ ] Définir la contrainte de connectivité
- [ ] Construire la liste complète des KPI prioritaires
- [ ] Concevoir les 8 écrans avec maquettes textuelles
- [ ] Écrire le MVP complet avec roadmap
- [ ] Transmettre à Claude Code pour implémentation

---

*Prochaine mise à jour : après Round 1 de questions utilisateur*
