#!/bin/bash
# Hook: Stop
# Avertit des changements non commités, log de session

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LOG_FILE="$PROJECT_DIR/.claude/session.log"

# Vérifier les changements non commités
cd "$PROJECT_DIR" 2>/dev/null || exit 0

UNCOMMITTED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
if [ "$UNCOMMITTED" -gt 0 ]; then
  echo ""
  echo "📦 $UNCOMMITTED fichier(s) non commité(s) — auto-commit en cours..."
  git add -A 2>/dev/null
  if ! git diff --cached --quiet 2>/dev/null; then
    git commit -m "chore(auto): save session work $(date '+%Y-%m-%d %H:%M')" 2>/dev/null && \
      echo "   ✅ Commit créé. Pensez à le renommer avec un message descriptif." || \
      echo "   ⚠️  Auto-commit échoué — commitez manuellement."
  fi
fi

# Log de session
mkdir -p "$(dirname "$LOG_FILE")"
{
  echo "--- Session $(date '+%Y-%m-%d %H:%M:%S') ---"
  echo "Branche : $(git branch --show-current 2>/dev/null || echo 'inconnue')"
  echo "Dernier commit : $(git log -1 --oneline 2>/dev/null || echo 'aucun')"
  if [ "$UNCOMMITTED" -gt 0 ]; then
    echo "Changements non commités : $UNCOMMITTED fichier(s)"
    git status --short 2>/dev/null | head -5
  else
    echo "Statut : propre"
  fi
  echo ""
} >> "$LOG_FILE" 2>/dev/null

exit 0
