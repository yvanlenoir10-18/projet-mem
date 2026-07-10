# ETAT.md — État vivant du projet

> **Rôle** : fichier d'état persistant entre les sessions Claude. L'agent oublie, le dépôt non.
> **Protocole** : lu en DÉBUT de chaque session (avec CLAUDE.md) · mis à jour en FIN de chaque session de travail.
> Les sections « Leçons apprises » et « Soutenance » sont *append-only* (on ajoute, on ne supprime pas).
> Ce fichier est un **résumé vivant** — le détail historique vit dans `documents/notes-impact/` (73+ notes).

---

## Dernière session — 2026-07-10

- **Import des données terrain réelles** (mai–juin 2026) en remplacement de la seed. Source : `documents/collecte/Suivi_bicoupe_CUF_mai-juin-2026.xlsx` (relevé chef, feuille 5 TRS). Outil versionné : `documents/outils/import_donnees_reelles.py` (idempotent). Note : `documents/notes-impact/import-donnees-reelles-mai-juin-2026.md`.
- **Méthode** : le fichier consigne le TRS mesuré mais pas les m³ → reconstruction par **inversion des formules `trs.py`**, ancrée sur les colonnes D/P/Q **publiées** (propres) plutôt que sur les colonnes brutes (incohérences de saisie : Marche > 480, retard = 979 min…). **Écart moyen TRS reconstruit vs fichier : 0,17 pt.**
- **Résultat** : 95 quarts, 3 créneaux réels (Matin/Après-midi/**Nuit** → chaîne 4 en 3×8), TRS bicoupe moyen **63,3 %** (médiane 65,7 %, min 0 %, max 97,9 %), conforme 756,5 m³ (atteinte 88,4 %), Pareto dominé par le **changement de lame (53,4 %)**, manque à gagner ~238,7 M FCFA.
- **Point mémoire** : TRS bicoupe réel (63,3 %) **au-dessus** de H3 (< 60 %) — à discuter honnêtement ; le vrai problème est la **dispersion** (0 %→98 %), pas la moyenne.
- **5 figures régénérées** avec les vraies données, profil Chef de Production (`prod@cuf.cm`) pour les figures 15-18, direction (`pdg@cuf.cm`) pour la 19. Smoke **24/24 verts** sur les données réelles. Aucun code applicatif modifié.

## Dernière session — 2026-06-10

- **Divergence remote/local détectée et résolue** : le revert P65 du 09/06 (restauration du rôle chef) n'avait jamais atteint le remote — le travail vivait dans un environnement perdu. Re-appliqué proprement : `git revert 70f51e0` (commit 6331133), 23 fichiers restaurés, note d'impact P65 recréée.
- **chef + prod coexistent à nouveau** : `ROLES_VALIDES = ('operateur', 'chef', 'prod', 'pdg', 'admin')`, 5 comptes en base, smoke.sh enrichi de 4 checks prod → **20/20 verts**.
- **Données simulées purgées** : 62 fiches + 109 arrêts supprimés. Comptes (5) et paramètres (27) conservés. L'utilisateur saisira ses **vraies données terrain** lui-même.
- Méthode : création de ce fichier (ETAT.md) + règle `.claude/rules/etat-vivant.md` ; vérificateur séparé prévu pour les prochaines formules critiques.

## En cours / prochaine étape

- [x] **Données réelles chargées** (2026-07-10) via `documents/outils/import_donnees_reelles.py` — mai-juin 2026, 95 quarts. La saisie manuelle opérateur reste possible en complément.
- [ ] **P5 — Dashboard Chef « aiguilleur »** : cadrage écrit le 07/06 (`documents/plans/P5-dashboard-chef-aiguilleur.md`, note P59). Aucun code encore — attendre le feu vert utilisateur.
- [x] **P4 — Moteur de prescriptions métier** : **LIVRÉ le 07/06** (P58) — 7 règles réécrites au format 6 sections, `reco_ai.py` supprimé (100 % hors ligne respecté), 4 colonnes modèle ajoutées.
- [x] **Chef V2 « Le Point »** + cascade économique : livré (P60–P62).
- [x] **Rôle prod autonome** : livré (P63) ; coexistence avec chef garantie (P65).

## Décisions verrouillées récentes (complète CLAUDE.md, ne le remplace pas)

| Date | Décision | Détail |
|---|---|---|
| 2026-07-10 | **Données réelles = source de vérité** | La base contient les relevés mai-juin 2026. Ré-import via `documents/outils/import_donnees_reelles.py` (idempotent, purge + recharge). Ne PAS relancer `seed_data.py` (regénérerait du fictif). DB hors-Git → rejouer l'import après tout nouveau conteneur. |
| 2026-07-10 | **Hypothèses d'import explicites** | Volumes m³ reconstruits par inversion TRS (le fichier n'a pas de m³). Rendement matière par essence = hypothèse de modélisation (densité bois), non mesurée — n'affecte pas le TRS. Chaîne 4 réelle = **3 postes** (Nuit inclus), objectif affiché 25 m³/j = 2 postes seulement. |
| 2026-06-10 | Base purgée des données simulées | Ne PAS relancer `seed_data.py` sans accord explicite — il regénérerait des données fictives par-dessus les vraies. |
| 2026-06-09 | **chef + prod coexistent** (P65, revert de P64 — ré-appliqué le 10/06) | Ne JAMAIS supprimer le rôle `chef`. Deux profils distincts : `chef@cuf.cm` (Chef Scierie, `/dashboard/chef`) et `prod@cuf.cm` (Chef de Production, `/dashboard/prod`). |
| 2026-06-07 | Couche IA supprimée (P58 — FAIT) | `reco_ai.py` et `test_ia.py` supprimés du dépôt. Toute réintroduction d'appel réseau viole la règle « 100 % hors ligne ». |
| 2026-06-05 | Format prescription = 6 sections | Signal → Lecture terrain → Coût → Action → Gain attendu → Vérification. Jamais de conseil générique. Implémenté via `_GABARITS` dans `services/recommandations.py`. |

## Définition de « livré » (conditions d'arrêt objectives)

Une feature n'est **livrée** que si TOUTES ces portes passent — jamais « ça a l'air bon » :

1. `python -m compileall app/` sans erreur ;
2. `bash .claude/skills/run-cuf-pilotage/smoke.sh` → **20/20 verts** (ou plus si checks ajoutés — le total ne baisse jamais) ;
3. Screenshots Playwright si l'UI a changé (`screenshot.py <role>`) ;
4. Note d'impact 9 sections dans `documents/notes-impact/` ;
5. Commit + push sur `claude/install-claude-excel-6MGzv` (jamais main) ;
6. Mise à jour de ce fichier (ETAT.md).

## Leçons apprises (append-only, datées)

- **2026-06-10** — **Un commit local jamais poussé est PERDU au changement d'environnement.** Le revert P65 du 09/06 n'existait que localement ; le remote était resté à l'état P64 (chef supprimé) pendant que le résumé de session croyait la coexistence en place. Règles : `git push` avant de clore TOUTE session ; `git fetch origin <branche>` en début de session pour détecter une divergence.
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
- **Moteur de prescriptions (P4/P58)** : 7 règles déterministes calculées sur les données réelles, chaque prescription = 6 sections (Signal → Lecture terrain → Coût → Action → Gain → Vérification). **Aucune IA, aucun appel réseau** — argument clé : reproductible et défendable, contrairement à une boîte noire.
- **Deux profils de pilotage** : `chef` (Chef Scierie — supervision atelier, validation des fiches) et `prod` (Chef de Production — cockpit décisionnel V2). La séparation reflète l'organisation réelle de CUF, pas une contrainte technique.

## Protocole de mise à jour de ce fichier

En fin de session de travail, mettre à jour : « Dernière session » (remplacer), « En cours » (cocher/ajouter), « Décisions verrouillées » (ajouter si nouvelle), « Leçons apprises » et « Soutenance » (ajouter, jamais supprimer). Garder le fichier sous ~150 lignes : si une section gonfle, archiver le détail dans une note d'impact et ne garder que l'essentiel ici.
