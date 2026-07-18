# P5 — Dashboard Chef : passer de l'agrégateur à l'aiguilleur

> Cadrage conceptuel. **Aucun code à écrire en P4.** À implémenter en P5 après livraison complète de P4.
> Issu de la conversation utilisateur du 2026-06-07 — verbatim conservé en section 1.

---

## 1. Insatisfaction exprimée — verbatim utilisateur

> « Je ne suis pas totalement satisfait du tableau de bord actuel. Ce que j'aime : il est mieux organisé qu'avant, il y a une meilleure logique visuelle, on sent qu'il commence à structurer le pilotage, les blocs sont plus cohérents qu'au début.
>
> Mais mon problème est le suivant : le tableau de bord affiche encore trop de choses. J'ai l'impression qu'il contient presque tout, au lieu de me montrer uniquement les éléments vraiment pertinents.
>
> Pour moi, le tableau de bord Chef ne doit pas être une page où l'on empile les KPI, les alertes, les fiches, les machines, les prescriptions, les décisions, les actions, les détails. Il doit plutôt être une porte d'entrée intelligente.
>
> Sa mission devrait être :
> 1. montrer les priorités du moment ;
> 2. dire au chef ce qu'il doit regarder maintenant ;
> 3. signaler les anomalies importantes ;
> 4. résumer l'état de production ;
> 5. renvoyer vers les pages détaillées appropriées.
>
> Le dashboard doit montrer les signaux prioritaires et orienter vers les bons écrans. Il ne doit pas essayer de remplacer toutes les pages. »

---

## 2. Principe directeur — phrase-clé à graver

> **« Le dashboard ne montre pas tout. Il montre ce qui mérite l'attention et renvoie vers le bon endroit. »**

C'est la phrase à coller dans le commit de P5 et dans la section UX du mémoire.

---

## 3. Trois exemples canoniques fournis par l'utilisateur

Ces trois exemples cadrent le pattern attendu pour **chaque carte du dashboard** : un signal court + un bouton qui renvoie.

### Exemple 1 — Machine critique

**❌ Aujourd'hui** : le dashboard affiche le diagnostic machine entier (graphique arrêts, top causes, durée cumulée, tendance, table machines, etc.).

**✅ Demain (P5)** :
```
┌──────────────────────────────────────┐
│ ⚠ Bicoupe critique                   │
│ 4h30 d'arrêts cette semaine          │
│           [Voir diagnostic machine →]│
└──────────────────────────────────────┘
```
→ clic = navigation vers la page **Diagnostic / Machines**.

### Exemple 2 — Fiche incohérente

**❌ Aujourd'hui** : le dashboard affiche le bloc Traçabilité avec compteurs, ratios, détail anomalies R1–R8.

**✅ Demain (P5)** :
```
┌──────────────────────────────────────┐
│ ⚠ 1 fiche bloquante à corriger       │
│           [Contrôler les fiches    →]│
└──────────────────────────────────────┘
```
→ clic = navigation vers **Fiches à contrôler** (déjà filtrée sur les bloquantes).

### Exemple 3 — Prescription urgente

**❌ Aujourd'hui** : le dashboard affiche un widget top recommandations avec titres + sous-textes tronqués (loop sur N prescriptions).

**✅ Demain (P5)** :
```
┌──────────────────────────────────────┐
│ ! 1 prescription urgente             │
│           [Voir la prescription    →]│
└──────────────────────────────────────┘
```
→ clic = navigation vers **Prescriptions de pilotage** (déjà filtrée ou ancrée sur la prioritaire).

---

## 4. Conséquences design — règles à appliquer à chaque carte

### R-DASH-1 : signal + verbe + lien
Toute carte du dashboard doit contenir, dans cet ordre :
1. Un **signal** court (1 ligne, chiffre ou alerte)
2. Un **verbe d'action** (« Voir », « Contrôler », « Diagnostiquer », « Décider »)
3. Un **lien** vers la page où l'action se fait

Si une carte n'a pas de verbe d'action, elle n'a pas sa place sur le dashboard → elle migre vers la page concernée.

### R-DASH-2 : pas de duplication de contenu
Si une information est déjà disponible sur une page dédiée, le dashboard n'en montre qu'un **résumé déclencheur**, jamais le contenu détaillé.
- Pareto complet → page Causes d'arrêts (pas dashboard)
- Décomposition D×P×Q → page Pertes financières (pas dashboard)
- Table essences → page Qualité (pas dashboard)
- Matrice arrêts → page Diagnostic / Machines (pas dashboard)
- Scorecard semaine → page Production (pas dashboard)
- Graphiques TRS → page Performance (pas dashboard)
- Simulateur de gain → page Pertes financières (pas dashboard)

### R-DASH-3 : silencieux quand tout va bien
Si la Bicoupe n'est pas critique → pas de carte machine.
Si aucune fiche n'est bloquante → pas de carte fiches.
Si aucune prescription n'est urgente → pas de carte prescription.

Le dashboard ne doit afficher **que ce qui mérite attention**. Les cartes apparaissent et disparaissent selon les signaux.

### R-DASH-4 : un seul niveau de profondeur
Le dashboard montre l'altitude 1 (le signal). Le clic emmène à l'altitude 2 (la page de diagnostic). Jamais d'altitude intermédiaire dans le dashboard lui-même.

---

## 5. Structure cible du dashboard Chef en P5

