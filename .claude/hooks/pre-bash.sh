#!/bin/bash
# Hook: PreToolUse → Bash
# Bloque les commandes dangereuses avant exécution + log audit

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# --- Log audit de toutes les commandes ---
LOG_FILE="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/command-log.txt"
mkdir -p "$(dirname "$LOG_FILE")"
printf '%s  %s\n' "$(date -Is)" "$COMMAND" >> "$LOG_FILE" 2>/dev/null || true

# --- Commandes destructives bloquées (exit 2 = Claude reçoit le feedback) ---
BLOCKED_PATTERNS=(
  "rm -rf /"
  "rm -rf \*"
  "git push --force.*main"
  "git push --force.*master"
  "git push -f.*main"
  "git push -f.*master"
  "DROP TABLE"
  "DROP DATABASE"
  "TRUNCATE TABLE"
  "chmod -R 777 /"
  "dd if=.*of=/dev/"
  "mkfs\."
  ":(){ :|:& };:"
  "^curl.*\|.*(sh|bash)"
  "^wget.*\|.*(sh|bash)"
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo "BLOCKED: Commande dangereuse détectée : $pattern. Proposez une alternative plus sûre." >&2
    exit 2
  fi
done

# --- Avertissements (non bloquants) ---
WARN_PATTERNS=(
  "git push --force"
  "git push -f"
  "git reset --hard"
  "git clean -f"
  "npm install"
  "npm ci"
)

for pattern in "${WARN_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo ""
    echo "⚠️  ATTENTION : Commande sensible détectée"
    echo "   → $COMMAND"
    echo "   → Vérifiez que c'est intentionnel"
    break
  fi
done

exit 0
