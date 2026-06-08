"""
Moteur de prescriptions de pilotage — Couche 1 : règles déterministes (100 % hors ligne).

Analyse les équipes d'une période et génère des prescriptions prioritaires
basées sur les métriques observées : TRS, manque à gagner, anomalies de saisie,
tendance hebdomadaire.
"""
from datetime import date, timedelta
from ..models import Parametre


def _fmt_fcfa(n):
    """Formate un entier en FCFA avec séparateurs d'espace."""
    return f"{int(n):,}".replace(",", " ") + " FCFA"


# ── Métadonnées des règles (déclencheurs inchangés) ───────────────────────────

_REGLES = [
    {
        'code':     'TRS_CRITIQUE',
        'titre':    'TRS critique — intervention urgente',
        'icone':    'bi-speedometer2',
        'couleur':  'terracotta',
        'priorite': 3,
        'famille':  'performance',
        'roles':    ['prod', 'admin'],
    },
    {
        'code':     'TRS_MOYEN',
        'titre':    "TRS sous l'objectif — amélioration possible",
        'icone':    'bi-graph-up-arrow',
        'couleur':  'ochre',
        'priorite': 2,
        'famille':  'performance',
        'roles':    ['prod', 'admin'],
    },
    {
        'code':     'MANQUE_ELEVE',
        'titre':    'Manque à gagner élevé — impact financier significatif',
        'icone':    'bi-cash-stack',
        'couleur':  'terracotta',
        'priorite': 3,
        'famille':  'financier',
        'roles':    ['pdg', 'admin'],
    },
    {
        'code':     'ARRETS_NON_DOCUMENTES',
        'titre':    'Arrêts non documentés — données insuffisantes pour agir',
        'icone':    'bi-file-earmark-x',
        'couleur':  'ochre',
        'priorite': 2,
        'famille':  'donnees',
        'roles':    ['prod', 'admin'],
    },
    {
        'code':     'DECLASS_EXCESSIF',
        'titre':    'Déclassé excessif — perte qualité matière',
        'icone':    'bi-exclamation-diamond',
        'couleur':  'terracotta',
        'priorite': 3,
        'famille':  'qualite',
        'roles':    ['prod', 'pdg', 'admin'],
    },
    {
        'code':     'SAISIES_INCOHERENTES',
        'titre':    'Saisies incohérentes — fiabilité des données à améliorer',
        'icone':    'bi-shield-exclamation',
        'couleur':  'ochre',
        'priorite': 1,
        'famille':  'donnees',
        'roles':    ['prod', 'admin'],
    },
    {
        'code':     'TENDANCE_NEGATIVE',
        'titre':    'Tendance baissière — dérive à corriger rapidement',
        'icone':    'bi-graph-down-arrow',
        'couleur':  'terracotta',
        'priorite': 3,
        'famille':  'tendance',
        'roles':    ['pdg', 'admin'],
    },
]

_INDEX_REGLES = {r['code']: r for r in _REGLES}


# ── Gabarits : 6 sections par code de règle ───────────────────────────────────

def _fiche_arrets_non_documentes(ctx: dict) -> dict:
    nb_postes   = ctx.get('nb_postes', 0) or 1
    pct_r2      = ctx.get('pct_r2', 0.0)
    nb_r2       = max(1, round(pct_r2 * nb_postes / 100))
    manque      = ctx.get('manque', 0)
    seuil_cible = 15.0
    pl          = 's' if nb_r2 > 1 else ''
    return {
        'signal': (
            f"{nb_r2} poste{pl} sur {nb_postes} analysés ({pct_r2} %) "
            f"présentent une anomalie R2 : TRS bas sans aucun arrêt documenté. "
            f"L'outil ne peut pas identifier la cause de ces baisses de cadence."
        ),
        'lecture': (
            "Un poste R2, c'est un poste où le chef de poste a constaté un ralentissement "
            "sans noter pourquoi. Ces postes sont des angles morts : le Pareto ne les "
            "inclut pas, les causes restent inconnues, et les mêmes problèmes peuvent se "
            "répéter sans jamais être traités."
        ),
        'cout': (
            f"Manque à gagner estimé sur la période : {_fmt_fcfa(manque)}. "
            f"Ce chiffre est une sous-estimation — les {nb_r2} poste{pl} R2 ont des "
            f"arrêts non saisis qui n'entrent pas dans le calcul."
        ),
        'action': (
            f"Rouvrir les {nb_r2} fiche{pl} R2 avec les chefs de poste concernés "
            f"et documenter rétrospectivement la cause probable. "
            f"Pour les prochains postes : saisir l'arrêt dès qu'il survient "
            f"(machine + durée + cause)."
        ),
        'gain': (
            "Non chiffrable directement en FCFA — ce n'est pas un problème de "
            "performance, c'est un problème de données. Le corriger rend le Pareto "
            "fiable sur ces postes et améliore la précision de tous les indicateurs."
        ),
        'verification': (
            f"Indicateur : % postes avec anomalie R2. "
            f"Avant : {pct_r2} %. "
            f"Objectif : ramener sous {seuil_cible} % "
            f"sur les {nb_postes} prochains postes."
        ),
        'cta':          'corriger_fiches',
        'cta_anomalie': 'avertissements',
    }