```
╔══════════════════════════════════════════════════════╗
║  VERDICT GLOBAL                                      ║
║  ● VERT / ORANGE / ROUGE — résumé une ligne          ║
╠══════════════════════════════════════════════════════╣
║  TRS du moment · Manque à gagner · État production   ║
║  (compact, lecture immédiate)                        ║
╠══════════════════════════════════════════════════════╣
║  CARTES DE PRIORITÉ (dynamiques, n'apparaissent     ║
║  que si signal actif)                                ║
║  ┌────────────────────────────────────────────────┐  ║
║  │ ⚠ Bicoupe critique                            │  ║
║  │   [Voir diagnostic machine →]                 │  ║
║  └────────────────────────────────────────────────┘  ║
║  ┌────────────────────────────────────────────────┐  ║
║  │ ⚠ 1 fiche bloquante à corriger                │  ║
║  │   [Contrôler les fiches →]                    │  ║
║  └────────────────────────────────────────────────┘  ║
║  ┌────────────────────────────────────────────────┐  ║
║  │ ! 1 prescription urgente                      │  ║
║  │   [Voir la prescription →]                    │  ║
║  └────────────────────────────────────────────────┘  ║
║  ┌────────────────────────────────────────────────┐  ║
║  │ ! 2 décisions en attente de vérification      │  ║
║  │   [Suivre les décisions →]                    │  ║
║  └────────────────────────────────────────────────┘  ║
╠══════════════════════════════════════════════════════╣
║  AIGUILLAGE (toujours visible, en pied de page)     ║
║  → Fiches à contrôler                                ║
║  → Diagnostic (Production / Qualité / Machines)      ║
║  → Prescriptions de pilotage                         ║
║  → Décisions de pilotage                             ║
╚══════════════════════════════════════════════════════╝
```

Tout le reste — D×P×Q, scorecard, graphique TRS, matrice, simulateur, recommandations détaillées, traçabilité complète, anomalies par règle R1–R8, etc. — **n'est plus sur le dashboard**. Ces contenus retournent sur leurs pages dédiées.

---

## 6. Pages cibles d'aiguillage (rappel — décidées avec Codex 2026-06-07)

P5 livre en même temps la **navigation à 5 entrées** convenue avec Codex :

1. **Aujourd'hui** (= ce dashboard aiguilleur)
2. **Fiches à contrôler**
3. **Diagnostic** (groupant Production · Qualité · Machines · Causes d'arrêts · Résolution Ishikawa)
4. **Prescriptions de pilotage**
5. **Décisions de pilotage**

Le dashboard P5 aiguille **vers ces 5 entrées**. Chaque carte de priorité a un lien qui pointe vers l'une d'elles (ou vers un de leurs sous-écrans).

---

## 7. Critères d'acceptation P5 (à valider plus tard)

- [ ] Le dashboard tient **sans scroll** sur un écran 1366×768 (laptop terrain)
- [ ] Si tous les signaux sont verts → seul le bloc verdict + état production reste, **aucune carte de priorité** n'apparaît
- [ ] Aucun contenu de la zone « cartes de priorité » n'est dupliqué sur une autre page (test : chaque texte du dashboard doit être unique ou être un résumé strict d'une info disponible ailleurs)
- [ ] Chaque carte de priorité a **exactement un bouton** menant à une page dédiée
- [ ] Les sections suivantes ont été **retirées** du dashboard et n'existent plus que sur leurs pages dédiées :
  - Décomposition D×P×Q détaillée
  - Scorecard semaine
  - Graphique TRS
  - Tableau essences
  - Matrice arrêts
  - Simulateur de gain
  - Anomalies de saisie détaillées (R1–R8)
  - Boucle Lean (compteurs détaillés)
- [ ] Le test des 10 secondes passe : un chef qui ouvre l'app sait en moins de 10 s s'il doit agir et où aller
- [ ] Le smoke test 16/16 reste vert

---

## 8. Articulation avec le reste de P5

Ce cadrage s'ajoute aux travaux P5 déjà identifiés :
- Source B (bibliothèque de contre-mesures par catégorie d'arrêt)
- Boucle avant/après sur indicateur (section Vérification des prescriptions)
- Bilan FCFA évité sur les Décisions
- Score FCFA × récurrence pour le tri des prescriptions
- Persistance `reco_code` dans `nouvelle_action_chef()`
- Navigation refactorée à 5 entrées avec groupe Diagnostic

**Ordre d'attaque suggéré pour P5** :
1. Navigation à 5 entrées (pose le squelette d'aiguillage)
2. Refonte dashboard aiguilleur (utilise les nouvelles destinations)
3. Source B + score dynamique (enrichit les prescriptions vers lesquelles on aiguille)
4. Boucle avant/après + bilan FCFA (enrichit la vérification des décisions)

---

## 9. Ce qui n'est PAS dans ce cadrage

- Aucune décision sur le **style visuel** des cartes de priorité (couleurs, icônes, animations) — à designer en début de P5
- Aucune décision sur le **comportement mobile** (cartes empilées vs grille) — à designer en début de P5
- Aucune décision sur la **hiérarchisation entre cartes** quand plusieurs signaux sont actifs en même temps (ordre par gravité ? par FCFA ? par urgence temporelle ?) — à débattre en début de P5
- Aucune décision sur les seuils qui font apparaître/disparaître chaque carte — à dériver des règles de prescription existantes

Tout ça sera tranché au lancement de P5, après livraison complète de P4 et validation Windows.
