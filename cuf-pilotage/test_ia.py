"""
Test rapide du moteur IA — Couche 2 Recommandations.
Usage :
  ANTHROPIC_API_KEY=sk-ant-... python test_ia.py
  ANTHROPIC_API_KEY=... TAVILY_API_KEY=tvly-... python test_ia.py
"""
import os, sys, json

# Vérifications préalables
anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
tavily_key    = os.environ.get('TAVILY_API_KEY', '').strip()

if not anthropic_key:
    print("❌  ANTHROPIC_API_KEY manquante.")
    print("    Lancez : ANTHROPIC_API_KEY=sk-ant-xxxx python test_ia.py")
    sys.exit(1)

print(f"✅  ANTHROPIC_API_KEY détectée ({len(anthropic_key)} chars)")
print(f"{'✅' if tavily_key else '⚠️ '}  TAVILY_API_KEY {'détectée' if tavily_key else 'absente — IA sans sources web'}")
print()

# Import du moteur
sys.path.insert(0, '.')
from app.services.reco_ai import ai_enrichissement

# Contexte simulé : TRS critique
contexte = {
    'trs_moyen':  35,
    'manque':     850_000,
    'nb_postes':  5,
}

print("🔍  Appel à Claude API (règle TRS_CRITIQUE)…")
print("    Cela peut prendre 10–20 secondes selon le réseau.")
print()

resultat = ai_enrichissement('TRS_CRITIQUE', contexte)

if resultat.get('erreur'):
    print(f"❌  Erreur : {resultat['erreur']}")
    sys.exit(1)

print(f"✅  Source : {resultat.get('source', '?')}")
print(f"✅  {len(resultat['solutions'])} solutions reçues\n")

for i, s in enumerate(resultat['solutions'], 1):
    print(f"  Solution {i} : {s['titre']}")
    print(f"    Justification : {s['justification'][:120]}…")
    print(f"    Exemple       : {s['exemple'][:100]}")
    print(f"    Référence     : {s['reference'][:80]}")
    print()

print("✅  Test réussi — le module IA fonctionne correctement.")
print()
print("Prochaine étape : créez le fichier .env dans cuf-pilotage/ avec :")
print("  ANTHROPIC_API_KEY=" + anthropic_key[:8] + "…")
if tavily_key:
    print("  TAVILY_API_KEY=" + tavily_key[:8] + "…")
