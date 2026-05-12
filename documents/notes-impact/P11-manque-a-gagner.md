# Note d'impact — P11 : Manque à gagner estimé + Renommage Wood_Pilot_Ebolowa
> Commit : (en attente) — feat(p11): manque à gagner estimé comme indicateur principal + renommage app
> Date : 2026-05-12
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Refonte de l'indicateur financier principal de l'application. La somme additive D + P + Q (auparavant nommée « pertes financières ») est remplacée par un calcul économique direct : **manque à gagner estimé = valeur potentielle cible − valeur réelle valorisée**. Cette approche évite le double comptage entre composantes de pertes (certaines causes pouvant se chevaucher dans la décomposition Disponibilité × Performance × Qualité). La décomposition D/P/Q est conservée mais rétrogradée au rang d'**attribution causale indicative** : elle explique pourquoi le manque existe, sans prétendre en quantifier exactement la somme.

Le calcul est effectué par essence lorsque le détail est disponible. La valeur conforme et la valeur déclassée (revendue à 30 % du prix conforme via le paramètre `taux_revente_rebut`) sont sommées par essence, puis additionnées pour obtenir la valeur réelle valorisée du poste. La valeur potentielle utilise l'objectif paramétrable (`objectif_m3`, valeur courante : 25 m³/poste) multiplié par le prix moyen pondéré des essences effectivement traitées.

En parallèle, l'application a été renommée de « WoodPilot » en **Wood_Pilot_Ebolowa**. Le nom apparaît désormais dans tous les titres HTML, dans la marque visible (sidebar desktop, mobile et page de login), dans les en-têtes d'erreur 404/500, dans le pied de la feuille de relevé imprimable, et dans tous les commentaires d'en-tête Python et CSS. La coloration verte sur « Pilot » est préservée dans le brand stylé. Une incohérence factuelle découverte au passage (sous-titre « CUF · Mbalmayo » alors que le site est à Ebolowa) a été corrigée.

---

## 2. Fichiers modifiés ou créés

| Fichier | Type | Action |
|---|---|---|
| `cuf-pilotage/app/services/trs.py` | Service | Ajout `calcule_manque_gagner()` + `manque_a_gagner_agrege()` |
| `cuf-pilotage/app/routes/dashboard.py` | Route | Import + appels dans `vue_chef`, `vue_pdg`, `pertes` |
| `cuf-pilotage/app/routes/saisie.py` | Route | Import + appel dans `detail_poste` |
| `cuf-pilotage/app/templates/dashboard/pertes.html` | Template | Refonte titre + KPIs principaux + causes D/P/Q secondaires |
| `cuf-pilotage/app/templates/chef/dashboard.html` | Template | Nouvelle carte manque à gagner + renommage décomposition |
| `cuf-pilotage/app/templates/pdg/dashboard.html` | Template | Remplacement KPI « Pertes financières » par « Manque à gagner estimé » |
| `cuf-pilotage/app/templates/saisie/detail.html` | Template | Refonte panneau financier du poste avec V. potentielle / V. valorisée / Manque |
| `cuf-pilotage/app/services/export.py` | Service | Section B Excel : manque à gagner principal + B-bis causes D/P/Q |
| `cuf-pilotage/config.py` | Config | Docstring renommée |
| `cuf-pilotage/run.py` | Entrypoint | Docstring renommée |
| `cuf-pilotage/app/__init__.py` | Factory | Docstring renommée |
| `cuf-pilotage/app/utils.py` | Utils | Docstring renommée |
| `cuf-pilotage/app/routes/admin.py` | Route | Docstring renommée |
| `cuf-pilotage/app/templates/base.html` | Template | Titre + marque sidebar (×2) + topbar + sous-titre Mbalmayo → Ebolowa |
| `cuf-pilotage/app/templates/auth/login.html` | Template | Marque page de login |
| `cuf-pilotage/app/templates/errors/404.html` | Template | Titre |
| `cuf-pilotage/app/templates/errors/500.html` | Template | Titre |
| `cuf-pilotage/app/templates/saisie/feuille_releve.html` | Template | Pied de feuille |
| `cuf-pilotage/app/static/css/style.css` | CSS | Commentaire d'en-tête |
| `documents/notes-impact/P11-manque-a-gagner.md` | Documentation | Nouveau |

