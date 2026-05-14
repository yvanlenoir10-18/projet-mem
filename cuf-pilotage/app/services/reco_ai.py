"""
Moteur de recommandations — Couche 2 : enrichissement IA on-demand.

Moteurs supportés (par ordre de priorité) :
  1. Claude API  — ANTHROPIC_API_KEY  (console.anthropic.com) — payant
  2. Groq        — GROQ_API_KEY       (console.groq.com)      — GRATUIT

+ Tavily pour la recherche web :
  TAVILY_API_KEY (app.tavily.com) — optionnel dans les deux cas

Cache : dict Python sauvegardé dans instance/reco_cache.json, TTL 7 jours.
Cette approche n'introduit aucune nouvelle table DB (R7 respectée) et persiste
entre redémarrages grâce au fichier JSON.
"""
import os
import json
import time

try:
    import anthropic as _anthropic_mod
    _ANTHROPIC_OK = True
except ImportError:
    _ANTHROPIC_OK = False

try:
    import groq as _groq_mod
    _GROQ_OK = True
except ImportError:
    _GROQ_OK = False

try:
    from tavily import TavilyClient as _TavilyClient
    _TAVILY_OK = True
except ImportError:
    _TAVILY_OK = False


_CACHE_FILE = os.path.join('instance', 'reco_cache.json')
_CACHE_TTL  = 7 * 24 * 3600  # 7 jours en secondes

# Requêtes de recherche par code de règle (EN + FR pour maximiser les résultats)
_REQUETES = {
    'TRS_CRITIQUE':          'OEE improvement sawmill low TRS bicoupe scierie Afrique solutions correctives',
    'TRS_MOYEN':             'OEE 55 percent manufacturing sawmill improvement solutions scierie',
    'MANQUE_ELEVE':          'réduction pertes financières scierie Afrique centrale manque gagner bois',
    'ARRETS_NON_DOCUMENTES': 'downtime documentation manufacturing shop floor arrêts non documentés production',
    'DECLASS_EXCESSIF':      'lumber degrade reduction sawmill blade maintenance déclassé scierie qualité bois',
    'SAISIES_INCOHERENTES':  'data quality manufacturing saisie terrain fiabilité données production',
    'TENDANCE_NEGATIVE':     'OEE decline rapid correction tendance baisse performance scierie actions correctives',
}

_SYSTEME = (
    "Tu es un expert en amélioration de la performance industrielle dans les scieries "
    "d'Afrique centrale, familier avec les réalités terrain camerounaises : contraintes "
    "d'approvisionnement en grumes, main-d'œuvre semi-qualifiée, essences tropicales "
    "(Ayous, Azobé, Iroko, Movingui), équipements parfois vieillissants. "
    "Tu proposes des solutions concrètes, actionnables sans investissement majeur, "
    "basées sur la littérature industrielle et des exemples réels d'autres usines. "
    "Tu réponds UNIQUEMENT en JSON valide, sans texte avant ou après le JSON."
)