def _fiche_saisies_incoherentes(ctx: dict) -> dict:
    nb_postes   = ctx.get('nb_postes', 0) or 1
    pct_r1_r4   = ctx.get('pct_r1_r4', 0.0)
    nb_incoher  = max(1, round(pct_r1_r4 * nb_postes / 100))
    manque      = ctx.get('manque', 0)
    seuil_cible = 10.0
    pl          = 's' if nb_incoher > 1 else ''
    return {
        'signal': (
            f"{nb_incoher} poste{pl} sur {nb_postes} ({pct_r1_r4} %) "
            f"présentent des incohérences de saisie (R1 ou R4) : volume ou TRS "
            f"impossible. Ces fiches ne peuvent pas être intégrées dans les calculs."
        ),
        'lecture': (
            "Une saisie incohérente, c'est un chiffre qui ne peut pas être réel — "
            "volume = 0 avec un TRS élevé, ou TRS > 100 %. "
            "L'outil les détecte et les exclut, mais leur présence fausse les compteurs "
            "de fiches validées et réduit la fiabilité des moyennes affichées."
        ),
        'cout': (
            f"Manque à gagner estimé sur la période : {_fmt_fcfa(manque)}. "
            f"Ce montant ne prend pas en compte les {nb_incoher} poste{pl} incohérents "
            f"exclus du calcul — le vrai manque à gagner est supérieur."
        ),
        'action': (
            f"Rouvrir les {nb_incoher} fiche{pl} incohérentes, identifier l'erreur "
            f"(volume mal saisi, arrêt non déduit du TRS) et corriger avant validation. "
            f"Pour les prochains postes : vérifier la cohérence TRS–volume "
            f"avant de soumettre la fiche."
        ),
        'gain': (
            "Non chiffrable directement en FCFA — c'est un problème de données, "
            "pas de production. Corriger ces saisies améliore la fiabilité du TRS "
            "moyen, du Pareto et de tous les indicateurs financiers de la période."
        ),
        'verification': (
            f"Indicateur : % postes avec incohérence de saisie (R1 ou R4). "
            f"Avant : {pct_r1_r4} %. "
            f"Objectif : ramener sous {seuil_cible} % "
            f"sur les {nb_postes} prochains postes."
        ),
        'cta':          'corriger_fiches',
        'cta_anomalie': 'bloquantes',
    }


