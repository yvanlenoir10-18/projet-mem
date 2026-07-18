# Note d'impact mémoire — Remplacement de l'essence Azobé par Bilinga

> Branche `claude/install-claude-excel-6MGzv` · Session 2026-07-14 · Commit `db74e76`
> Demande utilisateur explicite · Renomme la 4e essence configurée de l'application.

---

## 1. Ce qui a été implémenté

Remplacement complet de l'essence **Azobé** par **Bilinga** dans toute l'application
(23 occurrences, 10 fichiers) :

- **Constante métier** : `config.py` → `ESSENCES = ['Ayous', 'Bilinga', 'Iroko', 'Movingui']`.
- **Clés de paramètres** : `prix_azobe` → `prix_bilinga`, `capacite_azobe_h` →
  `capacite_bilinga_h` (seed `app/__init__.py`, liste `PARAMS_ADMIN_ONLY` de `admin.py`,
  template `admin/parametres.html`).
- **Interface** : puces de sélection d'essence du formulaire de saisie, libellés, couleur
  d'export Excel, ensemble `essences_dures` du dashboard.
- **Données de démonstration** : `seed_data.py`, `seed_scenarios_chef_v2.py`, scénarios
  démo de `__init__.py`.
- **Outil d'import terrain** : Bilinga devient la 4e essence configurée ; Azobé (minoritaire
  dans les relevés) bascule dans « Autre ».

Vérification : **0 occurrence fonctionnelle d'« Azobé »** dans `cuf-pilotage/` (seules
subsistent des mentions dans les commentaires de migration et la documentation, qui doivent
nommer l'ancienne essence pour tracer le changement). `python -m compileall` OK, smoke
**24/24 verts**, TRS réel inchangé (63,3 %), paramètres DB migrés.

## 2. Lien avec les objectifs du mémoire

- **Fidélité terrain (transversal OS1–OS4)** : Bilinga est une essence **majoritaire** des
  relevés réels de CUF (la base consolidée comporte une feuille dédiée `LARGEURS BILINGA` de
  ~58 lignes), alors qu'Azobé y est marginal. Le renommage aligne le modèle de l'app sur la
  réalité de la chaîne 4, ce qui renforce la crédibilité de la démonstration.
- **OS1 (rendement matière)** : Bilinga, bois dense, porte un rendement matière distinct
  (0,53) cohérent avec sa dureté, dans la logique de différenciation par essence déjà en place.

## 3. Données et calculs mobilisés

Le renommage ne change **aucune formule**. Il touche :
- la clé de recherche du prix et de la capacité par essence (`normalise_essence('Bilinga')`
  → `bilinga`, sans accent, donc `prix_bilinga` / `capacite_bilinga_h`) ;
- l'attribution des essences à l'import : `bilinga → 'Bilinga'` (configurée), tandis
  qu'Azobé, absent des 4 configurées, rejoint « Autre ».

Le TRS ne dépend pas de l'essence (il s'ancre sur temps d'ouverture et cadences) : sa valeur
réelle reste **63,3 %** après migration, ce qui confirme l'absence de régression.

## 4. Hypothèses testées ou confirmées

- **Cohérence de la clé de paramètre** : confirmé que `normalise_essence` reste générique
  (suppression d'accents) — aucun cas particulier « azobe » n'était codé en dur.
- **Prix/capacité Bilinga** : repris tels quels des valeurs Azobé (280 000 FCFA/m³ ; 1,5625
  m³/h) faute de valeur Bilinga spécifique confirmée — **à ajuster** dès que le prix de vente
  réel du Bilinga sera connu (paramétrable dans `/admin/parametres`).

## 5. Ce que ce module permet de montrer dans le mémoire

- Une application **paramétrable** : changer d'essence de référence se fait proprement, sans
  casser les calculs — argument de robustesse et d'adaptabilité de l'outil (OS6).
- Un modèle **fidèle au mix réel** d'essences de la chaîne 4 (Bilinga au premier plan).

## 6. Limites actuelles

- **Prix/capacité Bilinga hérités d'Azobé** : à valider avec le terrain (ordre de grandeur
  filière), sous peine de biaiser le manque à gagner sur les volumes Bilinga.
- **Azobé regroupé dans « Autre »** : les rares volumes Azobé réels perdent leur étiquette
  propre ; acceptable vu leur poids marginal, mais à mentionner si une analyse par essence
  cite Azobé.

## 7. Vérification de cohérence avec les notes précédentes

- **Contredit une règle verrouillée antérieure** : CLAUDE.md et `memoire-cuf.md` listaient
  « Essences (4 seulement) : Ayous, **Azobé**, Iroko, Movingui ». Cette règle est **mise à
  jour explicitement** (Azobé → Bilinga, décision 2026-07-14) et tracée dans ETAT.md. C'est
  un changement assumé de décision verrouillée, pas une incohérence silencieuse.
- **Cohérent avec la note d'import du 2026-07-10** : l'outil d'import est mis à jour en
  conséquence (Bilinga configurée, Azobé → Autre) ; le contrôle TRS (0,17 pt d'écart) reste
  valide.

## 8. Références bibliographiques mobilisées implicitement

- Aucune nouvelle référence : changement de nomenclature. La différenciation du rendement par
  densité (Bilinga bois dur) reste adossée aux **benchmarks filière bois** rappelés dans
  CLAUDE.md (rendement matière Afrique centrale ~35 % de pertes).

## 9. Prochaines étapes

- **Renseigner le prix de vente réel du Bilinga** dans `/admin/parametres` (aujourd'hui
  hérité d'Azobé : 280 000 FCFA/m³).
- Décider si les volumes Azobé résiduels doivent rester dans « Autre » ou être suivis à part.
- Rappel : la génération de journées fictives pour atteindre un TRS cible a été **refusée**
  (intégrité) — les ~95 postes réels donnent déjà 64,0 % (fichier `Analyses_et_resultats_CUF`).
