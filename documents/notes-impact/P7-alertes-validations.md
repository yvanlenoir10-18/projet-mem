# Note d'impact mémoire — P7 : Alertes & validations de cohérence
**Commit :** `4c6290a` — `feat(chef+saisie): P7 — alertes saisies/brouillons + validations cohérence`
**Date :** 2026-05-04
**Fichiers modifiés :** `app/routes/dashboard.py` (+62 lignes) · `app/routes/saisie.py` (+33 lignes) · `app/templates/chef/_alertes.html` (nouveau, 53 lignes) · `app/templates/chef/dashboard.html` (+2 lignes) · `app/templates/saisie/formulaire.html` (+2 lignes)

---

## 1. Ce qui a été implémenté

P7 introduit un dispositif complet de **protection de la qualité des données** à travers trois fonctionnalités complémentaires : deux bannières d'alerte sur le dashboard Chef et un mécanisme de validation bloquante à la soumission des équipes.

### P7-A1 — Bannière « Saisies manquantes »

Vérifie en début de chaque visite du dashboard Chef si des postes attendus n'ont pas été saisis sur les **7 derniers jours ouvrés** (lundi-samedi). Pour chaque poste manquant, un badge cliquable est affiché avec date et shift, et le clic ouvre le formulaire de saisie **pré-rempli** avec ces valeurs (via query params `?date=...&shift=...`).

```
⚠ 4 postes non saisis sur les 7 derniers jours ouvrés.
[Mar 28/04 · Matin] [Mer 29/04 · Apres-midi] [Jeu 30/04 · Matin] [Sam 02/05 · Matin]
ℹ Un poste oublié = des m³ produits non comptabilisés. Le TRS du dashboard est faussé tant que les saisies ne sont pas complètes.
```

### P7-A2 — Bannière « Brouillons oubliés »

Liste les brouillons de l'utilisateur courant datant de **plus de 2 jours**. Chaque badge cliquable mène directement au détail du brouillon pour finalisation ou suppression. Le seuil de 2 jours a été validé par l'utilisateur comme correspondant au délai métier au-delà duquel un brouillon doit être traité.

```
ℹ 2 brouillons en attente depuis plus de 2 jours.
[Lun 27/04 · Matin · il y a 7 j] [Mer 29/04 · Apres-midi · il y a 5 j]
```

### P7-V1 — Validations bloquantes à la soumission

Helper `_verifier_coherence(equipe)` ajouté dans `saisie.py`, appelé avant le freeze des prix et la transition `brouillon → soumis`. Trois contrôles, tous bloquants (R3 : exception explicite avec flash) :

| Contrôle | Règle | Message |
|---|---|---|
| Date | `equipe.date ≤ aujourd'hui` | « la date du poste est dans le futur » |
| Volume | `Σ(conforme + déclassé) ≤ Σ entrée` (tolérance 0.01 m³) | « volumes sortis (X m³) supérieurs au volume entré (Y m³) » |
| Durée arrêts | `Σ duree_min ≤ Parametre.duree_poste` (480 min par défaut) | « durée totale d'arrêts (X min) supérieure à la durée du poste (Y min) » |

Si une incohérence est détectée, la soumission est annulée, un `flash` de niveau `danger` explique le problème, et l'utilisateur est redirigé vers le détail du poste pour correction.

---

## 2. Lien avec les objectifs du mémoire

P7 répond directement à **OS2** (mesurer la production réelle à travers un système de collecte de données mis en place sur le terrain) et indirectement à **OS6** (concevoir un outil de pilotage adapté).

OS2 ne se contente pas de définir le système de saisie — il exige que les données collectées soient **utilisables pour l'analyse**. Sans contrôles de cohérence et sans alertes de complétude, les KPI affichés sur le dashboard auraient un statut épistémologique fragile : un TRS calculé sur des données partielles ou incohérentes ne peut pas valider H3, ni servir de base à la projection F3.

