# Note d'impact mémoire — P6-F1 : Décomposition TRS en m³ perdus (cascade D × P × Q)
**Commit :** `7b3fb37` — `feat(chef): P6-F1 — décomposition TRS en m³ perdus (cascade D × P × Q)`
**Date :** 2026-05-04
**Fichiers modifiés :** `app/services/trs.py` (+25 lignes) · `app/routes/dashboard.py` (+38 lignes) · `app/templates/chef/dashboard.html` (+65 lignes)

---

## 1. Ce qui a été implémenté

Ajout dans le dashboard Chef d'une carte « Décomposition des pertes (cascade D × P × Q) » qui exprime les pertes de production en mètres cubes sur la capacité théorique de la période sélectionnée.

**Trois éléments techniques :**

| Élément | Description |
|---|---|
| Helper `decompose_dpq(equipe)` (`trs.py`) | Fonction pure (sans mutation) retournant le triplet (D, P, Q) en proportions 0-1. Utilise les valeurs stockées sur l'équipe si présentes, sinon recalcule à partir des arrêts et volumes. Découplée de `calcule_trs()` qui mute l'objet. |
| Calcul cascade (`vue_chef`) | `cap_par_poste = capacite_h × duree_poste/60 = 12.5 m³`, puis pour chaque équipe accumule `perte_D = (1−D)·cap`, `perte_P = D·(1−P)·cap`, `perte_Q = D·P·(1−Q)·cap`. La somme `perte_D + perte_P + perte_Q + produit ≡ cap_total` est garantie par construction algébrique. |
| Card visuelle (template) | Barre Bootstrap 5 « stacked » à 4 segments colorés + 4 mini-cards détail (m³ et % par composante) + note explicative sur la nature multiplicative de la cascade. |

**Code couleur retenu :**

| Segment | Couleur | Sémantique |
|---|---|---|
| Produit conforme | vert (`bg-success`) | Ce qui a réellement abouti (D×P×Q × cap) |
| Perte D | rouge (`bg-danger`) | Arrêts machine (non planifiés ou non) |
| Perte P | jaune (`bg-warning`) | Sous-cadence sur le temps utile |
| Perte Q | bleu (`bg-info`) | Déclassé + déchets |

---

## 2. Lien avec les objectifs du mémoire

F1 répond à **OS3** (calculer le TRS et estimer le coût des pertes) et à **OS6** (outil de pilotage adapté).

L'apport spécifique de F1 par rapport au TRS affiché en pourcentage : un TRS de 60 % ne dit pas combien de m³ ont été perdus, ni *où* ils se sont perdus. La cascade D × P × Q en m³ rend visible la décomposition exacte — un Chef Scierie peut lire « j'ai perdu 5,2 m³ par arrêts et 6,4 m³ par sous-cadence ce mois-ci », ce qui est immédiatement actionnable, contrairement à « TRS = 66 % ».

Cette visualisation matérialise donc la transition pédagogique du **diagnostic statistique** (TRS %) vers la **prise de décision opérationnelle** (m³ → FCFA → action correctrice).

---

## 3. Données et calculs mobilisés

**Identité algébrique fondatrice (Jonsson & Lesshammar, 1999) :**

```
TRS = D × P × Q

Décomposition en parts complémentaires de la capacité totale :
  produit  = D × P × Q × cap
  perte_D  = (1 − D)         × cap
  perte_P  = D × (1 − P)     × cap
  perte_Q  = D × P × (1 − Q) × cap

  perte_D + perte_P + perte_Q + produit ≡ cap
```

**Vérification empirique (4 postes, 14-15 avril 2026, données locales) :**

| Composante | Valeur |
|---|---|
| Cap théorique | 50,00 m³ (4 postes × 12,5 m³) |
| TRS moyen | 66,4 % |
| Perte D | 5,20 m³ (10,4 %) |
| Perte P | 6,41 m³ (12,8 %) |
| Perte Q | 5,18 m³ (10,4 %) |
| Produit | 33,21 m³ (66,4 %) |
| **Somme** | **50,00 m³ ✓** |

La somme égale exactement la capacité théorique au centième près — l'identité algébrique est respectée dans l'implémentation.

**Capacité unitaire :** `capacite_h × (duree_poste/60) = 1.5625 × 8 = 12,5 m³/poste`. Cette valeur correspond à l'objectif paramétré actuellement (12,5 m³, valeur provisoire V1). Le mémoire précisera plus tard la capacité théorique réelle issue des fiches techniques constructeur (OS1).

---

## 4. Hypothèses testées ou confirmées

**H1 (capacité théorique réelle inférieure à 25 m³/poste) :** F1 utilise la capacité paramétrée (12,5 m³) qui est elle-même inférieure à l'objectif affiché de 25 m³/poste. Tant que la fiche technique constructeur n'est pas intégrée, F1 reflète l'hypothèse provisoire ; quand le paramètre `objectif_m3` sera mis à jour avec la valeur OS1, F1 s'ajustera automatiquement (le calcul lit le paramètre à chaque requête).

**H2 (pertes principalement organisationnelles) :** F1 ne tranche pas H2 directement, mais combinée avec la matrice F2 (machine × catégorie), elle permet de relier la perte D à la nature des arrêts. Sur les données locales actuelles, perte D et perte P sont du même ordre de grandeur, ce qui suggère que les deux leviers (réduire les arrêts ET améliorer la cadence) doivent être actionnés conjointement.

