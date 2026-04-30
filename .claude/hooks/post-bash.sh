#!/bin/bash
# Hook: PostToolUse → Bash
# npm audit après install, résumé après git commit

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# npm audit après npm install/ci
if echo "$COMMAND" | grep -qE "npm (install|ci|i )"; then
  echo ""
  echo "🔒 npm audit (post-install)..."
  cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" && npm audit --audit-level=high 2>&1 | tail -10 || \
    echo "   ⚠️  Vulnérabilités détectées — exécutez: npm audit fix"
fi

# Résumé après git commit
if echo "$COMMAND" | grep -qE "git commit"; then
  echo ""
  echo "📦 Dernier commit :"
  git -C "${CLAUDE_PROJECT_DIR:-$(pwd)}" log -1 --oneline 2>/dev/null | sed 's/^/   → /'
  echo "   Fichiers modifiés :"
  git -C "${CLAUDE_PROJECT_DIR:-$(pwd)}" diff --stat HEAD~1 HEAD 2>/dev/null | tail -5 | sed 's/^/     /' || true
fi

# Rappel après npm run build
if echo "$COMMAND" | grep -qE "npm run build"; then
  echo ""
  echo "✅ Build terminé. Pensez à vérifier :"
  echo "   → Taille du bundle (npm run analyze si disponible)"
  echo "   → Tests avant déploiement (npm test)"
fi

exit 0
