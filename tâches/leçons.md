# CUF Pilotage — Journal des erreurs et apprentissages

> Mis à jour automatiquement après chaque correction
> Lire en début de session avant toute action

---

## 📚 RÈGLES ACCUMULÉES

### R1 — Toujours supprimer cuf.db après un changement de schéma
**Contexte :** SQLAlchemy `db.create_all()` est non-destructif — il ne supprime pas les colonnes obsolètes.
**Règle :** Si un modèle change (ajout/suppression de colonne), le fichier `instance/cuf.db` doit être supprimé sur la machine cible avant redémarrage.
**Instruction utilisateur :** `del instance\cuf.db` (Windows) puis `python run.py`

### R2 — Windows : `use_reloader=False` obligatoire
**Contexte :** Flask debug mode avec watchdog sur Windows Store Python provoque une boucle de rechargement infinie — le processus se relance en boucle toutes les secondes.
**Règle :** `run.py` doit toujours avoir `use_reloader=False, debug=True`.

### R3 — Capturer toutes les exceptions dans les routes POST
**Contexte :** `except (ValueError, KeyError)` ne capture pas les erreurs SQLAlchemy (`OperationalError`, `IntegrityError`). Résultat : page 500 générique sans détail.
**Règle :** Les routes POST de saisie utilisent `except Exception as e` avec `flash(f'Erreur : {type(e).__name__} — {str(e)}', 'danger')`.

### R4 — Cadrage obligatoire avant implémentation
**Contexte :** P2 a été commencé sans cadrage préalable. L'utilisateur a dû stopper le développement et demander un cadrage en bonne et due forme.
**Règle :** Pour toute nouvelle phase ou fonctionnalité non triviale, présenter un document de cadrage et attendre la validation explicite avant tout code.

### R5 — volume_sorti ≠ volume_conforme
**Contexte :** L'ancien modèle avait `volume_sorti` ambigu. L'utilisateur a précisé que la production réelle se compose de trois catégories distinctes.
**Règle :** 
- `volume_conforme` = planches conformes (export, prix plein)
- `volume_declass` = bois déclassé vendu localement (prix ×0.30)
- `volume_dechets` = calculé par différence, jamais stocké en DB
- Pour le TRS Performance : `volume_sorti = conforme + declass` (tout ce qui sort de la scie utilisable)
- Pour le TRS Qualité : `conforme / (conforme + declass)` — les déchets sont exclus (pertes process, pas qualité)

### R6 — Ne jamais coder avant validation du plan (Vibe Coding Protocol)
**Contexte :** Instauré par l'utilisateur le 2026-04-30.
**Règle :** Toute tâche impliquant 3+ étapes requiert : plan écrit → explication → validation explicite → puis code.
**Commandes de validation :** `ok`, `vas-y`, `d'accord`, `go`, `✅`, `lance`, `continue`, `oui`

### R7 — Ne jamais effacer la DB au démarrage de l'application
**Contexte :** P5b — `start.ps1` supprimait `instance/cuf.db` à chaque lancement, laissant le dashboard vide à chaque redémarrage Windows. L'utilisateur ne voyait pas ses fonctionnalités P5.
**Règle :** Le script de démarrage ne doit jamais supprimer de données utilisateur. La suppression doit être manuelle et explicite (`del instance\cuf.db` documenté en cas de migration de schéma — voir R1). Le seed doit utiliser un guard idempotent (`if Equipe.query.first(): return`) pour ne s'exécuter qu'une fois sur base vide.

### R8 — Templates Jinja2 défensifs avec `|default()`
**Contexte :** P5c — un crash `UndefinedError: 'nb_brouillons' is undefined` est apparu côté Windows après un `git pull` partiellement échoué (DNS error). Le template avait été mis à jour mais pas la route → désynchronisation.
**Règle :** Toute variable de contexte référencée dans un template doit avoir un fallback `|default(valeur_neutre)`. Exemples : `{% if nb_brouillons|default(0) > 0 %}`, `{% if prix_manquants|default(false) %}`. Filet de sécurité contre les désynchronisations route/template, pas un substitut à la cohérence du code.

### R9 — Contrôle d'accès par propriété, pas seulement par rôle
**Contexte :** P5d — l'alerte brouillon devait mener à une vue lecture seule pour le PDG. Plutôt que d'ajouter `if role == 'pdg': hide_buttons`, on a constaté que le template existant `historique.html` masquait déjà les boutons via `if p.user_id == current_user.id`.
**Règle :** Préférer un contrôle d'accès basé sur la propriété de l'objet (`obj.user_id == current_user.id`) à un contrôle basé sur le rôle. Plus robuste, plus testable, fonctionne même si un nouveau rôle est ajouté plus tard sans modifier les templates.