def _charge_cache():
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE, encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _sauvegarde_cache(cache):
    os.makedirs('instance', exist_ok=True)
    with open(_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def cache_get(code):
    """Retourne les données du cache si valides (TTL 7 jours), sinon None."""
    cache = _charge_cache()
    entry = cache.get(code)
    if entry and time.time() - entry.get('ts', 0) < _CACHE_TTL:
        return entry.get('data')
    return None


def cache_invalidate(code):
    """Supprime l'entrée de cache pour forcer un recalcul au prochain appel."""
    cache = _charge_cache()
    if code in cache:
        del cache[code]
        _sauvegarde_cache(cache)


def _recherche_tavily(requete, tavily_key):
    """Retourne une liste de textes (source + extrait) depuis Tavily."""
    if not _TAVILY_OK or not tavily_key:
        return []
    try:
        client = _TavilyClient(api_key=tavily_key)
        res = client.search(requete, max_results=5, include_answer=False)
        return [
            f"[{r.get('url', '')}]\n{r.get('content', '')[:600]}"
            for r in res.get('results', [])
            if r.get('content')
        ]
    except Exception as e:
        return [f"[Tavily indisponible : {str(e)[:80]}]"]


def _charge_sources_externes(tavily_key):
    """
    Charge le contenu des URLs définies dans Parametre('reco_sources_externes').
    Retourne une liste de textes extraits.
    """
    if not _TAVILY_OK or not tavily_key:
        return []
    try:
        from ..models import Parametre
        sources_json = Parametre.get('reco_sources_externes', '[]')
        sources = json.loads(sources_json) if isinstance(sources_json, str) else []
        if not sources:
            return []

        client = _TavilyClient(api_key=tavily_key)
        textes = []
        for src in sources[:3]:  # max 3 sources externes
            url = src.get('url', '') if isinstance(src, dict) else str(src)
            titre = src.get('titre', url) if isinstance(src, dict) else url
            if not url:
                continue
            try:
                extracted = client.extract(urls=[url])
                for item in extracted.get('results', []):
                    content = item.get('raw_content', '')[:1000]
                    if content:
                        textes.append(f"[Source chargée — {titre}]\n{content}")
            except Exception:
                pass
        return textes
    except Exception:
        return []


def _appel_anthropic(anthropic_key, prompt):
    """Appelle Claude API et retourne le texte brut de la réponse."""
    client = _anthropic_mod.Anthropic(api_key=anthropic_key)
    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1800,
        system=_SYSTEME,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return message.content[0].text.strip()


def _appel_groq(groq_key, prompt):
    """Appelle Groq API (Llama 3.3 70B) et retourne le texte brut de la réponse."""
    client = _groq_mod.Groq(api_key=groq_key)
    message = client.chat.completions.create(
        model='llama-3.3-70b-versatile',
        max_tokens=1800,
        messages=[
            {'role': 'system', 'content': _SYSTEME},
            {'role': 'user', 'content': prompt},
        ],
    )
    return message.choices[0].message.content.strip()


def _nettoyer_json(contenu):
    """Nettoie les balises markdown éventuelles autour du JSON."""
    if '```' in contenu:
        parts = contenu.split('```')
        for p in parts:
            cleaned = p.strip()
            if cleaned.startswith('json'):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith('{'):
                return cleaned
    return contenu


def ai_enrichissement(code, contexte):
    """
    Appelle un moteur IA (Claude ou Groq) + Tavily pour enrichir une recommandation.

    Priorité : ANTHROPIC_API_KEY → GROQ_API_KEY (gratuit)

    Retourne un dict :
      solutions : liste de dicts (titre, justification, exemple, reference)
      source    : 'cache' | 'api_anthropic' | 'api_groq'
      erreur    : str | None
    """
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    groq_key      = os.environ.get('GROQ_API_KEY', '').strip()
    tavily_key    = os.environ.get('TAVILY_API_KEY', '').strip()

    # Sélection du moteur
    if anthropic_key and _ANTHROPIC_OK:
        moteur = 'anthropic'
    elif groq_key and _GROQ_OK:
        moteur = 'groq'
    else:
        manquants = []
        if not _ANTHROPIC_OK and not _GROQ_OK:
            manquants.append('pip install -r requirements.txt')
        else:
            manquants.append('ANTHROPIC_API_KEY (console.anthropic.com) ou GROQ_API_KEY (console.groq.com — gratuit)')
        return {
            'solutions': [],
            'erreur': 'Aucun moteur IA configuré. Ajoutez dans .env : ' + ' | '.join(manquants),
        }

    # Vérification cache
    cached = cache_get(code)
    if cached is not None:
        return {'solutions': cached, 'source': 'cache', 'erreur': None}

    # Recherche web via Tavily
    requete = _REQUETES.get(code, 'OEE sawmill improvement solutions Africa')
    resultats_web  = _recherche_tavily(requete, tavily_key)
    sources_extras = _charge_sources_externes(tavily_key)

    all_sources   = resultats_web + sources_extras
    sources_texte = '\n\n'.join(all_sources)[:3500] or 'Aucune source externe disponible.'

    # Construction du prompt
    trs_str    = f"{contexte.get('trs_moyen')}%" if contexte.get('trs_moyen') is not None else 'non calculé'
    manque_val = contexte.get('manque', 0)
    manque_str = f"{int(manque_val):,} FCFA".replace(',', ' ') if manque_val else 'N/A'
    nb_str     = str(contexte.get('nb_postes', 0))

    prompt = (
        f"PROBLÈME DÉTECTÉ : {code.replace('_', ' ')}\n"
        f"TRS moyen période : {trs_str}\n"
        f"Manque à gagner : {manque_str}\n"
        f"Postes analysés : {nb_str}\n"
        f"Contexte : Scierie CUF Ebolowa, Cameroun — bicoupe (goulot) — "
        f"essences Ayous/Azobé/Iroko/Movingui\n\n"
        f"SOURCES DOCUMENTAIRES :\n{sources_texte}\n\n"
        "Propose 3 solutions concrètes basées sur ces sources et ton expertise.\n"
        "Pour chaque solution fournis :\n"
        "- titre (max 10 mots)\n"
        "- justification (2-3 phrases, chiffres si disponibles)\n"
        "- exemple (usine ou cas réel similaire)\n"
        "- reference (URL ou citation de la source, ou \"\" si aucune)\n\n"
        'Réponds UNIQUEMENT avec ce JSON :\n'
        '{"solutions": [{"titre":"...","justification":"...","exemple":"...","reference":"..."}]}'
    )

    try:
        if moteur == 'anthropic':
            contenu = _appel_anthropic(anthropic_key, prompt)
            source_label = 'api_anthropic'
        else:
            contenu = _appel_groq(groq_key, prompt)
            source_label = 'api_groq'

        contenu = _nettoyer_json(contenu)
        data = json.loads(contenu)
        solutions = []
        for s in data.get('solutions', []):
            if isinstance(s, dict) and s.get('titre'):
                solutions.append({
                    'titre':         str(s.get('titre', '')),
                    'justification': str(s.get('justification', '')),
                    'exemple':       str(s.get('exemple', '')),
                    'reference':     str(s.get('reference', '')),
                })

        _ecrire_cache(code, solutions)
        return {'solutions': solutions, 'source': source_label, 'erreur': None}

    except json.JSONDecodeError as exc:
        return {'solutions': [], 'erreur': f'Réponse IA non parseable : {exc}'}
    except Exception as exc:
        return {'solutions': [], 'erreur': f'Erreur API {moteur} : {str(exc)[:200]}'}


def _ecrire_cache(code, data):
    cache = _charge_cache()
    cache[code] = {'ts': time.time(), 'data': data}
    _sauvegarde_cache(cache)


def cache_set(code, data):
    """Force l'écriture d'une entrée en cache (utilisé depuis tests ou admin)."""
    _ecrire_cache(code, data)
