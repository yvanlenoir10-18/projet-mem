# Note d'impact mémoire — P26 : Skill run-cuf-pilotage (smoke driver)

> Générée le : 2026-05-28
> Commit : `c01f2b5` — feat(skill): run-cuf-pilotage — smoke driver + SKILL.md vérifié
> Branche : `claude/install-claude-excel-6MGzv`
> Fichiers : `cuf-pilotage/.claude/skills/run-cuf-pilotage/smoke.sh`, `…/SKILL.md`

---

## 1. Résumé de la fonctionnalité

Ajout d'un skill Claude Code (`/run-cuf-pilotage`) qui permet à n'importe quel agent ou développeur de lancer, piloter et vérifier l'app CUF Pilotage depuis un shell propre, sans connaissance préalable de l'application.

Le skill est composé de deux fichiers colocalisés dans `cuf-pilotage/.claude/skills/run-cuf-pilotage/` :

- **`smoke.sh`** : driver exécutable autonome. Lance Flask si le port 5000 est libre, teste 16 points de contrôle (4 rôles × routes clés + soumission de fiche + validation anti-chevauchement), retourne exit 0 ou exit 1. Vérifié dans ce container Linux — 16/16 OK.
- **`SKILL.md`** : documentation agent-first avec frontmatter auto-load. Couvre le chemin agent (`smoke.sh`), le chemin humain (`python run.py`), les comptes de test, les routes, les gotchas et le troubleshooting. Toutes les commandes ont été exécutées dans la session de génération.

---

## 2. Décision d'architecture — driver curl, pas Playwright

L'app est un serveur web Flask standard (pas un frontend JS lourd, pas d'Electron). Le driver naturel est `curl` + cookies de session. Playwright aurait été adapté pour tester des interactions JavaScript côté client (alertes temps réel, chevauchement JS) ; `curl` est suffisant pour vérifier les routes serveur et la logique métier POST.

**Cas d'usage du driver selon le type de PR :**
- PR touchant une route Flask (validation, calcul, DB) → `smoke.sh` suffit
- PR touchant du JavaScript inline (poka-yoke, chevauchement client-side) → tester manuellement dans le navigateur ou avec Playwright ; le smoke vérifie le comportement serveur correspondant

Le smoke teste le chevauchement côté **serveur** (HTTP 200 + flash danger) — qui est la garde de confiance — pas le chevauchement client-side (JS).

---

## 3. Lien avec les objectifs spécifiques du mémoire

| Objectif spécifique | Impact |
|---|---|
| OS6 — Outil de pilotage adapté | **Indirect (maintenabilité).** Le skill garantit que l'outil reste vérifiable à chaque session de développement, sans dépendance à la mémoire humaine des procédures de test. |

Ce skill n'a pas d'impact direct sur les OS métier (OS1–OS4) : c'est de l'infrastructure de développement.

---

## 4. Impact sur la validité scientifique des données

Aucun impact direct. Le smoke ne modifie pas les données — il crée des fiches de test en brouillon (statut `brouillon`, non soumises au chef, non incluses dans les calculs TRS). Ces fiches de test peuvent être nettoyées avec un DELETE admin si nécessaire.

---

## 5. Règle R7 — Aucune nouvelle table DB

Respectée. Aucune modification du modèle de données. Le smoke crée des fiches via les routes existantes — il n'interagit pas directement avec la DB.

---

## 6. Contradiction avec hypothèses précédentes

**Aucune contradiction avec H1–H4.** Ce commit est de l'infrastructure de test, sans effet sur les hypothèses de recherche.

---

## 7. Nouvelles fonctions clés introduites

| Élément | Fichier | Rôle |
|---|---|---|
| `smoke.sh` | `.claude/skills/run-cuf-pilotage/smoke.sh` | Driver autonome : start serveur + 16 checks + exit 0/1 |
| `SKILL.md` | `.claude/skills/run-cuf-pilotage/SKILL.md` | Documentation agent : frontmatter auto-load, commandes vérifiées |

---

## 8. Utilisabilité terrain et adoption

- **Avant le skill :** un agent ou développeur reprenant le projet devait lire le README (inexistant ou générique), deviner les comptes de test, découvrir les noms de champs POST par inspection du code source.
- **Après le skill :** `bash .claude/skills/run-cuf-pilotage/smoke.sh` donne une réponse binaire en < 10 secondes. Les comptes, les routes, les gotchas et les commandes curl sont documentés avec des valeurs exactes vérifiées.

---

## 9. Ce que cela change pour le mémoire

Aucun impact sur le contenu rédactionnel du mémoire. Ce skill est un outil de développement interne.

En revanche, il garantit la **reproductibilité des démonstrations** : avant une présentation terrain ou une session de collecte, `bash smoke.sh` confirme en 10 secondes que l'app est opérationnelle sur 16 points critiques. C'est une garantie de fiabilité du prototype pour OS6.

---

> **Vérification réalisée :** `bash smoke.sh --keep-running` exécuté deux fois dans la session — 16/16 checks OK, exit 0. Toutes les commandes curl de `SKILL.md` ont été exécutées manuellement avant rédaction.