### R10 — Fonctions pures vs fonctions à mutation : séparer
**Contexte :** P6-F1 — `calcule_trs(equipe)` mute l'objet (assigne `equipe.trs_disponibilite`, etc.). Pour le dashboard en lecture seule, il fallait un (D, P, Q) sans dirtyfier la session SQLAlchemy.
**Règle :** Quand un calcul est utilisé dans un contexte read-only (dashboard, export, stats), créer un helper pur séparé (ex. `decompose_dpq(equipe)` retourne `(d, p, q)` sans rien modifier). Garder la version à mutation pour les routes de soumission/écriture. Ne jamais appeler la version mutante depuis une route GET.

### R11 — Toute arithmétique côté Python, jamais en Jinja2
**Contexte :** P6-F2 — la matrice criticité affiche des durées formatées (`1h30`, `45min`). Tenté de faire la conversion minutes → format en Jinja2 : impossible (pas de `divmod`). 
**Règle :** Pré-calculer toutes les valeurs d'affichage côté route Python (formats, pourcentages, couleurs CSS) et passer au template un dict prêt à l'emploi. Jinja2 ne doit faire que de l'itération et de l'affichage. Bénéfice secondaire : les valeurs sont testables sans lancer Flask.

### R12 — Cascade multiplicative D × P × Q : jamais 3 barres de pourcentage juxtaposées
**Contexte :** P6-F1 — réflexe initial : afficher D=89 %, P=86 %, Q=87 % comme trois barres côte à côte. Erreur cognitive : suggère une additivité fausse alors que TRS = D × P × Q (multiplicatif). La critique utilisateur a corrigé : afficher la cascade en m³ perdus.
**Règle :** Pour toute visualisation TRS, utiliser la décomposition cascade `(1−D)·cap + D·(1−P)·cap + D·P·(1−Q)·cap + D·P·Q·cap = cap`. Une seule barre stacked à 4 segments, pas 3 barres distinctes. L'identité algébrique garantit qu'aucune perte n'est comptée deux fois.

### R13 — TRS par essence : toujours rattacher les arrêts par chevauchement horaire
**Contexte :** Une essence peut être sciée de 06h à 09h puis une autre de 09h à 14h. Affecter le TRS global du poste à chaque essence biaise l'analyse : un arrêt 10h-11h ne concerne pas l'essence terminée à 09h.
**Règle :** Chaque ligne `Production` doit porter `heure_debut` et `heure_fin`. Le TRS par essence se calcule sur sa fenêtre : disponibilité = `(durée fenêtre − arrêts chevauchants) / durée fenêtre`, performance = `volume sorti essence / capacité théorique du temps utile`, qualité = `conforme / sorti`. Garder un fallback ancien calcul seulement pour les relevés historiques sans créneau.

### R14 — Perte financière officielle = CA potentiel − CA réel valorisé
**Contexte :** Le total D/P/Q peut donner un chiffre plausible mais méthodologiquement fragile, car disponibilité, performance et qualité peuvent expliquer le même manque à gagner.
**Règle :** L'indicateur financier officiel est le manque à gagner net : `CA potentiel − CA réel valorisé`. Le déclassé est valorisé à 70 % du prix normal par défaut, les déchets valent 0 FCFA/m³ en V1. D/P/Q restent une attribution causale indicative, jamais une perte financière officielle additionnée.

### R15 — Opérateur = saisie terrain, pas lecture économique
**Contexte :** L'opérateur doit saisir son nom pour que le chef sache qui a rempli la fiche, mais il ne doit pas voir les chiffres économiques.
**Règle :** Les vues opérateur affichent les données saisies et l'historique opérationnel autorisé, mais masquent le manque à gagner, les prix/m³ et les tableaux financiers. Les chiffres économiques sont réservés aux rôles chef, PDG et admin selon les routes concernées.

### R16 — Ne pas appeler “Télécharger” un export HTML présenté comme PDF
**Contexte :** L'étape 7 proposait un téléchargement HTML autonome alors que l'utilisateur attendait une fiche PDF. Cela crée une confusion d'usage.
**Règle :** Si l'application ne génère pas un vrai fichier PDF, l'action doit s'appeler `Imprimer / enregistrer en PDF` et passer par `window.print()`. Réserver `Télécharger` aux vrais fichiers joints ou aux exports dont le format est explicite.

### R17 — Après ajout d'une route Flask, redémarrer le serveur local
**Contexte :** Avec `use_reloader=False`, Flask peut recharger un template modifié sans recharger les nouvelles routes Python. Résultat : `BuildError` sur un endpoint pourtant présent dans le code.
**Règle :** Après toute nouvelle route, arrêter le serveur (`Ctrl+C`) puis relancer `python run.py`. Si un bouton pointe vers une route toute neuve, éviter de bloquer le rendu d'une page critique en cas de serveur non redémarré.

### R18 — Les classifications métier sensibles doivent être recalculées côté serveur
**Contexte :** Le formulaire d'arrêt affichait une catégorie modifiable. Même si l'interface remplissait automatiquement la catégorie, une valeur falsifiée pouvait être envoyée avec le POST.
**Règle :** Pour les champs qui pilotent les calculs ou les analyses, ne jamais faire confiance au champ envoyé par l'interface. La catégorie d'arrêt doit être recalculée côté serveur depuis la cause choisie. Le formulaire peut afficher la catégorie pour guider l'opérateur, mais il ne décide pas de la classification.

