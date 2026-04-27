#!/bin/bash
# Hook: PreToolUse → Edit/Write/MultiEdit
# Snapshot avant édition, rappel si TODO/FIXME présents

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# --- Protection fichiers sensibles (exit 2 = Claude reçoit le feedback) ---
PROTECTED_PATTERNS=(
  "\.env$"
  "\.env\."
  "\.pem$"
  "\.key$"
  "\.p12$"
  "\.pfx$"
  "secrets/"
  "package-lock\.json$"
  "yarn\.lock$"
  "\.git/"
)

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if echo "$FILE_PATH" | grep -qiE "$pattern"; then
    echo "BLOCKED: '$FILE_PATH' est un fichier protégé. Expliquez pourquoi cette modification est nécessaire." >&2
    exit 2
  fi
done

# Vérifier si le fichier existe déjà
if [ -f "$FILE_PATH" ]; then
  # Rappel TODO/FIXME
  TODO_COUNT=$(grep -c "TODO\|FIXME\|HACK\|XXX" "$FILE_PATH" 2>/dev/null || echo 0)
  if [ "$TODO_COUNT" -gt 0 ]; then
    echo ""
    echo "📝 RAPPEL : $TODO_COUNT TODO/FIXME dans $FILE_PATH"
    grep -n "TODO\|FIXME\|HACK\|XXX" "$FILE_PATH" 2>/dev/null | head -5 | sed 's/^/   → /'
  fi

  # Snapshot léger (nom + taille + date)
  SNAPSHOT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/.snapshots"
  mkdir -p "$SNAPSHOT_DIR"
  SNAP_FILE="$SNAPSHOT_DIR/$(basename "$FILE_PATH").$(date +%s).bak"
  cp "$FILE_PATH" "$SNAP_FILE" 2>/dev/null && \
    echo "   💾 Snapshot: $SNAP_FILE" || true

  # Nettoyer les snapshots anciens (garder les 5 derniers par fichier)
  ls -t "$SNAPSHOT_DIR/$(basename "$FILE_PATH").*.bak" 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null || true
fi

exit 0
