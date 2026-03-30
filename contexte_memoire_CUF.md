# CONTEXTE MÉMOIRE M2 — CUF EBOLOWA
> Fichier de référence pour Claude Code et nouvelles sessions Claude
> Dernière mise à jour : mars 2026

---

## 1. IDENTITÉ DU PROJET

| Champ | Valeur |
|---|---|
| **Étudiant** | BWAME EBENGUE CARLOS YVAN |
| **Matricule** | 21ISFS0606 |
| **Niveau** | Master 2 |
| **Université** | Université d'Ebolowa |
| **École** | Institut Supérieur d'Agriculture, du Bois, de l'Eau et de l'Environnement (ISABEE) |
| **Département** | Foresterie, Sciences et Technologies du Bois |
| **Année académique** | 2025-2026 |
| **Encadreur académique** | Dr Tchiofo Rodine |
| **Conseiller** | Dr Manga (spécialiste chimie du bois) |
| **Site de stage** | Scierie industrielle CUF (Cameroon United Forests), Ebolowa, Cameroun |
| **Durée du stage** | 3 mois |

---

## 2. TITRE DU MÉMOIRE

> **Amélioration des performances de production de la chaîne 4 de la scierie industrielle CUF d'Ebolowa**

---

## 3. CONTEXTE TERRAIN

### L'entreprise CUF
- Grande scierie industrielle à Ebolowa, région du Sud-Cameroun
- 4 chaînes de sciage au total
- Produits : bois scié pour marché local et export (selon essences)
- PDG sans formation forestière → nécessité d'un tableau de bord exécutif accessible

### La chaîne 4
- **Flux de production** :
  - Parc à grumes → Scie de tête (plateaux) → Bicoupe (planches)
  - Planches défectueuses → Déligneuse / Ébouteuse / Dédoubleuse → Triage
  - Bonnes planches → Triage direct → Empilage
  - Toutes les machines sont dans le même atelier
- **Essences traitées** : Ayous, Azobé, Iroko, Movingui (4 essences principales)
- **Régime** : 2 postes de travail continus (~10 opérateurs/poste)
- **Objectif affiché** : 25 m³/poste (fixé empiriquement, sans base technique)
- **Production réelle** : 10 à 20 m³/poste (écart pouvant atteindre 60 %)
- **Machine centrale / goulot** : La bicoupe traite 100 % du bois
- **État du suivi à l'arrivée du stagiaire** : RIEN — aucune feuille de relevé, aucun tableau, aucun historique structuré

### Méthodologie recommandée par Dr Manga
1. Établir la capacité théorique à partir de la documentation constructeur
2. Mesurer toutes les opérations réelles par chronométrage systématique
3. Calculer l'écart capacité théorique / production réelle → identifier les pertes
4. Proposer des solutions concrètes avec simulation de l'impact

---

## 4. PROBLÈME DE RECHERCHE

La chaîne 4 de la scierie industrielle CUF d'Ebolowa présente un déficit de production persistant et non documenté. L'objectif de 25 m³ par poste n'est pas atteint : la production réelle se situe entre 10 et 20 m³, soit un écart pouvant dépasser 60 %. Cet écart est connu de l'encadrement mais n'a jamais été mesuré ni analysé. La valeur cible elle-même n'a pas de fondement technique — elle a été fixée empiriquement, sans référence aux capacités réelles des équipements. En l'absence de données structurées, de référence théorique établie et d'outils de diagnostic, il est impossible d'identifier les causes de ces pertes ni d'engager des actions d'amélioration sur des bases solides.

---

## 5. PROBLÉMATIQUE

> Dans quelle mesure l'absence de référence technique de production, de système de mesure et de diagnostic des pertes compromet-elle les performances de production de la chaîne 4 de la scierie industrielle CUF d'Ebolowa, et quelles actions correctives permettraient d'y remédier de façon durable ?

---

## 6. OBJECTIF GÉNÉRAL