def _fiche_trs_critique(ctx: dict) -> dict:
    trs_moyen      = ctx.get('trs_moyen') or 0.0
    manque         = ctx.get('manque', 0)
    trs_objectif   = ctx.get('trs_objectif', 60.0)
    machine_crit   = ctx.get('machine_critique') or 'la machine goulot'
    machine_h      = ctx.get('machine_arrets_h', 0.0)
    gain_potentiel = ctx.get('gain_potentiel_fcfa', 0)
    nb_postes      = ctx.get('nb_postes', 0)
    ecart          = round(trs_objectif - trs_moyen, 1)
    return {
        'signal': (
            f"TRS moyen de la période : {trs_moyen} % — "
            f"en dessous du seuil critique de 50 % "
            f"(objectif CUF : {trs_objectif} %). "
            f"Sur {nb_postes} poste{'s' if nb_postes > 1 else ''} analysés, "
            f"{machine_crit} cumule {machine_h} h d'arrêts."
        ),
        'lecture': (
            f"Un TRS sous 50 % signifie que la chaîne 4 tourne à moins de la "
            f"moitié de sa capacité. {machine_crit.capitalize()} est le goulot identifié : "
            f"chaque heure d'arrêt sur cette machine arrête toute la production. "
            f"La cause racine n'est pas encore identifiée — c'est l'objectif de cette prescription."
        ),
        'cout': (
            f"Manque à gagner estimé sur la période : {_fmt_fcfa(manque)}. "
            f"L'écart de {ecart} points de TRS représente l'essentiel de ce montant."
        ),
        'action': (
            f"Analyser la cause racine des arrêts sur {machine_crit} via une analyse "
            f"Ishikawa : identifier si l'arrêt vient d'une panne machine, d'un "
            f"manque d'approvisionnement, d'un réglage inadapté ou d'une cause "
            f"organisationnelle. Traiter la cause identifiée avant le prochain poste."
        ),
        'gain': (
            f"Si le TRS remonte de {trs_moyen} % à {trs_objectif} %, "
            f"gain estimé : {_fmt_fcfa(gain_potentiel)} sur la même période. "
            f"Estimation basée sur l'écart TRS × capacité chaîne 4 × prix moyen pondéré."
        ),
        'verification': (
            f"Indicateur : TRS moyen de la période. "
            f"Avant : {trs_moyen} %. "
            f"Objectif intermédiaire : dépasser 55 % sur les 7 prochains postes, "
            f"puis {trs_objectif} % à 30 jours."
        ),
        'cta': 'creer_ishikawa',
    }


def _fiche_trs_moyen(ctx: dict) -> dict:
    trs_moyen      = ctx.get('trs_moyen') or 0.0
    manque         = ctx.get('manque', 0)
    trs_objectif   = ctx.get('trs_objectif', 60.0)
    machine_crit   = ctx.get('machine_critique') or 'la bicoupe'
    gain_potentiel = ctx.get('gain_potentiel_fcfa', 0)
    nb_postes      = ctx.get('nb_postes', 0)
    ecart          = round(trs_objectif - trs_moyen, 1)
    return {
        'signal': (
            f"TRS moyen de la période : {trs_moyen} % — "
            f"sous l'objectif CUF de {trs_objectif} % (écart : {ecart} points). "
            f"Sur {nb_postes} poste{'s' if nb_postes > 1 else ''} analysés, "
            f"{machine_crit} est la machine la plus impactante."
        ),
        'lecture': (
            f"Un TRS entre 50 et 60 % indique une marge d'amélioration réelle "
            f"sans situation de crise. L'écart de {ecart} points avec l'objectif "
            f"correspond à des pertes de performance (vitesse, micro-arrêts) "
            f"et/ou de qualité (déclassé) réductibles avec des actions ciblées."
        ),
        'cout': (
            f"Manque à gagner estimé sur la période : {_fmt_fcfa(manque)}. "
            f"Les {ecart} points d'écart TRS représentent l'essentiel de ce montant."
        ),
        'action': (
            f"Analyser les causes des pertes de performance sur {machine_crit} : "
            f"temps de réglage, micro-arrêts non saisis, transitions d'essence. "
            f"Identifier la cause principale (Pareto) et planifier une action corrective "
            f"testable dès le prochain poste."
        ),
        'gain': (
            f"Si le TRS remonte à {trs_objectif} %, "
            f"gain estimé : {_fmt_fcfa(gain_potentiel)} sur la même période. "
            f"Une amélioration de 5 points de TRS est atteignable en 2 à 4 semaines "
            f"avec des actions organisationnelles ciblées."
        ),
        'verification': (
            f"Indicateur : TRS moyen de la période. "
            f"Avant : {trs_moyen} %. "
            f"Objectif : dépasser {trs_objectif} % sur les 30 prochains jours."
        ),
        'cta': 'creer_ishikawa',
    }


