# Claude Agents & Project Configuration

## Project Overview

**projet-mem** = **Mémoire de Master 2** de BWAME EBENGUE CARLOS YVAN, ISABEE — Université d'Ebolowa.

**Titre :** Amélioration des performances de production de la chaîne 4 de la scierie industrielle CUF d'Ebolowa

**Contexte complet :** voir `contexte_memoire_CUF.md` à la racine du repo (TOUJOURS lire ce fichier en début de session).

### Ce que ce repo contient réellement
- **Documents du mémoire** : protocole, fiches de revue de littérature, méthodologie
- **Outils de collecte** : feuilles de relevé terrain, Google Forms
- **Outils d'analyse** : calcul TRS/OEE, Pareto, Ishikawa, capacité théorique
- **Tableau de bord** : Excel ou Looker Studio (3 vues : opérateur / chef production / PDG)
- **Infrastructure IA** : outils installés pour assister la rédaction et l'analyse

### Outils de développement disponibles (déjà installés)
- **Stack web** : Node.js 20, React + TypeScript, PostgreSQL + Prisma (disponible si besoin)
- **IA** : LightRAG (recherche sémantique), Claude AI service (analyse), LangChain, LangGraph, CrewAI
- **Automatisation** : n8n (workflows), MCP servers (context7, tavily, task-master, markdownify)
- **Package manager:** npm
- **Commit style:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`)
- **Testing:** Jest (unit/integration), Playwright (E2E)

---

## Tech Stack & Conventions

| Layer | Technology |
|---|---|
| Runtime | Node.js 20 LTS |
| Frontend | React 18 + TypeScript + Vite |
| Backend | Express.js + TypeScript |
| ORM | Prisma |
| Database | PostgreSQL 15 |
| Auth | JWT + bcrypt |
| Testing | Jest + Supertest + Playwright |
| Linting | ESLint + Prettier |
| CI/CD | GitHub Actions |

**Rules:**
- Never hardcode secrets — use environment variables
- Never commit on `main`/`master` directly — always use a feature branch + PR
- Every API route must have at least one integration test
- No personal data in logs (no journal content, no emails in plain text)

---

## Project File Structure

```
projet-mem/
├── src/
│   ├── api/          # Express routes & controllers
│   ├── services/     # Business logic
│   ├── models/       # Prisma models + helpers
│   ├── middleware/   # Auth, validation, error handling
│   └── utils/        # Shared utilities
├── frontend/
│   └── src/
│       ├── components/   # React UI components
│       ├── pages/        # Route-level pages
│       ├── hooks/        # Custom React hooks
│       └── store/        # State management
├── tests/
│   ├── unit/         # Jest unit tests
│   ├── integration/  # Supertest API tests
│   └── e2e/          # Playwright end-to-end tests
├── prisma/
│   ├── schema.prisma
│   └── migrations/
├── .claude/
│   ├── agents/       # AI agents (engineering + product + gsd)
│   ├── hooks/        # Automated hooks
│   └── settings.json
└── .github/workflows/ # CI/CD pipelines
```

---

## Development Commands

```bash
npm run dev          # Start dev server (backend + frontend)
npm test             # Run all tests
npm run test:unit    # Unit tests only
npm run test:e2e     # Playwright E2E tests
npm run lint         # ESLint check
npm run lint:fix     # Auto-fix lint issues
npm run build        # Production build
npm run db:migrate   # Run Prisma migrations
npm run db:seed      # Seed database with test data
npm run db:studio    # Open Prisma Studio
```

---

## Core Domain Concepts

| Concept | Description |
|---|---|
| **Entry** | A memoir entry — title, body (markdown), date, tags, mood |
| **User** | Account with email + hashed password, multi-tenant isolation |
| **Tag** | Categorization label attached to entries |
| **Draft/Published** | Entry lifecycle states |
| **Media** | Images/files attached to entries |
| **Timeline** | Chronological view of entries with filters |

**Privacy rules:** Each user can only access their own entries. Never expose entry content in error messages, logs, or API responses for other users.

---

## Active Agents

### Engineering

| Agent | File | Use for |
|---|---|---|
| Backend Architect | `.claude/agents/engineering/backend-architect.md` | API design, database schema, scalability |
| Frontend Developer | `.claude/agents/engineering/frontend-developer.md` | React components, UI/UX, accessibility |
| DevOps Automator | `.claude/agents/engineering/devops-automator.md` | CI/CD, deployment, infrastructure |
| Security Auditor | `.claude/agents/engineering/security-auditor.md` | OWASP, threat modeling, GDPR, deps audit |
| Test Engineer | `.claude/agents/engineering/test-engineer.md` | Jest, Playwright, test strategy, coverage |
| Data Modeler | `.claude/agents/engineering/data-modeler.md` | PostgreSQL schema, Prisma migrations, search |
| Performance Optimizer | `.claude/agents/engineering/performance-optimizer.md` | Profiling, bundle size, caching, Core Web Vitals |

### Product

| Agent | File | Use for |
|---|---|---|
| UX Writer | `.claude/agents/product/ux-writer.md` | Microcopy, error messages, onboarding |
| Code Reviewer | `.claude/agents/product/code-reviewer.md` | Structured PR review, conventions, maintainability |

---

## Hooks Reference

| Hook | Trigger | What it does |
|---|---|---|
| `session-start.sh` | Session open | Checks git health, creates dirs |
| `pre-bash.sh` | Before Bash | Blocks dangerous commands (rm -rf /, force push on main) |
| `pre-edit.sh` | Before Edit/Write | Snapshot of file, shows TODO/FIXME reminders |
| `post-edit.sh` | After Edit/Write | Auto-lint JS/TS, validates JSON, shellcheck for .sh |
| `post-bash.sh` | After Bash | npm audit after install, git commit summary |
| `stop.sh` | Session end | Warns about uncommitted changes, writes session.log |

---

## Working Agreements

1. **Never commit directly to `main` or `master`** — open a PR with a descriptive title
2. **No secrets in code** — use `.env` (gitignored) and environment variables
3. **Every API route needs a test** — at minimum one happy-path integration test
4. **No personal data in logs** — journal content, email, names must never appear in console logs
5. **Conventional Commits** — `feat: add timeline filter`, `fix: auth token expiry`, etc.
6. **Migrations are forward-only** — never modify existing migrations, always create new ones
7. **Keep PRs small** — max ~400 lines changed; split large features into phases

---

## Common Task Patterns

### Add a new API endpoint
1. Define route in `src/api/routes/`
2. Implement controller in `src/api/controllers/`
3. Add business logic in `src/services/`
4. Write integration test in `tests/integration/`
5. Update Prisma schema if needed → `npm run db:migrate`

### Add a React component
1. Create component in `frontend/src/components/`
2. Add Storybook story if complex
3. Write unit test with React Testing Library
4. Ensure keyboard navigation and ARIA labels

### Fix a security issue
1. Run `npm audit` and identify the package
2. Check if `npm audit fix` is safe (no breaking changes)
3. Use Security Auditor agent for threat assessment
4. Add regression test if applicable
5. Document in PR description

### Deploy to staging
1. Merge PR to `main`
2. GitHub Actions `deploy-staging.yml` triggers automatically
3. Run smoke tests on staging URL
4. Check logs in monitoring dashboard

---

**Source:** [aiagentskit/claude-agents-library](https://github.com/aiagentskit/claude-agents-library)

---

## Intégrations à faire (backlog)

| Outil | Repo | Quand intégrer | Pourquoi |
|---|---|---|---|
| **Arbor** | [penso/arbor](https://github.com/penso/arbor) | Quand plusieurs branches/worktrees actives en parallèle | Gestionnaire natif de worktrees Git + daemon multi-agents (Claude, Codex) + MCP server + terminal PTY intégré. Rust nightly requis — compiler quand le besoin de parallélisation devient réel. |
