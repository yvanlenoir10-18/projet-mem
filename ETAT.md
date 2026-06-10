# ETAT.md — État vivant du projet

> **Rôle** : fichier d'état persistant entre les sessions Claude. L'agent oublie, le dépôt non.
> **Protocole** : lu en DÉBUT de chaque session (avec CLAUDE.md) · mis à jour en FIN de chaque session de travail.
> Les sections « Leçons apprises » et « Soutenance » sont *append-only* (on ajoute, on ne supprime pas).
> Ce fichier est un **résumé vivant** — le détail historique vit dans `documents/notes-impact/` (73+ notes).

---

## Dernière session — 2026-06-10

- **Données simulées purgées** : 62 fiches de production + 109 arrêts supprimés de la base dev (`instance/woodpilot.db`). Comptes (4) et paramètres (27) conservés. L'utilisateur saisira ses **vraies données terrain** lui-même.
- Smoke test : **20/20 verts** après purge (l'app gère la base vide sans erreur).
- Décision de méthode : adoption du pattern « fichier d'état » (ce fichier), vérificateur séparé pour les formules critiques (à activer en P4), conditions de livraison objectives formalisées ci-dessous.

## En cours / prochaine étape

- [ ] **Saisie des données réelles** par l'utilisateur (comptes : `saisie@cuf.cm` / `cuf2026` pour les opérateurs).
- [ ] **P4 — Moteur de recommandations métier** : plan complet validé dans `documents/plans/quizzical-percolating-parasol.md` (6 sections par reco, bibliothèque de contre-mesures, bilan FCFA, suppression couche IA). **En attente du feu vert utilisateur avant tout code.**
- Reporté P5 : auto-validation fiches, tendances par essence, comparaison multi-période (liste complète dans le plan P4).

## Décisions verrouillées récentes (complète CLAUDE.md, ne le remplace pas)

| Date | Décision | Détail |
|---|---|---|
| 2026-06-10 | Base purgée des données simulées | Ne PAS relancer `seed_data.py` sans accord explicite — il regénérerait des données fictives par-dessus les vraies. |
| 2026-06-09 | **chef + prod coexistent** (P65, revert de P64) | Ne JAMAIS supprimer le rôle `chef`. Deux profils distincts : `chef@cuf.cm` (Chef Scierie, cockpit `/dashboard/chef`) et `prod@cuf.cm` (Chef de Production, `/dashboard/prod`). |
| 2026-06-05 | Couche IA à supprimer en P4 | `app/services/reco_ai.py` viole la règle « 100 % hors ligne ». Suppression actée, exécution prévue en P4. |
| 2026-06-05 | Format reco = 6 sections | Signal → Lecture terrain → Coût → Action → Gain attendu → Vérification. Jamais de conseil générique. |

## Définition de « livré » (conditions d'arrêt objectives)

Une feature n'est **livrée** que si TOUTES ces portes passent — jamais « ça a l'air bon » :

1. `python -m compileall app/` sans erreur ;
2. `bash .claude/skills/run-cuf-pilotage/smoke.sh` → **20/20 verts** (ou plus si checks ajoutés — le total ne baisse jamais) ;
3. Screenshots Playwright si l'UI a changé (`screenshot.py <role>`) ;
4. Note d'impact 9 sections dans `documents/notes-impact/` ;
5. Commit + push sur `claude/install-claude-excel-6MGzv` (jamais main) ;
6. Mise à jour de ce fichier (ETAT.md).

## Leçons apprises (append-only, datées)

- **2026-06-10** — La purge de données doit respecter l'ordre des FK : `ActionChefEvenement → ActionChef → Probleme → Arret → Equipe`. Users et Parametres épargnés.
- **2026-06-09** — `git revert --no-edit <sha>` est la voie propre pour annuler une feature entière (P64→P65 : 22 fichiers restaurés d'un coup, y compris un template supprimé). Reconstruire à la main = risque d'oubli.
- **2026-06-09** — Un revert git ne défait PAS les migrations déjà exécutées en base : après le revert de P64, `chef@cuf.cm` avait encore `role='prod'` en DB. Toujours vérifier la base après un revert qui touche `_repair_seed_roles()`.
- **2026-06-09** — La compaction de conversation perd des décisions → ce fichier existe pour ça. Toute décision structurante doit être écrite ici AVANT la fin de session.
- **2026-06-08** — Les notes d'impact vivent à la racine (`documents/`), pas dans `cuf-pilotage/`. Lancer `git add` depuis `/home/user/projet-mem`, sinon erreur pathspec.
- **2026-06-04** — Playwright : un `browser.new_context()` PAR rôle, sinon Flask-Login redirige et `input[name="email"]` n'existe pas (TimeoutError).
- **2026-06-04** — Les tokens CSRF sont à usage unique : re-récupérer un token avant chaque POST.

## À savoir expliquer en soutenance (dette de compréhension)

> Chaque feature livrée ajoute ici ce que BWAME doit pouvoir expliquer SANS l'app sous les yeux.

- **TRS = Disponibilité × Performance × Qualité** (D×P×Q). L'app le calcule par poste via un balayage des créneaux horaires (`app/services/trs.py`) ; seul le dépassement de maintenance planifiée est imputé à la Disponibilité.
- **Pourquoi la bicoupe est le goulot** : elle traite 100 % du bois (chariot va-et-vient). Un arrêt bicoupe = arrêt de toute la chaîne 4 → c'est pourquoi les analyses de criticité la priorisent.
- **Manque à gagner (FCFA)** = heures perdues × capacité (m³/h, paramètre `capacite_equipe_h` ≈ 1,5625) × prix moyen pondéré par essence. Ce n'est PAS un chiffre inventé : chaque terme est paramétrable dans `/admin/parametres`.
- **Deux jeux de prix coexistent** : le `prix_snapshot` figé à la soumission de chaque fiche (intégrité historique) et les `Parametre` vivants (calculs courants). En soutenance : « les montants historiques ne changent pas quand on met à jour un prix ».
- **Objectif 25 m³/jour** = objectif affiché CUF, jamais présenté comme techniquement fondé (règle mémoire). Production réelle observée : 10–20 m³/poste. C'est l'écart que l'app mesure (H1/H3).
- **Pourquoi 100 % hors ligne** : terrain Ebolowa sans réseau fiable ; SQLite local + .exe Windows = zéro dépendance externe, données souveraines.
- **Statuts de fiche** : seules les fiches `valide_chef` + `verrouille` entrent dans les KPI (traçabilité de la validation) — un chiffre du dashboard est toujours adossé à des fiches validées identifiables.

## Protocole de mise à jour de ce fichier

En fin de session de travail, mettre à jour : « Dernière session » (remplacer), « En cours » (cocher/ajouter), « Décisions verrouillées » (ajouter si nouvelle), « Leçons apprises » et « Soutenance » (ajouter, jamais supprimer). Garder le fichier sous ~150 lignes : si une section gonfle, archiver le détail dans une note d'impact et ne garder que l'essentiel ici.