def _fiche_manque_eleve(ctx: dict) -> dict:
    manque     = ctx.get('manque', 0)
    trs_moyen  = ctx.get('trs_moyen') or 0.0
    nb_postes  = ctx.get('nb_postes', 0)
    cause_dom  = ctx.get('cause_dominante') or 'la cause principale'
    cause_pct  = ctx.get('cause_dominante_pct', 0.0)
    cause_fcfa = ctx.get('cause_dominante_fcfa', 0)
    return {
        'signal': (
            f"Manque à gagner estimé sur la période : {_fmt_fcfa(manque)} "
            f"sur {nb_postes} poste{'s' if nb_postes > 1 else ''} "
            f"(TRS moyen : {trs_moyen} %). "
            f"La cause « {cause_dom} » représente {cause_pct} % "
            f"du temps d'arrêt ({_fmt_fcfa(cause_fcfa)})."
        ),
        'lecture': (
            f"Un manque à gagner élevé signifie que la chaîne 4 produit nettement "
            f"moins que sa capacité théorique. La cause « {cause_dom} » "
            f"est le levier prioritaire : elle concentre {cause_pct} % "
            f"des pertes et est donc la plus rentable à traiter en premier."
        ),
        'cout': (
            f"Manque à gagner total estimé : {_fmt_fcfa(manque)} sur la période. "
            f"Part attribuable à « {cause_dom} » : "
            f"{_fmt_fcfa(cause_fcfa)} ({cause_pct} %). "
            f"Ce montant intègre les pertes de disponibilité, de performance et de qualité."
        ),
        'action': (
            f"Lancer une analyse Ishikawa sur la cause « {cause_dom} » "
            f"pour identifier la cause racine et planifier une contre-mesure structurelle. "
            f"Prioriser cette action avant toute autre : c'est la plus coûteuse."
        ),
        'gain': (
            f"Si la cause « {cause_dom} » est réduite de moitié, "
            f"gain estimé : {_fmt_fcfa(cause_fcfa // 2)} sur la même période. "
            f"Estimation conservatrice basée sur la part actuelle dans le Pareto."
        ),
        'verification': (
            f"Indicateur : manque à gagner total FCFA / période. "
            f"Avant : {_fmt_fcfa(manque)}. "
            f"Comparer sur la même durée après action corrective."
        ),
        'cta': 'creer_ishikawa',
    }


def _fiche_declass_excessif(ctx: dict) -> dict:
    pct_r3      = ctx.get('pct_r3', 0.0)
    manque      = ctx.get('manque', 0)
    nb_postes   = ctx.get('nb_postes', 0)
    ess_dec     = ctx.get('essence_declass') or 'une essence'
    dec_pct_ess = ctx.get('declass_pct_essence', 0.0)
    seuil_dec   = float(Parametre.get('seuil_declass_pct', '30'))
    nb_r3       = max(1, round(pct_r3 * nb_postes / 100))
    pl          = 's' if nb_r3 > 1 else ''
    return {
        'signal': (
            f"{nb_r3} poste{pl} sur {nb_postes} ({pct_r3} %) "
            f"dépassent le seuil de déclassement ({seuil_dec} %). "
            f"L'essence la plus problématique est {ess_dec} avec "
            f"{dec_pct_ess} % de volume déclassé."
        ),
        'lecture': (
            f"Un déclassement élevé sur {ess_dec} signifie que le bois sort de la "
            f"bicoupe en qualité inférieure au prix nominal. Causes les plus fréquentes : "
            f"lame émoussée, mauvais réglage bicoupe pour cette essence, "
            f"ou grumes de mauvaise qualité à l'entrée du parc."
        ),
        'cout': (
            f"Manque à gagner estimé sur la période : {_fmt_fcfa(manque)}. "
            f"Une partie est due au différentiel de prix entre le volume conforme "
            f"et le volume déclassé — le déclassé se vend à prix inférieur ou est perdu."
        ),
        'action': (
            f"Vérifier et remplacer les lames bicoupe pour {ess_dec} ; "
            f"contrôler les réglages (vitesse, pression) adaptés à cette essence ; "
            f"inspecter la qualité des grumes entrantes si le problème persiste. "
            f"Appliquer le standard lames : préventif toutes les 2 h "
            f"+ immédiat au changement tendre↔dure."
        ),
        'gain': (
            f"Si le taux de déclassement de {ess_dec} revient sous {seuil_dec} %, "
            f"une partie du volume actuellement déclassé est récupérée en valeur conforme. "
            f"Estimation : 30 à 60 % du manque à gagner lié au déclassé "
            f"est récupérable avec des actions sur les lames et les réglages."
        ),
        'verification': (
            f"Indicateur : % volume déclassé sur {ess_dec}. "
            f"Avant : {dec_pct_ess} %. "
            f"Objectif : revenir sous {seuil_dec} % "
            f"sur les 7 prochains postes traitant cette essence."
        ),
        'cta': 'creer_ishikawa',
    }