Améliorer les performances de production de la chaîne 4 de la scierie industrielle CUF d'Ebolowa en établissant sa capacité théorique réelle, en mesurant sa production réelle, en diagnostiquant les causes de perte et en proposant des actions correctives mesurables accompagnées d'un outil de pilotage adapté.

---

## 7. OBJECTIFS SPÉCIFIQUES

1. Déterminer la capacité théorique réelle de la chaîne 4 à partir des caractéristiques techniques des machines et des essences transformées
2. Mesurer la production réelle de la chaîne 4 à travers un système de collecte de données mis en place sur le terrain
3. Évaluer l'écart entre la capacité théorique et la production réelle, calculer le TRS de la chaîne 4 et estimer le coût financier des pertes enregistrées
4. Identifier et hiérarchiser les causes responsables de cet écart à l'aide d'outils d'analyse appropriés
5. Proposer des actions correctives prioritaires et estimer les gains de production et les bénéfices financiers attendus de leur mise en œuvre
6. Concevoir un outil de pilotage adapté aux besoins des différents responsables de CUF pour assurer un suivi continu des performances de la chaîne 4

---

## 8. HYPOTHÈSES DE RECHERCHE

- **H1** : La capacité théorique réelle de la chaîne 4 est inférieure à l'objectif de 25 m³/poste actuellement fixé par CUF
- **H2** : Les pertes de performance sont principalement d'origine organisationnelle et opérationnelle, non liées à des défaillances techniques des équipements
- **H3** : En l'absence de système de mesure, le TRS réel de la chaîne 4 est inférieur à 60 %
- **H4** : Des actions correctives ciblées, sans investissement majeur en équipement, permettent d'améliorer significativement le TRS et de réduire les pertes financières

---

## 9. LIVRABLES PRÉVUS PAR OBJECTIF

| Objectif | Livrable minimal | Livrable envisageable |
|---|---|---|
| OS1 | Tableau de capacité théorique par machine et par essence + Abaque essence × diamètre → m³/heure | Comparaison avec benchmarks scieries africaines |
| OS2 | Base de données production réelle + feuille de relevé standardisée | Formulaire numérique sur téléphone (Google Forms) |
| OS3 | Fichier Excel TRS automatique + rapport mensuel + chiffrage pertes en FCFA | Tableau de bord TRS dynamique vert/orange/rouge |
| OS4 | Pareto des arrêts + Ishikawa causes racines | Matrice de criticité + VSM (Value Stream Mapping) |
| OS5 | Plan d'actions correctives avec priorisation et projection financière | Simulation Excel impact sur TRS + ROI par action |
| OS6 | Tableau de bord Excel opérationnel (vue opérateur + chef production + PDG) + guide utilisation | Google Looker Studio avec 3 vues différenciées |

### Décision sur l'outil de suivi
- Pas d'application développée from scratch (trop long, maintenance impossible)
- Option retenue : **Google Looker Studio ou Excel** avec 3 vues distinctes
- Décision finale entre les deux : à trancher ultérieurement

---

## 10. REVUE DE LITTÉRATURE — ÉTAT D'AVANCEMENT

### Thèmes traités (tous complétés avec fiches Word)

| Thème | Sujet | Nb articles | Statut |
|---|---|---|---|
| Thème 1 | Méthodes de collecte de données | 4 | ✅ Fiches + Word |
| Thème 2 | TRS/OEE — indicateurs de performance | 5 | ✅ Fiches + Word |
| Thème 3 | Optimisation du rendement matière | 4 | ✅ Fiches + Word |
| Thème 4 | Méthodes de collecte terrain | 4 | ✅ Fiches + Word |
| Thème 5 | Scie à ruban / bicoupe | 4 | ✅ Fiches + Word |
| Thème 6 reformulé | Pilotage performance + tableaux de bord | 8 | ✅ Fiches + Word |
| Thème 7 | Scieries africaines et tropicales | 10 | ✅ Fiches + Word |

### Articles clés Thème 6 reformulé (les 8 retenus)

