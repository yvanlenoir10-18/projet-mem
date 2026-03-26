#!/bin/bash
# Hook: PreToolUse → Bash
# Bloque les commandes dangereuses avant exécution

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# --- Commandes destructives bloquées ---
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
)

for pattern in "${BLOCKED_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiE "$pattern"; then
    echo "BLOCKED: Commande dangereuse détectée : $pattern" >&2
    echo "Commande refusée par le hook pre-bash.sh. Vérifiez avant d'exécuter." >&2
    exit 1
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
