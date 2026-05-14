"""
Test rapide du moteur IA — Couche 2 Recommandations.

Moteurs supportés :
  - Claude (Anthropic) : ANTHROPIC_API_KEY=sk-ant-...   console.anthropic.com  (payant)
  - Groq (Llama 3.3)  : GROQ_API_KEY=gsk_...            console.groq.com       (GRATUIT)

Usage :
  GROQ_API_KEY=gsk_xxxx python test_ia.py
  ANTHROPIC_API_KEY=sk-ant-xxxx python test_ia.py
  GROQ_API_KEY=gsk_xxxx TAVILY_API_KEY=tvly-xxxx python test_ia.py
"""
import os, sys, json

anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
groq_key      = os.environ.get('GROQ_API_KEY', '').strip()
tavily_key    = os.environ.get('TAVILY_API_KEY', '').strip()

if not anthropic_key and not groq_key:
    print("❌  Aucune clé IA configurée.")
    print()
    print("  Option 1 — Groq (GRATUIT) :")
    print("    1. Créez un compte sur console.groq.com")
    print("    2. API Keys → Create API Key")
    print("    3. Lancez : GROQ_API_KEY=gsk_xxxx python test_ia.py")
    print()
    print("  Option 2 — Anthropic (payant) :")
    print("    ANTHROPIC_API_KEY=sk-ant-xxxx python test_ia.py")
    sys.exit(1)

if anthropic_key:
    print(f"✅  ANTHROPIC_API_KEY détectée ({len(anthropic_key)} chars) — moteur Claude")
    moteur_label = "Claude (Anthropic)"
else:
    print(f"✅  GROQ_API_KEY détectée ({len(groq_key)} chars) — moteur Llama 3.3 70B")
    moteur_label = "Llama 3.3 70B (Groq)"

print(f"{'✅' if tavily_key else '⚠️ '}  TAVILY_API_KEY {'détectée' if tavily_key else 'absente — IA sans sources web'}")
print()

sys.path.insert(0, '.')
from app.services.reco_ai import ai_enrichissement

contexte = {
    'trs_moyen':  35,
    'manque':     850_000,
    'nb_postes':  5,
}

print(f"🔍  Appel à {moteur_label} (règle TRS_CRITIQUE)…")
print("    Cela peut prendre 10–20 secondes.")
print()

resultat = ai_enrichissement('TRS_CRITIQUE', contexte)

if resultat.get('erreur'):
    print(f"❌  Erreur : {resultat['erreur']}")
    sys.exit(1)

print(f"✅  Source : {resultat.get('source', '?')}")
print(f"✅  {len(resultat['solutions'])} solutions reçues\n")

for i, s in enumerate(resultat['solutions'], 1):
    print(f"  Solution {i} : {s['titre']}")
    print(f"    Justification : {s['justification'][:140]}…")
    print(f"    Exemple       : {s['exemple'][:100]}")
    print(f"    Référence     : {s['reference'][:80]}")
    print()

print("✅  Test réussi — le module IA fonctionne correctement.")
