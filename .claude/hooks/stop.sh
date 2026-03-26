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
  echo "⚠️  $UNCOMMITTED fichier(s) non commité(s) :"
  git status --short 2>/dev/null | head -10 | sed 's/^/   /'
  echo ""
  echo "   → git add . && git commit -m 'votre message'"
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
