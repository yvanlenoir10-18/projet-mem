# Note d'impact — Remplacement des workflows GitHub Actions

> Commit : c542c4d
> Date : 2026-04-30
> Type : Infrastructure / CI/CD (pas une fonctionnalité applicative)

---

## Nature du commit

Remplacement des 5 workflows Node.js hérités du template de repo par un seul workflow Python minimaliste (`python-ci.yml`).

**Workflows supprimés :**
- `ci.yml`
- `pr-checks.yml`
- `security-scan.yml`
- `deploy-staging.yml`
- `release.yml`

**Workflow créé :**
- `python-ci.yml` — vérification de la syntaxe Python uniquement

## Raison du changement

Tous les workflows supprimés échouaient systématiquement sur `npm ci` car le projet est une application Flask/Python/SQLite, pas une application Node.js. Ces échecs ne reflétaient aucun problème réel du code — ils étaient purement un artefact du template utilisé lors de l'initialisation du repository.

## Impact sur le mémoire

**Aucun.** Ce changement est une correction administrative : il élimine les faux négatifs dans les vérifications CI et réduit le bruit dans les notifications GitHub Actions.

## Impact sur l'application

**Aucun.** L'application CUF Pilotage continue à fonctionner identiquement. Le workflow Python créé n'ajoute aucune nouvelle contrainte — il vérifie simplement que les fichiers `.py` sont syntaxiquement valides.

## Pas de contradiction avec les hypothèses

Ce commit n'introduit aucune décision de conception ni aucune modification au modèle de données ou aux indicateurs métier.

## Prochaine note attendue

La prochaine note incrémentale sera produite lors du commit de la Phase P4 (Export Excel enrichi) ou d'une autre fonctionnalité applicative.