| Code | Référence | Note |
|---|---|---|
| A.5 | Jaouane (2022) — Tableau de bord, Général Emballage, Algérie | ⭐⭐⭐ |
| B.1 | Laine (2024) — Reporting visuel, Metsä Board, Finlande | ⭐⭐⭐ |
| C.1 | Jonsson & Lesshammar (1999) — OEE fondateur, Suède | ⭐⭐⭐ |
| C.3 | Mncwango & Mdunge (2025) — DMAIC, OEE bas, Afrique du Sud | ⭐⭐⭐ |
| C.4 | Novochadlo & Paladini (2024) — OEE temps réel, Brésil | ⭐⭐ |
| D.4 | Koc & Eryuruk (2025) — OEE industrie textile, Turquie | ⭐⭐⭐ |
| B.4 | Steenkamp et al. (2017) — VMS open-source, Afrique du Sud | ⭐⭐ |
| E.3 | Kankkunen & Holopainen (2024) — Daily management, UPM Plywood | ⭐⭐ |

### Articles clés Thème 7 (scieries africaines)
- Karsenty (2021) : rendement matière 35% Afrique centrale
- Ngobi et al. (2023) : rendement 32% Ouganda, efficience 26,6%
- Danwé, Bindzi & Meva'a (2012) : scieries camerounaises, rendement 30-36%, décisions de coupe = levier principal
- Cheboiwo, Macharia & Kiprop (2023) : Kenya, scieries à <1/3 capacité optimale
- Benchmark international : 60% et plus

### Données secteur bois Cameroun (vérifiées)
- Contribution PIB : 3,8% en 2022 (Banque mondiale, 2024)
- 3ème source d'exportation après cacao et hydrocarbures
- 314,8 milliards FCFA d'exportations forestières en 2022
- Bois scié : 14-16% des exportations hors hydrocarbures
- 45 000 emplois dont 22 000 dans le secteur informel
- 1er exportateur mondial de sapelli et iroko sciés (737 000 tonnes en 2022)
- Politique : interdiction progressive des exportations de grumes

---

## 11. DOCUMENTS WORD GÉNÉRÉS

| Fichier | Contenu |
|---|---|
| `fiches_nouveaux_articles_CUF.docx` | 8 fiches complètes Thème 6 reformulé + carte des contributions |
| `protocole_introduction_CUF.docx` | Page de garde ISABEE + Introduction complète (contexte, problème, problématique, objectifs, hypothèses) |

---

## 12. PRINCIPES DE TRAVAIL ÉTABLIS

### Style de rédaction
- Langue simple, précise, directe — style qui ressemble à la voix de l'étudiant
- Ton académique + terrain combinés
- Pas de listes à tirets dans les textes rédigés : phrases complètes et connecteurs logiques
- Citations en mode APA (auteur, année)
- Jamais de langage IA détectable

### Règles de la revue de littérature
- "quiz" → QCM sur le dernier article analysé (toujours suivi d'un encadré À RETENIR)
- "suivant" → passer directement au prochain article sans quiz
- Chaque fiche contient : orientation (3 cadres), référence complète, contexte, idée centrale, méthode détaillée avec parallèle CUF, résultats, contributions, limites, verdict, À RETENIR
- Lire l'article en entier avant de produire la fiche

### Approche collaborative
- Brainstorming obligatoire avant toute rédaction
- Claude propose, l'étudiant valide ou corrige
- Claude doit être honnête et pousser ses positions même si l'étudiant n'est pas d'accord

---

## 13. PROCHAINES ÉTAPES

- [ ] Générer le Word final du protocole avec le texte révisé (style ingénieur, sans tirets)
- [ ] Rédiger la section Méthodologie du protocole
- [ ] Collecte terrain : feuilles de relevé, chronométrage, mesures bicoupe
- [ ] Récupérer fiches techniques bicoupe et scie de tête
- [ ] Récupérer prix de vente du m³ par essence chez CUF
- [ ] Décision finale : Looker Studio ou Excel pour le tableau de bord
