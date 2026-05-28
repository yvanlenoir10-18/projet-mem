#!/usr/bin/env bash
# smoke.sh — Lance l'app CUF Pilotage, vérifie les routes clés, arrête proprement.
# Usage : bash .claude/skills/run-cuf-pilotage/smoke.sh [--keep-running]
# Retourne 0 si tout est OK, 1 si une route échoue.
# Avec --keep-running, laisse le serveur actif après les tests.

set -euo pipefail

UNIT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"  # cuf-pilotage/
PORT=5000
BASE="http://127.0.0.1:${PORT}"
KEEP_RUNNING=false
[[ "${1:-}" == "--keep-running" ]] && KEEP_RUNNING=true

# ── 1. Démarrage ────────────────────────────────────────────────────────────
SERVER_PID=""

_stop_server() {
  [[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null && echo "[smoke] serveur arrêté (PID $SERVER_PID)"
}

if curl -s -o /dev/null -w "%{http_code}" "${BASE}/" 2>/dev/null | grep -q "200\|302"; then
  echo "[smoke] serveur déjà actif sur :${PORT}"
else
  echo "[smoke] démarrage du serveur Flask…"
  cd "$UNIT_DIR"
  python run.py > /tmp/cuf-pilotage-run.log 2>&1 &
  SERVER_PID=$!
  trap '_stop_server' EXIT

  for i in $(seq 1 12); do
    sleep 1
    if curl -s -o /dev/null "${BASE}/" 2>/dev/null; then
      echo "[smoke] serveur prêt (${i}s)"
      break
    fi
    [[ $i -eq 12 ]] && { echo "[smoke] TIMEOUT — log:"; cat /tmp/cuf-pilotage-run.log; exit 1; }
  done
fi

# ── 2. Helpers ───────────────────────────────────────────────────────────────
COOKIE_JAR=$(mktemp)
ERRORS=0

_login() {
  local email="$1" password="$2"
  rm -f "$COOKIE_JAR"; touch "$COOKIE_JAR"
  local csrf
  csrf=$(curl -s -c "$COOKIE_JAR" "${BASE}/login" \
    | grep -o 'name="csrf_token" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//')
  local http
  http=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    --data "email=${email}&password=${password}&csrf_token=${csrf}" \
    -o /dev/null -w "%{http_code}" \
    "${BASE}/login")
  [[ "$http" == "302" ]] || { echo "[smoke] ÉCHEC login ${email} — HTTP ${http}"; ((ERRORS++)); }
}

_check() {
  local label="$1" url="$2" expected="${3:-200}"
  local http
  http=$(curl -s -b "$COOKIE_JAR" -c "$COOKIE_JAR" -o /dev/null -w "%{http_code}" "${BASE}${url}")
  if [[ "$http" == "$expected" ]]; then
    echo "[smoke] OK  ${label} → ${http}"
  else
    echo "[smoke] ERR ${label} → ${http} (attendu ${expected})"
    ((ERRORS++))
  fi
}

# ── 3. Opérateur ─────────────────────────────────────────────────────────────
echo "--- Profil opérateur (saisie@cuf.cm) ---"
_login "saisie%40cuf.cm" "cuf2026"
_check "accueil opérateur"  "/saisie/accueil"
_check "formulaire nouveau" "/saisie/nouveau"
_check "historique"         "/saisie/historique"

# Soumettre une fiche de test
CSRF=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" "${BASE}/saisie/nouveau" \
  | grep -o 'name="csrf_token" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//')
HTTP=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  --data "csrf_token=${CSRF}&date=2026-05-28&poste=matin&numero_equipe=SMOKE&operateur_nom=Smoke&rempli_par_nom=Smoke&effectif=10&aucun_arret_confirme=1&prod_essence[]=Ayous&prod_heure_debut[]=06:00&prod_heure_fin[]=11:00&prod_volume_entree[]=8.0&prod_volume_conforme[]=5.0&prod_volume_declass[]=1.0" \
  -o /dev/null -w "%{http_code}" "${BASE}/saisie/nouveau")
[[ "$HTTP" == "302" ]] && echo "[smoke] OK  soumission fiche → 302 (brouillon créé)" \
                       || { echo "[smoke] ERR soumission fiche → $HTTP"; ((ERRORS++)); }

# ── 4. Chef ──────────────────────────────────────────────────────────────────
echo "--- Profil chef (chef@cuf.cm) ---"
_login "chef%40cuf.cm" "cuf2026"
_check "dashboard chef"    "/dashboard/chef"
_check "production"        "/dashboard/chef/production"
_check "qualité"           "/dashboard/chef/qualite"
_check "machines"          "/dashboard/chef/machines"
_check "analyse arrêts"    "/analyse/arrets"
_check "recommandations"   "/recommandations/"
_check "problèmes liste"   "/problemes/"

# ── 5. PDG ───────────────────────────────────────────────────────────────────
echo "--- Profil PDG (pdg@cuf.cm) ---"
_login "pdg%40cuf.cm" "cuf2026"
_check "dashboard PDG"     "/dashboard/pdg"

# ── 6. Admin ─────────────────────────────────────────────────────────────────
echo "--- Profil admin (admin@cuf.cm) ---"
_login "admin%40cuf.cm" "cuf2026"
_check "paramètres"        "/admin/parametres"
_check "utilisateurs"      "/admin/utilisateurs"

# ── 7. Anti-chevauchement (doit bloquer) ─────────────────────────────────────
echo "--- Validation métier ---"
_login "saisie%40cuf.cm" "cuf2026"
CSRF=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" "${BASE}/saisie/nouveau" \
  | grep -o 'name="csrf_token" value="[^"]*"' | head -1 | sed 's/.*value="//;s/"//')
RESP=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
  --data "csrf_token=${CSRF}&date=2026-05-28&poste=matin&numero_equipe=CHV&operateur_nom=Smoke&rempli_par_nom=Smoke&effectif=10&aucun_arret_confirme=1&prod_essence[]=Ayous&prod_heure_debut[]=06:00&prod_heure_fin[]=11:00&prod_volume_entree[]=8.0&prod_volume_conforme[]=5.0&prod_volume_declass[]=1.0&prod_essence[]=Azobe&prod_heure_debut[]=08:00&prod_heure_fin[]=14:00&prod_volume_entree[]=7.0&prod_volume_conforme[]=4.0&prod_volume_declass[]=1.0" \
  -w "\n__HTTP:%{http_code}__" "${BASE}/saisie/nouveau")
CHV_HTTP=$(echo "$RESP" | grep -o '__HTTP:[0-9]*__' | sed 's/__HTTP://;s/__//')
CHV_MSG=$(echo "$RESP" | grep -oi "Chevauchement horaire" | head -1)
[[ "$CHV_HTTP" == "200" && -n "$CHV_MSG" ]] \
  && echo "[smoke] OK  anti-chevauchement → bloqué (HTTP 200 + flash danger)" \
  || { echo "[smoke] ERR anti-chevauchement → HTTP $CHV_HTTP, flash: '$CHV_MSG'"; ((ERRORS++)); }

# ── 8. Résultat ──────────────────────────────────────────────────────────────
rm -f "$COOKIE_JAR"

if [[ $ERRORS -eq 0 ]]; then
  echo ""
  echo "[smoke] ✓ Tous les tests passent."
  $KEEP_RUNNING || true
  exit 0
else
  echo ""
  echo "[smoke] ✗ ${ERRORS} erreur(s) détectée(s)."
  exit 1
fi
