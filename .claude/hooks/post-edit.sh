#!/bin/bash
# Hook: PostToolUse → Edit/Write/MultiEdit
# Auto-lint après édition JS/TS, validation JSON, shellcheck pour .sh

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
  exit 0
fi

EXT="${FILE_PATH##*.}"

case "$EXT" in
  js|jsx|ts|tsx|mjs|cjs)
    # ESLint si disponible
    if command -v npx &>/dev/null && [ -f "${CLAUDE_PROJECT_DIR:-$(pwd)}/.eslintrc*" ] || [ -f "${CLAUDE_PROJECT_DIR:-$(pwd)}/eslint.config*" ]; then
      echo "🔍 ESLint → $FILE_PATH"
      cd "${CLAUDE_PROJECT_DIR:-$(pwd)}" && npx eslint --max-warnings=0 "$FILE_PATH" 2>&1 | head -20 || \
        echo "   ⚠️  Problèmes ESLint détectés — corrigez avant de commit"
    fi
    ;;
  json)
    # Validation JSON
    if python3 -c "import json,sys; json.load(open('$FILE_PATH'))" 2>/dev/null; then
      echo "✅ JSON valide : $FILE_PATH"
    else
      echo "❌ JSON invalide : $FILE_PATH"
      python3 -c "import json,sys; json.load(open('$FILE_PATH'))" 2>&1
    fi
    ;;
  sh|bash)
    # shellcheck si disponible
    if command -v shellcheck &>/dev/null; then
      echo "🔍 shellcheck → $FILE_PATH"
      shellcheck "$FILE_PATH" 2>&1 | head -20 || \
        echo "   ⚠️  Problèmes shellcheck détectés"
    fi
    ;;
  md)
    # Vérifier les liens cassés basiques (optionnel, non bloquant)
    BROKEN=$(grep -o '\[.*\]([^)]*' "$FILE_PATH" | grep -v 'http' | grep -o '([^)]*' | tr -d '(' | while read -r link; do
      [ -n "$link" ] && [ ! -f "$(dirname "$FILE_PATH")/$link" ] && echo "$link"
    done 2>/dev/null | head -3)
    if [ -n "$BROKEN" ]; then
      echo "⚠️  Liens potentiellement cassés dans $FILE_PATH :"
      echo "$BROKEN" | sed 's/^/   → /'
    fi
    ;;
esac

exit 0
