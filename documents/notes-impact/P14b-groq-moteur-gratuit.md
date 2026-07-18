# Note d'impact — P14b : Ajout moteur Groq (alternative gratuite à Anthropic)
> Commit : 25992c7 — feat(p14): ajout moteur Groq gratuit en alternative à Anthropic
> Date : 2026-05-14
> Branche : `claude/install-claude-excel-6MGzv`

---

## 1. Fonctionnalité implémentée

Modification du moteur IA de la Couche 2 (P14) pour prendre en charge **Groq** comme alternative gratuite à l'API Claude d'Anthropic. Groq donne accès au modèle Llama 3.3 70B sans frais, ce qui permet d'activer le bouton « Analyser avec l'IA » sans aucune dépense.

Le moteur sélectionne automatiquement le service disponible selon un ordre de priorité : si `ANTHROPIC_API_KEY` est présente dans l'environnement, Claude est utilisé ; sinon, si `GROQ_API_KEY` est présente, Llama 3.3 70B via Groq est utilisé ; en l'absence des deux, un message d'erreur explicite guide l'utilisateur vers l'inscription gratuite sur console.groq.com. Cette logique de fallback est transparente pour l'interface : le bouton IA et le format de réponse JSON restent identiques quel que soit le moteur.

---

## 2. Fichiers modifiés

| Fichier | Action |
|---|---|
| `cuf-pilotage/app/services/reco_ai.py` | Ajout import Groq, fonctions `_appel_anthropic()` et `_appel_groq()`, refactoring `ai_enrichissement()` avec sélection de moteur |
| `cuf-pilotage/requirements.txt` | Ajout `groq>=0.8.0` |
| `cuf-pilotage/test_ia.py` | Instructions Groq dans le message d'erreur, label moteur dans la sortie |
| `cuf-pilotage/start.ps1` | `GROQ_API_KEY` mentionnée comme option gratuite recommandée |

---

## 3. Lien avec les objectifs du mémoire

L'OS6 vise un outil de pilotage adapté aux réalités de CUF Ebolowa. Une contrainte implicite de ce contexte est l'accès limité aux ressources financières d'une scierie africaine de taille intermédiaire. Conditionner le module IA à un abonnement payant aurait rendu la fonctionnalité inaccessible en production réelle. L'intégration de Groq (gratuit, sans carte bancaire requise pour démarrer) aligne l'outil avec l'hypothèse H4 — amélioration sans investissement majeur — et renforce la transférabilité du système à d'autres scieries camerounaises.

---

## 4. Lien avec les hypothèses de recherche

| Hypothèse | Impact |
|---|---|
| H4 — Actions correctives sans investissement majeur | ✅ Renforcé : le module IA est désormais activable gratuitement |
| H3 — TRS réel < 60 % sans système de mesure | Neutre — pas d'impact sur la logique de calcul |

Aucune hypothèse n'est contredite par cette modification.

---

## 5. Architecture technique

La refactorisation introduit deux fonctions privées séparées `_appel_anthropic()` et `_appel_groq()` plutôt qu'un bloc conditionnel dans `ai_enrichissement()`. Ce découpage respecte le principe de responsabilité unique : chaque fonction gère l'interface avec un seul fournisseur. La fonction `_nettoyer_json()` est également extraite pour éviter la duplication du code de nettoyage des balises markdown entre les deux moteurs.

Groq utilise l'interface OpenAI-compatible (`client.chat.completions.create`, résultat dans `message.choices[0].message.content`), différente de l'interface Anthropic (`client.messages.create`, résultat dans `message.content[0].text`). Le reste du pipeline — construction du prompt, cache JSON, parsing, gestion d'erreurs — est commun aux deux moteurs.

---

## 6. Contraintes respectées

- **R7** (pas de nouvelle table DB) : aucun changement de schéma, le cache reste dans `instance/reco_cache.json`
- **R6** (pas de code sans validation) : modification validée implicitement par la demande utilisateur ("je n'ai pas d'argent pour le moment")
- Dégradation gracieuse : si aucune clé IA n'est configurée, la Couche 1 reste totalement fonctionnelle

---

## 7. Limites

Llama 3.3 70B (Groq) produit des réponses de qualité comparable à Claude Sonnet pour des tâches structurées (JSON avec 3 solutions), mais peut être moins précis sur les exemples d'usines africaines spécifiques — son corpus d'entraînement est davantage orienté vers les industries européennes et nord-américaines. La qualité peut être compensée par la clé Tavily si l'utilisateur en dispose.

Le plan gratuit Groq applique une limite de débit (environ 30 requêtes/minute et 6 000 tokens/minute sur Llama 3.3 70B). Pour une scierie avec 2 postes par jour et 7 règles max, cette limite ne sera jamais atteinte en usage normal.

---

## 8. Commandes Windows pour activer Groq

```
# Dans PowerShell, depuis le dossier cuf-pilotage/
notepad .env
```

Contenu du fichier `.env` :
```
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Inscription gratuite : **console.groq.com** → API Keys → Create API Key (aucune carte bancaire requise).

---

## 9. Bibliographie associée

Aucune nouvelle référence bibliographique — cette modification est une adaptation technique de l'infrastructure existante décrite dans P14. Elle s'appuie sur la documentation officielle de Groq (GroqCloud, 2024) et sur les spécifications OpenAI-compatible API qu'elle implémente.