def _fiche_tendance_negative(ctx: dict) -> dict:
    manque    = ctx.get('manque', 0)
    trs_moyen = ctx.get('trs_moyen') or 0.0
    nb_postes = ctx.get('nb_postes', 0)
    return {
        'signal': (
            f"Le manque à gagner est en hausse de plus de 10 % par rapport "
            f"à la semaine précédente. "
            f"TRS actuel : {trs_moyen} % sur "
            f"{nb_postes} poste{'s' if nb_postes > 1 else ''} analysés. "
            f"Manque à gagner estimé cette semaine : {_fmt_fcfa(manque)}."
        ),
        'lecture': (
            "Une tendance baissière signifie que la performance se dégrade d'une semaine "
            "à l'autre. Ce n'est pas encore une crise, mais la dérive doit être stoppée "
            "rapidement avant de s'installer. Les causes les plus fréquentes : "
            "changement de mix essence, début de panne progressive, "
            "ou relâchement organisationnel."
        ),
        'cout': (
            f"Manque à gagner estimé cette semaine : {_fmt_fcfa(manque)}. "
            f"Si la tendance continue au même rythme, le manque à gagner mensuel "
            f"sera supérieur de plus de 40 % à la semaine précédente."
        ),
        'action': (
            "Comparer le mix d'essences des deux semaines pour exclure un effet naturel. "
            "Puis analyser le TRS par shift (Matin vs Après-midi) pour localiser la dérive. "
            "Si un shift décroche, réunion de 15 min avec les chefs concernés pour "
            "identifier la cause et tester une action corrective dès le même jour."
        ),
        'gain': (
            f"Si la dérive est stoppée cette semaine, le manque à gagner revient "
            f"au niveau de la semaine précédente. "
            f"Gain estimé : entre 10 et 40 % du montant actuel selon "
            f"la cause identifiée."
        ),
        'verification': (
            f"Indicateur : manque à gagner FCFA / semaine. "
            f"Avant : {_fmt_fcfa(manque)} cette semaine. "
            f"Objectif : semaine prochaine sous le niveau de la semaine d'avant la dérive."
        ),
        'cta': 'creer_ishikawa',
    }


_GABARITS = {
    'ARRETS_NON_DOCUMENTES': _fiche_arrets_non_documentes,
    'SAISIES_INCOHERENTES':  _fiche_saisies_incoherentes,
    'TRS_CRITIQUE':          _fiche_trs_critique,
    'TRS_MOYEN':             _fiche_trs_moyen,
    'MANQUE_ELEVE':          _fiche_manque_eleve,
    'DECLASS_EXCESSIF':      _fiche_declass_excessif,
    'TENDANCE_NEGATIVE':     _fiche_tendance_negative,
}


# ── Moteur principal ───────────────────────────────────────────────────────────