### R19 — Une ressaisie papier sans preuve ne doit pas entrer dans le circuit chef
**Contexte :** Une fiche déclarée comme ressaisie depuis papier pouvait être envoyée avec seulement un avertissement, sans fiche signée jointe.
**Règle :** Si `mode_saisie = papier`, l'envoi au chef est bloqué tant que la fiche papier signée n'est pas confirmée et jointe. Le brouillon reste possible, mais l'exploitation métier exige la preuve terrain.

### R20 — CSRF + `use_reloader=False` : templates défensifs obligatoires
**Contexte :** Après ajout de CSRF, les templates appellent `csrf_token()`. Avec `use_reloader=False`, un ancien serveur peut recharger les templates modifiés sans réinitialiser l'application Python, ce qui peut rendre `csrf_token` indisponible et provoquer un crash au rendu.
**Règle :** Tout appel template à `csrf_token()` doit être gardé par `{% if csrf_token is defined %}`. Après ajout de CSRF ou de routes Python, redémarrer complètement Flask. Le garde-fou évite le crash, mais ne remplace pas le redémarrage.

### R21 — Un champ de guidage ne doit pas ressembler à une action
**Contexte :** Côté chef, `Zone à corriger` était techniquement fonctionnel mais ambigu : changer la sélection ne faisait rien immédiatement, car la valeur sert seulement à guider l'opérateur après le renvoi.
**Règle :** Tout champ qui prépare une action future doit afficher son rôle exact, un aperçu du résultat et une confirmation après enregistrement. Si possible, ajouter un lien de prévisualisation vers la zone concernée pour éviter l'impression d'un champ "cassé".

### R22 — Les journaux techniques ne doivent pas polluer les écrans métier
**Contexte :** Le détail d'une fiche affichait `Journal d'audit des corrections` avec `soumission_initiale`, auteur, statuts et valeurs tracées. C'est utile pour la traçabilité interne, mais incompréhensible et inutile dans le flux normal du chef.
**Règle :** Garder les traces en base, mais ne les afficher que dans un espace admin/audit dédié si nécessaire. Les écrans chef/opérateur doivent montrer les décisions et actions utiles, pas les logs techniques.

### R23 — Les helpers de formulaire doivent séparer valeur par défaut et limite
**Contexte :** Dans P3.5, le helper de lecture du formulaire `get()` utilisait le deuxième argument comme valeur par défaut alors que l'appelant l'utilisait comme limite de longueur. Résultat : `GET /problemes/nouveau` envoyait un entier à `.strip()` et provoquait une erreur 500.
**Règle :** Les helpers de formulaire doivent avoir des paramètres explicites (`default`, `limite`) et être couverts par un test de rendu GET avant de tester le POST. Ne jamais mélanger valeur métier et contrainte de nettoyage dans un même argument ambigu.

---

## 📅 HISTORIQUE DES CORRECTIONS

| Date | Correction | Règle créée |
|------|-----------|-------------|
| 2026-04-30 | Schéma DB incompatible → 500 | R1 |
| 2026-04-30 | Flask reload infini Windows | R2 |
| 2026-04-30 | Exceptions trop étroites | R3 |
| 2026-04-30 | P2 sans cadrage | R4 |
| 2026-04-30 | Modèle matière ambigu | R5 |
| 2026-04-30 | Vibe Coding Protocol instauré | R6 |
| 2026-05-03 | DB effacée à chaque lancement | R7 |
| 2026-05-03 | UndefinedError sur désync template/route | R8 |
| 2026-05-03 | Contrôle PDG basé sur rôle au lieu de propriété | R9 |
| 2026-05-04 | Mutation d'équipe dans contexte read-only | R10 |
| 2026-05-04 | Tentative de divmod en Jinja2 | R11 |
| 2026-05-04 | TRS affiché comme 3 barres % juxtaposées | R12 |
| 2026-05-18 | TRS par essence biaisé par absence de créneau horaire | R13 |
| 2026-05-21 | P2 pertes nettes et rôle opérateur cadrés | R14, R15 |
| 2026-05-23 | Téléchargement HTML confondu avec fiche PDF | R16 |
| 2026-05-23 | BuildError après ajout d'une route sans redémarrage Flask | R17 |
| 2026-05-23 | Catégorie d'arrêt et preuve papier trop faciles à contourner | R18, R19 |
| 2026-05-23 | Crash potentiel templates CSRF sans redémarrage Python | R20 |
| 2026-05-24 | `Zone à corriger` fonctionnelle mais ambiguë côté chef | R21 |
| 2026-05-24 | Journal d'audit trop technique dans le détail fiche | R22 |
| 2026-05-27 | Helper formulaire P3.5 ambigu `default/limite` | R23 |
