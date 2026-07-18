# Note d'impact mémoire — P22 : Bugfix rôle opérateur DB + compte admin manquant

> Générée le : 2026-05-27
> Commit : `d3bb834` — fix(db): répare le rôle opérateur et ajoute le compte admin manquant
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `app/__init__.py`

---

## 1. Résumé de la fonctionnalité

Correction d'un bug de données critiques introduit lors du seeding initial de la base : le compte `Agent Saisie` (`saisie@cuf.cm`), destiné au rôle `operateur`, avait été créé avec `role='admin'`. La fonction `_init_donnees_defaut()` ne corrige pas les données existantes (sa garde `if not User.query.first()` empêche toute ré-exécution), si bien que ce rôle erroné persistait à chaque redémarrage.

Conséquences directes du bug :
- Aucun utilisateur avec `role='operateur'` n'existait en base.
- Le profil opérateur (accueil, formulaire, historique, widget de progression) était entièrement inaccessible — non pas via une erreur 500, mais de façon silencieuse : l'utilisateur `saisie@cuf.cm` obtenait la vue admin sans s'en rendre compte.
- `_stats_operateur()` n'était jamais appelé (conditionné à `current_user.role == 'operateur'`), rendant le composant de progression inopérant même après le bugfix P21.
- Le compte `Administrateur` (`admin@cuf.cm`) était absent de la base.

**Correction :** ajout d'une fonction `_repair_seed_roles()` appelée au démarrage, après `_init_donnees_defaut()`. Elle corrige le rôle de `saisie@cuf.cm` → `'operateur'` si nécessaire, et crée `admin@cuf.cm` s'il est absent.

---

## 2. Décision d'architecture — migration légère au démarrage

Le pattern `_repair_seed_roles()` suit la même logique que `_ensure_schema()` (ajout de colonnes manquantes) déjà présente dans `__init__.py` : une fonction de réparation idempotente appelée à chaque démarrage, qui ne fait rien si les données sont déjà correctes.

**Pourquoi pas une migration Alembic ?** L'application utilise SQLite en développement terrain, sans outillage de migration. Le mécanisme `_ensure_schema()` est le pattern établi pour ce projet. `_repair_seed_roles()` est cohérent avec lui.

**Idempotence garantie :** chaque bloc vérifie l'état avant d'écrire (`if saisie and saisie.role != 'operateur'`, `if not User.query.filter_by(email='admin@cuf.cm').first()`). Un redémarrage sur une base déjà correcte ne produit aucun effet.

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS2 — Mesurer la production réelle via collecte terrain | **Direct (stabilité critique).** Aucune donnée ne peut être saisie si le profil opérateur est inaccessible. Ce bug bloquait entièrement OS2. |
| OS6 — Outil de pilotage adapté, vue opérateur | **Direct.** La vue opérateur (accueil, progression F1/F6/F6b, formulaire) requiert explicitement `role='operateur'`. Sans ce rôle, la vue est inaccessible. |

---

## 4. Impact sur la validité scientifique des données

Ce bugfix est une condition préalable à toute collecte. Tant que `saisie@cuf.cm` avait le rôle `'admin'`, le protocole de collecte de données du mémoire (OS2) ne pouvait pas être exécuté depuis ce compte. La correction est donc une exigence de validité, pas une amélioration fonctionnelle.

Aucune formule TRS, aucune règle de calcul, aucune donnée existante n'est modifiée. Le fix ne touche qu'à la valeur du champ `role` d'un enregistrement `User`.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. `_repair_seed_roles()` ne crée aucune table. Elle modifie un champ d'un enregistrement existant et ajoute au plus un enregistrement `User`. Le schéma reste identique.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.** Ce commit est une correction de déploiement, sans rapport avec les hypothèses de recherche.

**Point à signaler — cohérence avec P21 :** P21 avait documenté que la cause du crash était un désalignement de versions entre `saisie.py` et `_progression.html`. C'était exact, mais incomplet : même après P21, le profil opérateur restait inaccessible parce qu'aucun utilisateur n'avait le rôle `'operateur'`. P22 est donc le complément indispensable de P21 pour rendre le profil opérateur réellement fonctionnel. Les deux bugfixes sont nécessaires simultanément.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| `_repair_seed_roles()` | `app/__init__.py` | Migration légère au démarrage : corrige `saisie@cuf.cm` → `role='operateur'`, crée `admin@cuf.cm` si absent. |
| Appel dans `create_app()` | `app/__init__.py` | `_repair_seed_roles()` est appelée après `_init_donnees_defaut()` et avant `_seed_donnees_demo()`. |

---

## 8. Utilisabilité terrain et adoption

- **Avant le fix :** connexion en tant que `saisie@cuf.cm` donnait accès à la vue admin — les menus, routes et indicateurs de l'opérateur n'étaient jamais affichés. Un opérateur CUF ne pouvait pas saisir ses fiches depuis ce compte, et aucune erreur explicite ne signalait le problème.
- **Après le fix :** `saisie@cuf.cm` ouvre le profil opérateur (accueil, formulaire, historique, progression) comme prévu. `admin@cuf.cm` donne accès aux fonctions d'administration.
- La correction est transparente pour l'utilisateur : aucune action requise, le redémarrage de l'application suffit.

---

## 9. Ce que cela change pour le mémoire

Ce bugfix ne modifie pas le contenu académique du mémoire, mais il était un prérequis bloquant pour la collecte terrain (OS2). Sans lui, aucune démonstration du profil opérateur ni aucune donnée saisie via ce compte ne pouvait être réalisée.

Pour le rapport, il peut être mentionné en note de bas de page dans la section OS6 (outil de pilotage) comme exemple de problème de déploiement rencontré et résolu — illustrant la nécessité de tester le prototype sur la base de données réelle de l'environnement cible, pas uniquement en environnement de développement frais.

---

> **Vérification réalisée :** `python -c "from app import create_app; app = create_app(); print('OK')"` → OK. Après redémarrage : `User.query.all()` retourne 4 comptes — `Agent Saisie (operateur)`, `Chef Scierie (chef)`, `Directeur (pdg)`, `Administrateur (admin)`. `User.query.filter_by(role='operateur').first()` → `<User Agent Saisie (operateur)>`. `_stats_operateur(op.id)` retourne un dict complet avec `nb_equipes=60`. Template `_progression.html` rendu en isolation avec un dict complet : progression, record, barre hebdomadaire — tous corrects.