def analyse_recommandations(equipes, contexte_extra=None):
    """
    Analyse une liste d'équipes et retourne les prescriptions actives,
    triées par priorité décroissante.

    Paramètres :
        equipes       : liste de Equipe (données validées de la période).
        contexte_extra: dict optionnel avec des clés enrichies (machine_critique,
                        cause_dominante, essence_declass…) calculées dans la route.

    Retourne une liste de dicts avec :
        - clés _REGLES (code, titre, icone, couleur, priorite, famille, roles)
        - 'contexte' : métriques ayant déclenché la règle
        - 'fiche'    : 6 sections dynamiques (signal, lecture, cout, action, gain, verification)
        - 'solutions': [] (maintenu vide pour compatibilité legacy)
    """
    if not equipes:
        return []

    from .trs import manque_a_gagner_agrege
    from .controles_saisie import detecte_anomalies

    nb_postes = len(equipes)
    trs_vals  = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else None
    manque    = manque_a_gagner_agrege(equipes).get('manque_a_gagner_estime', 0.0)

    nb_r1 = nb_r2 = nb_r3 = nb_r4 = 0
    for e in equipes:
        for a in detecte_anomalies(e):
            code_a = a.get('code', '')
            if   code_a == 'R1': nb_r1 += 1
            elif code_a == 'R2': nb_r2 += 1
            elif code_a == 'R3': nb_r3 += 1
            elif code_a == 'R4': nb_r4 += 1

    pct_r2    = round(nb_r2    / nb_postes * 100, 1)
    pct_r3    = round(nb_r3    / nb_postes * 100, 1)
    pct_r1_r4 = round((nb_r1 + nb_r4) / nb_postes * 100, 1)

    seuil_trs_critique = float(Parametre.get('seuil_trs_critique',         '50'))
    seuil_trs_moyen    = float(Parametre.get('seuil_trs_moyen',            '60'))
    seuil_manque       = float(Parametre.get('seuil_manque_eleve',         '500000'))
    seuil_anomalie_pct = float(Parametre.get('seuil_anomalies_pct',        '30'))
    seuil_incoher      = float(Parametre.get('seuil_saisies_incoherentes', '20'))
    trs_objectif       = float(Parametre.get('trs_objectif_pct',           '60'))

    # Gain potentiel : fraction du manque récupérable en atteignant l'objectif TRS
    gain_potentiel = 0.0
    if trs_moyen is not None and trs_moyen < trs_objectif and trs_moyen < 100:
        gain_potentiel = round(manque * (trs_objectif - trs_moyen) / (100 - trs_moyen))

    contexte = {
        'trs_moyen':          trs_moyen,
        'manque':             manque,
        'nb_postes':          nb_postes,
        'pct_r2':             pct_r2,
        'pct_r3':             pct_r3,
        'pct_r1_r4':          pct_r1_r4,
        'trs_objectif':       trs_objectif,
        'gain_potentiel_fcfa': gain_potentiel,
    }
    if contexte_extra:
        contexte.update(contexte_extra)

    actives = []

    if trs_moyen is not None and trs_moyen < seuil_trs_critique:
        actives.append('TRS_CRITIQUE')
    elif trs_moyen is not None and trs_moyen < seuil_trs_moyen:
        actives.append('TRS_MOYEN')

    if manque > seuil_manque:
        actives.append('MANQUE_ELEVE')

    if pct_r2 > seuil_anomalie_pct:
        actives.append('ARRETS_NON_DOCUMENTES')

    if pct_r3 > seuil_anomalie_pct:
        actives.append('DECLASS_EXCESSIF')

    if pct_r1_r4 > seuil_incoher:
        actives.append('SAISIES_INCOHERENTES')

    try:
        from .cumuls import vue_executive_pdg
        vue = vue_executive_pdg(date.today())
        delta_manque = vue.get('semaine', {}).get('deltas', {}).get('manque_a_gagner', {})
        pct_manque = delta_manque.get('pct')
        if pct_manque is not None and pct_manque > 10:
            actives.append('TENDANCE_NEGATIVE')
    except Exception:
        pass

    result = []
    for code in actives:
        regle = dict(_INDEX_REGLES[code])
        regle['solutions'] = []   # legacy — maintenu vide
        regle['contexte']  = contexte
        if code in _GABARITS:
            regle['fiche'] = _GABARITS[code](contexte)
        result.append(regle)

    result.sort(key=lambda r: r['priorite'], reverse=True)
    return result


def top_n_recommandations(equipes, role, n=3):
    """Retourne les n prescriptions les plus prioritaires pour un rôle donné."""
    all_recos = analyse_recommandations(equipes)
    return [r for r in all_recos if role in r['roles']][:n]
