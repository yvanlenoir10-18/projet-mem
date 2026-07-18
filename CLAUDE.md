# CLAUDE.md — App CUF (assako) — contexte verrouillé

> Lu automatiquement par Claude Code au début de chaque session. Contient le noyau métier verrouillé. Les détails de développement vivent dans le skill `brief-app-cuf` et le protocole `vibe-coding`.

## Projet
Application desktop de pilotage de la production de la chaîne 4 — scierie industrielle CUF, Ebolowa. Utilisée par **BWAME EBENGUE CARLOS YVAN** (analyse, export) et les **opérateurs** (saisie au niveau du poste). Soutient le mémoire M2 « Amélioration des performances de production de la chaîne 4 ».

## ⚠️ Règles métier verrouillées — ne jamais inventer, confondre ou approximer
- **Objectif officiel = 25 m³/poste-équipe** (un quart de 8 h ; confirmé 2× par le chef — mémoire §3.1.1.2). Production réelle ≈ **14,55 m³/poste = 58 %** d'atteinte. Ne JAMAIS présenter les 25 m³ comme techniquement fondés ; ne pas confondre production (débité) et conforme.
- Deux postes : matin **6h–14h**, soir **14h–23h**. Environ **10 opérateurs/poste**.
- Ordre exact des machines : **Scie de tête → Bicoupe → Scie de tronçonnage**.
  - Bicoupe : chariot en va-et-vient (coupe à l'aller et au retour ; plateaux par passes successives).
  - Scie de tronçonnage : délignage, éboutage, dédoublage.
- Lames : préventif **toutes les 2 h** ; immédiat à tout **changement d'essence tendre↔dure**.
- Essences (4 seulement) : **Ayous, Bilinga, Iroko, Movingui**. (Bilinga remplace Azobé depuis le 2026-07-10 ; Azobé, minoritaire dans les relevés, bascule dans « Autre ».)
- Point de comptage terrain : **passage fixe AVANT la bicoupe**.
- Benchmarks : Cameroun 60 % (cible) ; pertes scieries 30–36 % ; Afrique centrale ~35 % ; Ouganda ~32 % ; Nigeria 46–58 %.

## Cadre du mémoire (cohérence app <-> mémoire)
4 OS. **OS1** = capacité théorique -> production réelle -> écart + TRS. OS2/OS3/OS4 = anciens OS4/OS5/OS6. Fil conducteur **DMAIC**. Hypothèses **H1–H4**.

## ⚠️ Règles app verrouillées
- Cible : **.exe Windows, 100 % hors ligne, stockage local uniquement**.
- UI **en français**, éléments **larges et tactiles** (saisie opérateur sur le terrain).
- Double usage : BWAME (analyse/export) vs opérateurs (saisie par poste).
- **Code existant** : lire l'existant AVANT toute modification. Ne jamais repartir de zéro.

## Méthode (protocole vibe-coding)
Cadrage avant code, une feature à la fois, screenshots pour l'UI, notes.md tenu à jour, **git commit avant tout changement**.

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
| ------ | ---------- |
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