P7 ferme la boucle :
- **A1** garantit la **complétude** (aucun poste oublié)
- **A2** garantit la **terminaison du workflow** (aucun brouillon abandonné qui fausserait l'invisibilité des données)
- **V1** garantit la **cohérence interne** (aucune saisie absurde acceptée)

Sans P7, la base de données pourrait silencieusement contenir des incohérences que ni le Chef ni le PDG ne verraient.

---

## 3. Données et calculs mobilisés

### Calcul des saisies manquantes (P7-A1)

```python
debut_check = aujourd_hui - timedelta(days=7)
postes_attendus = [(j, shift) for j in range(debut_check, aujourd_hui)
                   if j.weekday() < 6  # exclut dimanche
                   for shift in ('Matin', 'Apres-midi')]

postes_existants = {(e.date, e.numero_equipe) for e in Equipe.query.filter(...)}
manquants = [p for p in postes_attendus if p not in postes_existants]
```

**Complexité :** une seule requête SQL pour récupérer les équipes existantes (≤ 14 lignes), set lookup en O(1) pour chaque poste attendu. Coût négligeable.

### Calcul des brouillons oubliés (P7-A2)

```python
brouillons = Equipe.query.filter(
    user_id == current_user.id,
    statut == 'brouillon',
    date <= aujourd_hui - timedelta(days=2)
).all()
```

**Filtrage par propriété (R9) :** seul l'utilisateur courant voit ses propres brouillons. Aucune fuite entre comptes.

### Validations de cohérence (P7-V1)

Aucun nouveau modèle, aucun calcul nouveau. Lecture directe des champs `volume_entree`, `volume_conforme`, `volume_declass` (productions) et `duree_min` (arrêts), comparaison à `Parametre.duree_poste`.

**Tolérance arrondi 0.01 m³** sur le volume : un opérateur peut saisir `volume_entree=10.00, conforme=6.50, declass=3.50` (`somme=10.00, exact`). Si la somme dérive de 0.01 m³ à cause d'arrondis flottants, le contrôle ne déclenche pas. Au-delà de 0.01 m³, c'est une vraie incohérence.

---

## 4. Hypothèses testées ou confirmées

**P7 ne contredit aucune hypothèse — il les renforce toutes.**

- **H3** (TRS réel < 60 %) : la validité scientifique de cette mesure dépend de la cohérence des données. Sans P7, un TRS de 55 % calculé sur une base contenant des saisies absurdes (volume sorti > entré) ou incomplète (40 % des postes non saisis) ne pourrait pas valider H3 — il pourrait être un artefact statistique. P7 garantit que le TRS observé est **interprétable**.

- **H4** (actions correctives sans investissement majeur peuvent améliorer le TRS) : la projection F3 du gain FCFA s'appuie sur le TRS courant. Si ce TRS est faux, la projection est fausse. P7 protège la fiabilité des décisions prises sur la base de F3.

- **H1, H2** : non directement impactées, mais la base de données sur laquelle elles seront vérifiées (rapport stage, comparaisons benchmark) bénéficie de la qualité protégée par P7.

**Aucune contradiction signalée.** P7 est une couche transversale de qualité des données.

---

## 5. Ce que ce module permet de montrer dans le mémoire

- **Démarche scientifique de la collecte :** P7 démontre que la base de données du mémoire n'est pas un simple agrégat de saisies — c'est un **corpus contrôlé**. Chaque équipe soumise a passé les trois contrôles V1. Cette traçabilité de qualité peut être présentée dans la section Méthodologie comme une garantie de la validité des données analysées.
- **Détection active des oublis :** la bannière A1 transforme un risque silencieux (données manquantes) en signal visible (badges orange). C'est l'incarnation du principe de **management visuel** décrit par Kankkunen & Holopainen (2024) — les écarts ne sont pas découverts en bout de chaîne, ils s'invitent dans la conscience du Chef chaque jour.
- **Interface auto-explicative :** les messages d'erreur de V1 sont rédigés en langage métier (« volumes sortis supérieurs au volume entré »), pas en langage technique (« constraint violation »). L'opérateur comprend l'erreur sans documentation. Cela illustre un choix UX cohérent avec OS6 (outil adapté aux utilisateurs réels, pas aux développeurs).
- **Boucle complète saisie → analyse → action :** P7 ferme la boucle de l'outil de pilotage. Les phases précédentes l'ouvraient (P1 saisie, P2 analyse, P5/P6 visualisation, P3 workflow). P7 garantit que la boucle entière s'exécute proprement, sans rupture de qualité de donnée à aucune étape.

---

## 6. Limites actuelles

- **Pas de notification externe :** P7 n'envoie ni email ni SMS. Le Chef ne voit les alertes que s'il ouvre le dashboard. Acceptable pour le contexte CUF où le dashboard est consulté quotidiennement, mais limitant si un Chef est absent plusieurs jours.
- **Seuil 7 jours codé en dur pour A1 :** si la chaîne 4 passe à un rythme de production différent (ex. 5 jours/semaine), le calcul des postes attendus reste sur 6 jours ouvrés. À refactoriser en paramètre `Parametre.jours_ouvres_semaine` si le besoin émerge.
- **Pas de distinction « jamais prévu » vs « oublié » :** un samedi de fermeture exceptionnelle apparaîtra comme un poste manquant. Le Chef devra mentalement filtrer ces faux positifs. Pas de mécanisme pour marquer un jour comme « non productif planifié ».
- **Validation V1 limitée à la cohérence interne :** P7-V1 ne détecte pas les valeurs **plausibles mais aberrantes** (ex. `volume_entree=500 m³` pour un poste de 8h). Une validation par seuil métier (ex. `volume_entree ≤ 50 m³ par poste`) pourrait être ajoutée mais nécessite calibration sur données CUF réelles.
- **Tolérance arrondi 0.01 m³ assumée :** si CUF passe à une saisie au gramme près (improbable), cette tolérance pourra masquer de vraies incohérences. Pas un risque pratique.
- **Brouillons d'autres utilisateurs invisibles :** A2 ne montre que les brouillons de l'utilisateur courant (cohérent avec R9 propriété > rôle). Si un opérateur quitte CUF en laissant des brouillons, le Chef ne les voit pas dans son alerte personnelle. La page `historique` reste accessible pour ce cas.

---

## 7. Vérification de cohérence avec les notes précédentes

La règle **R3** (`leçons.md` : capturer toutes les exceptions dans les routes POST) est respectée : `_verifier_coherence` retourne un message d'erreur explicite plutôt que de laisser remonter une exception générique. Le `flash(..., 'danger')` traduit l'erreur en message UX clair.

La règle **R9** (contrôle d'accès par propriété, pas par rôle) est respectée : la bannière A2 filtre `Equipe.user_id == current_user.id`, pas `current_user.role == 'chef'`. Un opérateur, un chef et un admin voient chacun **leurs** brouillons.

La règle **R10** (fonctions pures vs mutation) est respectée : `_verifier_coherence` est une fonction **pure** — elle lit les attributs de l'équipe et retourne un message ou `None`, sans modifier d'objet SQLAlchemy. La transition de statut est faite après validation, pas pendant.

La règle **R11** (arithmétique en Python, pas en Jinja2) est respectée : tous les calculs (`Σ volumes`, `Σ durées`, `aujourd_hui − date`, `weekday() < 6`) sont en Python. Les templates ne font que de l'itération et de l'affichage.

La note `P5d-alerte-brouillon-lien-pdg.md` documentait une alerte brouillon côté PDG. **P7-A2 ne duplique pas P5d, elle la complète :** P5d alerte le PDG sur le **nombre total** de brouillons sur la période, P7-A2 alerte le Chef sur **ses propres** brouillons individuels avec lien direct vers chaque détail. Les deux vues coexistent légitimement et reflètent les deux personas (PDG = vision agrégée, Chef = vision opérationnelle).

La note `P6-F5-scorecard-semaine.md` documentait que le scorecard montrait les saisies manquantes par un tiret `—` mais sans alerte active. **P7-A1 complète F5 :** le scorecard reste passif (regard d'ensemble), la bannière P7-A1 est active (interpellation immédiate). Les deux mécanismes ne se contredisent pas, ils se renforcent.

**Aucune contradiction signalée.**

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Jonsson & Lesshammar (1999) — OEE fondateur, Suède | Insistent sur la cohérence des données comme prérequis à la calculabilité du TRS : « OEE is only as reliable as its inputs ». P7-V1 incarne ce principe — refuser une saisie incohérente plutôt que d'en tirer un TRS fictif |
| Kankkunen & Holopainen (2024) — Daily management UPM Plywood | Principe du management visuel : les écarts (saisies manquantes, brouillons abandonnés) doivent être détectés **chaque jour** dans l'interface consultée, pas en revue mensuelle. P7-A1 et P7-A2 instancient ce principe |
| Steenkamp et al. (2017) — VMS open-source, Afrique du Sud | Importance des contrôles automatiques de cohérence dans les systèmes manuels de saisie : sans ces contrôles, la base devient rapidement non-fiable. P7-V1 transpose ce principe au contexte CUF |
| Mncwango & Mdunge (2025) — DMAIC, OEE bas, Afrique du Sud | Phase « Measure » du DMAIC : pas d'analyse possible sans validation de la mesure. P7 est l'équivalent applicatif de cette phase — la mesure (TRS) ne peut être analysée que si elle est garantie cohérente à la source |

---

## 9. Prochaines étapes

- **Test terrain Windows :** validation par l'utilisateur lors du prochain stage CUF — vérifier que les bannières apparaissent quand attendu, que le pré-remplissage du formulaire fonctionne, et que les messages d'erreur de V1 sont bien compris par les opérateurs.
- **Recalibrage des seuils si nécessaire :** si A1 produit trop de faux positifs (samedis de fermeture, jours fériés camerounais), introduire un calendrier de jours non productifs. Différé jusqu'à observation terrain.
- **Validation par seuil métier (V2 différé) :** ajouter `volume_entree ≤ 50 m³ par poste` une fois la valeur calibrée sur données réelles CUF. Évite les fautes de frappe (50 → 500).
- **Rédaction mémoire — section Méthodologie :** P7 fournit le matériau pour décrire la **rigueur de collecte** de la base de données du mémoire. À mentionner dans la sous-section « Validation des données ».
- **P6 + P7 = OS2 + OS6 complets :** l'outil de pilotage est désormais fonctionnellement clos. Prochaine grande étape : rédaction mémoire ou documentation utilisateur (guide opérateur, guide Chef, guide PDG).
- **Windows :** synchronisation git nécessaire (`git pull origin claude/install-claude-excel-6MGzv`) pour récupérer P7.