**H3 (TRS réel < 60 %) :** sur les données locales, TRS = 66,4 % — au-dessus du seuil. Mais ce sont des données démo calibrées favorablement. Sur les données terrain réelles, F1 fournira une décomposition immédiate du TRS observé sans recalcul manuel.

**Aucune contradiction avec les hypothèses existantes.**

---

## 5. Ce que ce module permet de montrer dans le mémoire

- La barre stacked à 4 segments est la **traduction visuelle directe de l'identité TRS = D × P × Q**. Elle évite l'erreur cognitive courante consistant à présenter D, P, Q comme trois barres de pourcentage juxtaposées (qui suggérerait une additivité fausse).
- La séparation produit/perte rend l'**enjeu financier visible sans calcul FCFA explicite** : 5,2 m³ d'Iroko à 110 000 FCFA/m³ représentent immédiatement 572 000 FCFA — le Chef peut faire la conversion mentale.
- La fonction `decompose_dpq()` extraite comme helper pur est réutilisable par F3 (calculateur de potentiel) qui aura besoin du même triplet sans muter les équipes. C'est une **décision d'architecture qui anticipe les phases suivantes** sans dette technique.
- La cohérence des conventions visuelles est préservée : rouge/jaune/vert pour les niveaux de criticité, mêmes seuils que F2 (matrice criticité) et que le KPI TRS principal.

---

## 6. Limites actuelles

- **Capacité unitaire fixe :** F1 utilise `capacite_h` constant (1,5625 m³/h) pour toutes les essences. En réalité, les essences denses (Azobé) sciées plus lentement que les tendres (Ayous) auraient des capacités différentes. Différé jusqu'à OS1 finalisé (fiches constructeur + abaque essence × diamètre).
- **Performance plafonnée à 100 % :** si une équipe produit plus que la capacité théorique (vol_sorti > vol_theorique), `decompose_dpq` clampe P à 1.0 — comme `calcule_trs`. Ce choix évite un TRS > 100 % mais masque les cas où la capacité paramétrée est sous-estimée. Acceptable tant que la valeur 12,5 m³ reste provisoire.
- **Conversion en FCFA non affichée dans la card F1 :** la décomposition est en m³ uniquement. La conversion FCFA reste accessible via la page « Analyse des pertes » (`/dashboard/pertes`). Choix volontaire : éviter la surcharge cognitive sur le dashboard Chef et garder la vue financière dans une page dédiée.
- **Pas de drill-down par essence :** F1 agrège toutes les essences. Une décomposition par essence (« perte D pour Iroko vs Ayous ») serait pertinente mais complexifierait la lecture. Différé.

---

## 7. Vérification de cohérence avec les notes précédentes

La note `P6-F2-matrice-criticite.md` annonçait F1 comme prochaine étape — F1 est livré conformément à la critique utilisateur (« m³ losses multiplicative cascade, NOT % bars additive misrepresentation »). Le choix d'une barre stacked à 4 segments respecte cette contrainte : aucun pourcentage isolé n'est présenté comme une perte indépendante.

La note `P5-dashboard-pdg-enrichi.md` documentait que le PDG dispose d'un KPI TRS global et d'une perte FCFA totale. F1 enrichit le dashboard Chef avec une vue intermédiaire entre ces deux niveaux : ni le TRS brut, ni la perte FCFA, mais la **décomposition physique en m³** qui sert de pont entre les deux.

La note `00-cadrage-global-P1-P2-P3.md` rappelait que `calcule_trs()` mute l'équipe (effets de bord). F1 introduit volontairement `decompose_dpq()` comme alternative pure pour les contextes de lecture seule (dashboards), ce qui clarifie la séparation lecture/écriture sans casser le code existant.

Aucune contradiction avec les notes précédentes.

---

## 8. Références bibliographiques mobilisées implicitement

| Référence | Lien |
|---|---|
| Jonsson & Lesshammar (1999) | Identité fondatrice TRS = D × P × Q et décomposition cascadée des pertes — F1 traduit cette identité en visualisation directe |
| Mncwango & Mdunge (2025) | DMAIC étape « Measure » : quantifier les pertes par catégorie pour orienter les actions de l'étape « Improve » — la décomposition m³ est la mesure attendue |
| Laine (2024) | Reporting visuel pour décideurs opérationnels : barre stacked = format à un seul coup d'œil, sans légende complexe |
| Karsenty (2021) | Benchmarks africains de rendement matière (35 % Afrique centrale) : la perte Q affichée en m³ permet la comparaison directe avec ces benchmarks sans conversion mentale |

---

## 9. Prochaines étapes

- **F5 — Scorecard 7 jours calendaire (lun–sam)** : grille semaine état TRS % / ⏳ brouillon / — absent.
- **F4 — Score régularité CV** : coefficient de variation du TRS, affiché uniquement si n ≥ 10 postes.
- **F3 — Calculateur potentiel gain FCFA** : slider cible TRS (défaut 70 %, modifiable). Utilisera `decompose_dpq()` pour estimer le gain m³ et FCFA si chaque composante atteint la cible.
- **F6 — Filtre date partagé (refactoring DRY)** : helper commun Chef/PDG pour la sélection de période.
- **OS1 (fiches techniques) :** quand la capacité réelle par essence sera intégrée dans `Parametre`, F1 affichera automatiquement les nouvelles valeurs sans modification de code (lecture du paramètre à chaque requête).
- **Windows :** synchronisation git `reset --hard origin/claude/install-claude-excel-6MGzv` pour récupérer P6-F1 et F2.