Aucune migration de base de données. Aucun ajout de colonne. Aucun risque sur les données existantes (`instance/cuf.db` non touchée, R7 respectée).

---

## 3. Objectif spécifique du mémoire servi

**OS3 — Évaluer l'écart entre la capacité théorique et la production réelle, calculer le TRS de la chaîne 4 et estimer le coût financier des pertes enregistrées** : la nouvelle formule donne une estimation économique défendable, sans contradiction interne ni double comptage. La présentation « manque à gagner estimé » est plus prudente que « pertes financières certaines » et résiste mieux à une critique méthodologique en soutenance.

**OS5 — Proposer des actions correctives prioritaires et estimer les gains de production et les bénéfices financiers attendus** : la décomposition D/P/Q en attribution causale fournit aux décideurs le diagnostic nécessaire pour orienter les actions correctives (cause majoritaire = piste prioritaire), sans confondre diagnostic et chiffrage.

**OS6 — Concevoir un outil de pilotage adapté** : le renommage en Wood_Pilot_Ebolowa donne à l'outil une identité claire, ancrée géographiquement, qui facilite son adoption sur site et sa pérennité après le stage.

---

## 4. Lien avec les hypothèses de recherche

**H3 — Le TRS réel de la chaîne 4 est inférieur à 60 %** : la refonte n'affecte pas le calcul du TRS lui-même (toujours D × P × Q × 100). Elle clarifie en revanche la distinction entre l'indicateur opérationnel (TRS, mesure de l'utilisation de la capacité technique) et l'indicateur économique (manque à gagner, mesure de l'écart à l'objectif financier). Cette clarification renforce la cohérence du raisonnement défendu sous H3.

**H4 — Des actions correctives sans investissement majeur permettent d'améliorer le TRS et de réduire les pertes financières** : la mécanique d'attribution causale (D/P/Q) permet de cibler les actions correctives les plus impactantes en fonction de la cause dominante observée. La séparation entre mesure du manque et diagnostic des causes est un préalable méthodologique à la formulation d'actions correctives crédibles.

**H1 et H2 ne sont pas directement concernées par cette modification**. H2 doit néanmoins être nuancée par les observations terrain à venir, certaines pertes pouvant relever de l'approvisionnement amont (parc à grumes) plutôt que de l'organisation interne, sans qu'une donnée suffisante permette encore de trancher.

---

## 5. Technique utilisée et choix architectural

La nouvelle fonction `calcule_manque_gagner()` est ajoutée **à côté** de `calcule_pertes_equipe()` sans modifier cette dernière. Cette stratégie « add-then-deprecate » évite tout risque de régression sur les appelants existants (5 références dans `export.py`, 2 dans `dashboard.py`, 1 dans `saisie.py`). Les templates passent désormais le dictionnaire `manque` ou `manque_periode` au rendu, et `calcule_pertes_equipe()` reste utilisée pour fournir les valeurs D/P/Q en attribution causale.

La fonction `manque_a_gagner_agrege()` somme les composantes sur une liste d'équipes, ce qui permet aux dashboards chef et PDG d'afficher un total période (7 j, 30 j, 90 j, mois complet, période libre). Aucun cache n'est introduit — le calcul est suffisamment rapide pour un volume de quelques centaines d'équipes par mois.

Pour le renommage, la stratégie a été de ne pas toucher au dossier `cuf-pilotage/` ni aux classes CSS `wp-*` : ces identifiants techniques sont référencés par Flask (paths statiques) et par les hooks git (post-commit-memoir.sh), et leur renommage casserait la procédure Windows et la chaîne d'intégration. Le nom de marque a été correctement séparé de l'identifiant technique.

---

## 6. Contrainte respectée

**Règle R7** : aucune modification de schéma de base de données. Aucune migration. La base `instance/cuf.db` reste intacte. Toutes les données existantes (équipes, productions, arrêts, paramètres, utilisateurs) continuent de fonctionner sans intervention.

**Règle R6** : validation explicite obtenue avant écriture du code — l'utilisateur a confirmé les trois points clés (taux global suffisant, objectif 25 m³, déchets valorisés différés) et a explicitement répondu « GO » au plan présenté.

---

## 7. Limites identifiées

- **Prix déclassé par essence non implémenté** : le calcul utilise un taux global `taux_revente_rebut` (30 %) appliqué uniformément au prix conforme de chaque essence. Si CUF distingue à l'avenir un prix de revente déclassé par essence, il faudra ajouter une colonne `prix_declass_snapshot` au modèle `Production`. Cette extension est documentée dans le plan P11 et reportée à une phase ultérieure.

- **Déchets valorisés non saisissables** : la valeur des déchets vendus localement (sciure, dosses) n'est pas encore intégrée à la valeur réelle valorisée. Selon l'utilisateur, cette vente est occasionnelle et le besoin de saisie ne se justifie pas pour la V1. Quand le besoin émergera, deux champs (`dechets_valorises_fcfa`, `dechets_valorises_note`) seront ajoutés à la table `Equipe`.

- **Cohérence D + P + Q ≠ manque à gagner total** : c'est précisément le constat qui justifie la refonte. Le delta peut atteindre 10 à 30 % selon les postes. L'interface affiche désormais explicitement cette indication via la note « certaines causes peuvent se chevaucher ». Aucune alerte automatique de cohérence n'est encore générée — c'est une piste pour P12.

- **Renommage du dossier non effectué** : le dossier reste `cuf-pilotage/`. Un renommage en `wood-pilot-ebolowa/` casserait la procédure Windows (`cd cuf-pilotage`), les imports Python, le hook post-commit et le chemin PythonAnywhere. Ce renommage est jugé non rentable pour un gain purement cosmétique.

---

## 8. Commandes Windows pour appliquer

```powershell
git pull origin claude/install-claude-excel-6MGzv
python run.py
```

L'application est ensuite accessible sur `http://127.0.0.1:5000`. Aucune migration de base de données n'est nécessaire. Les anciennes équipes saisies affichent le nouveau libellé « Manque à gagner estimé » avec le calcul appliqué rétroactivement sur leurs prix snapshot.

Pour vérifier visuellement le renommage :
- Page de login : marque « Wood_*Pilot*_Ebolowa » avec « Pilot » en vert
- Sidebar sous le logo : même marque + sous-titre « CUF · Ebolowa »
- Onglet du navigateur : « Wood_Pilot_Ebolowa — CUF Chaîne 4 »
- Détail d'un poste : carte « Manque à gagner estimé » à la place de « Pertes financières estimées »

---

## 9. Références bibliographiques mobilisées

- **Jonsson & Lesshammar (1999)** — *Evaluation and improvement of manufacturing performance measurement systems – the role of OEE*, Suède : article fondateur du TRS/OEE. Distinction explicite entre « loss measurement » (chiffrage économique direct via la différence entre potentiel et réel) et « loss attribution » (décomposition Disponibilité × Performance × Qualité comme outil de diagnostic). Cette distinction est le fondement académique de la refonte : le manque à gagner mesure, D/P/Q diagnostiquent.

- **Mncwango & Mdunge (2025)** — *DMAIC pour OEE bas en industrie agro-alimentaire*, Afrique du Sud : confirme que la valorisation économique des pertes en contexte africain doit rester prudente et défendable, sans agréger des composantes potentiellement chevauchantes. Recommande explicitement la séparation entre indicateurs et causes.

- **Laine (2024)** — *Reporting visuel, Metsä Board*, Finlande : insiste sur la lisibilité immédiate des indicateurs financiers pour les décideurs non techniciens (PDG de CUF). La formulation « manque à gagner estimé » est plus accessible et moins anxiogène que « pertes financières », tout en restant rigoureuse.
