#!/usr/bin/env bash
# Triggered after each git commit on CUF Pilotage.
# Injects a reminder into Claude's context to generate the memoir impact note.

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)

# Only act on git commit commands
if ! echo "$CMD" | grep -q 'git commit'; then
  exit 0
fi

# Skip meta-commits (infrastructure, memoir notes) — avoids infinite loop
LAST_MSG=$(git -C "$CLAUDE_PROJECT_DIR" log -1 --format="%s" 2>/dev/null)
if echo "$LAST_MSG" | grep -qE '^(docs|chore|fix)\((memoir|notes-impact|notes|ci|hooks|config|taches)\):'; then
  exit 0
fi

# Check whether a global framing note already exists
NOTES_DIR="$CLAUDE_PROJECT_DIR/documents/notes-impact"
HAS_BASE="false"
if ls "$NOTES_DIR"/00-cadrage-global*.md 2>/dev/null | grep -q .; then
  HAS_BASE="true"
fi

if [ "$HAS_BASE" = "false" ]; then
  CONTEXT="RAPPEL AUTOMATIQUE - NOTE D IMPACT MEMOIRE : Un commit CUF Pilotage vient d etre effectue. Aucune note de cadrage global n existe encore dans documents/notes-impact/. Tu dois donc produire en premier lieu le Cadrage global de l application (section A : finalite, modules P1/P2/P3, donnees collectees, acteurs, indicateurs TRS/pertes, hypotheses provisoires, limites actuelles, consequences sur la methodologie et la fiche de collecte), puis enchainer avec la note specifique de la fonctionnalite commitee (section B en 9 sous-sections). Sauvegarde la note dans documents/notes-impact/ avec un nom de fichier explicite (ex: 00-cadrage-global-P1-P2-P3.md pour la base, puis P3-workflow-statut.md pour la note specifique)."
else
  CONTEXT="RAPPEL AUTOMATIQUE - NOTE D IMPACT MEMOIRE : Un commit CUF Pilotage vient d etre effectue. Une note de cadrage global existe deja dans documents/notes-impact/. Produis maintenant la note d impact incrementale de la fonctionnalite commitee, en 9 sections, selon les instructions de l utilisateur. Verifie si la nouvelle fonctionnalite contredit une hypothese precedente et signale-le explicitement. Sauvegarde dans documents/notes-impact/."
fi

printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}' "$CONTEXT"
