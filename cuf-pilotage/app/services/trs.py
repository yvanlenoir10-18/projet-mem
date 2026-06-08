"""
Service de calcul du TRS et des pertes financières — Scierie CUF, Chaîne 4.

TRS = Disponibilité × Performance × Qualité
Référence : Jonsson & Lesshammar (1999), fondateurs de l'OEE/TRS.

Attribution D/P/Q indicative :
  Cause D = arrêts impactants × capacité_h × prix_moyen_pondéré
  Cause P = (capacité_temps_utile − volume_sorti) × prix_moyen_pondéré
  Cause Q = pertes de valeur sur déclassé + déchets sans valeur en V1

Volumes :
  volume_sorti   = conforme + declass (base Performance et Qualité TRS)
  volume_conforme = planches satisfaisant les contrats (base Qualité TRS)
  volume_declass  = planches déclassées vendues localement à 70% par défaut
  volume_dechets  = sciure/dosses/chutes — valeur résiduelle 0 FCFA en V1
"""
from collections import defaultdict

from ..models import Parametre, normalise_essence


# ── TRS ──────────────────────────────────────────────────────────────────────

def _minutes(hhmm):
    try:
        h, m = map(int, hhmm.split(':'))
        return h * 60 + m
    except (AttributeError, ValueError):
        return None


def _param_float(cle, defaut=0.0):
    try:
        return float(Parametre.get(cle, defaut))
    except (TypeError, ValueError):
        return float(defaut)


def _capacite_h_essence(essence):
    """Capacité théorique m³/h d'une essence, avec fallback global."""
    capacite_defaut = _param_float('capacite_equipe_h', 1.5625)
    cle = f'capacite_{normalise_essence(essence)}_h'
    return _param_float(cle, capacite_defaut)


def _duree_minutes(debut, fin):
    d = _minutes(debut)
    f = _minutes(fin)
    if d is None or f is None:
        return 0
    return max(0, f - d)


def _chevauchement_minutes(debut_a, fin_a, debut_b, fin_b):
    da = _minutes(debut_a)
    fa = _minutes(fin_a)
    db = _minutes(debut_b)
    fb = _minutes(fin_b)
    if None in (da, fa, db, fb):
        return 0
    return max(0, min(fa, fb) - max(da, db))


def _intervalle_impact_arret(arret):
    """
    Retourne l'intervalle horaire qui impacte réellement le TRS.
    Pour une maintenance planifiée, seul le dépassement est imputé, en fin
    d'arrêt : prévu 30 min, réel 50 min => impact des 20 dernières minutes.
    """
    debut = _minutes(arret.heure_debut)
    fin = _minutes(arret.heure_fin)
    if debut is None or fin is None or fin <= debut:
        return None

    impact = arret.duree_impact_min
    if impact <= 0:
        return None

    if arret.categorie == 'Maintenance planifiée':
        return (max(debut, fin - impact), fin)
    return (debut, fin)


def _arrets_sur_creneau(equipe, heure_debut, heure_fin):
    debut = _minutes(heure_debut)
    fin = _minutes(heure_fin)
    if debut is None or fin is None:
        return 0

    total = 0
    for arret in equipe.arrets:
        intervalle = _intervalle_impact_arret(arret)
        if not intervalle:
            continue
        a_debut, a_fin = intervalle
        total += max(0, min(fin, a_fin) - max(debut, a_debut))
    return total


def calcule_trs_production(production):
    """
    Calcule le TRS d'une essence sur sa propre fenêtre horaire.
    Les arrêts retenus sont uniquement ceux qui chevauchent cette fenêtre.
    """
    duree = production.duree_traitement_min
    if duree <= 0:
        return None

    capacite_h = _capacite_h_essence(production.essence)
    arrets_min = _arrets_sur_creneau(
        production.equipe,
        production.heure_debut,
        production.heure_fin,
    )
    temps_utile = max(0, duree - arrets_min)

    disponibilite = temps_utile / duree if duree > 0 else 0
    volume_theorique = capacite_h * (temps_utile / 60)
    volume_sorti = production.volume_conforme + production.volume_declass
    performance = min(1.0, volume_sorti / volume_theorique) if volume_theorique > 0 else 0
    qualite = production.volume_conforme / volume_sorti if volume_sorti > 0 else 0
    trs_global = disponibilite * performance * qualite * 100

    return {
        'essence': production.essence,
        'duree_planifiee': duree,
        'duree_arrets': arrets_min,
        'temps_utile': temps_utile,
        'volume_theorique': round(volume_theorique, 2),
        'disponibilite': round(disponibilite * 100, 1),
        'performance': round(performance * 100, 1),
        'qualite': round(qualite * 100, 1),
        'trs_global': round(trs_global, 1),
    }


def calcule_trs_par_essence(equipes):
    """
    Agrège le TRS par essence à partir des fenêtres horaires de Production.
    Fallback : si une essence n'a aucune fenêtre renseignée, on garde l'ancien
    indicateur basé sur les TRS globaux des postes qui contiennent cette essence.
    """
    data = defaultdict(lambda: {
        'volume_total': 0.0,
        'volume_temps': 0.0,
        'volume_conforme_temps': 0.0,
        'volume_theorique': 0.0,
        'temps_planifie': 0,
        'arrets': 0,
        'trs_fallback': [],
        'nb_lignes': 0,
        'nb_lignes_temporalisees': 0,
    })

    for equipe in equipes:
        for prod in equipe.productions:
            essence = prod.essence
            volume_sorti = prod.volume_conforme + prod.volume_declass
            d = data[essence]
            d['volume_total'] += volume_sorti
            d['nb_lignes'] += 1

            duree = prod.duree_traitement_min
            if duree > 0:
                arrets = _arrets_sur_creneau(equipe, prod.heure_debut, prod.heure_fin)
                temps_utile = max(0, duree - arrets)
                d['temps_planifie'] += duree
                d['arrets'] += arrets
                d['volume_temps'] += volume_sorti
                d['volume_conforme_temps'] += prod.volume_conforme
                d['volume_theorique'] += _capacite_h_essence(essence) * (temps_utile / 60)
                d['nb_lignes_temporalisees'] += 1
            elif equipe.trs_global is not None:
                d['trs_fallback'].append(equipe.trs_global)

    resultats = []
    for essence, d in data.items():
        if d['temps_planifie'] > 0:
            temps_utile = max(0, d['temps_planifie'] - d['arrets'])
            disponibilite = temps_utile / d['temps_planifie'] if d['temps_planifie'] else 0
            volume_theorique = d['volume_theorique']
            performance = (
                min(1.0, d['volume_temps'] / volume_theorique)
                if volume_theorique > 0 else 0
            )
            qualite = (
                d['volume_conforme_temps'] / d['volume_temps']
                if d['volume_temps'] > 0 else 0
            )
            trs = disponibilite * performance * qualite * 100
            resultats.append({
                'essence': essence,
                'volume_total': round(d['volume_total'], 2),
                'trs_moyen': round(trs, 1),
                'disponibilite': round(disponibilite * 100, 1),
                'performance': round(performance * 100, 1),
                'qualite': round(qualite * 100, 1),
                'temps_planifie': d['temps_planifie'],
                'duree_arrets': d['arrets'],
                'mode': 'temporalise',
                'couverture': round(d['nb_lignes_temporalisees'] / d['nb_lignes'] * 100, 0),
            })
        else:
            trs_vals = d['trs_fallback']
            resultats.append({
                'essence': essence,
                'volume_total': round(d['volume_total'], 2),
                'trs_moyen': round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else 0,
                'disponibilite': None,
                'performance': None,
                'qualite': None,
                'temps_planifie': 0,
                'duree_arrets': 0,
                'mode': 'poste',
                'couverture': 0,
            })

    return sorted(resultats, key=lambda x: x['volume_total'], reverse=True)

def calcule_trs(equipe):
    """
    Calcule et stocke les 3 composantes du TRS d'une équipe.
    Disponibilité : temps machine réel / temps poste officiel.
    Performance   : volume sorti / volume théorique sur temps utile.
    Qualité       : volume conforme / volume sorti (planches).
    """
    duree_poste = _param_float('duree_poste', 480)
    capacite_h  = _param_float('capacite_equipe_h', 1.5625)

    # Disponibilité
    duree_arrets = equipe.duree_arrets_impact
    temps_utile  = max(0, duree_poste - duree_arrets)
    disponibilite = temps_utile / duree_poste if duree_poste > 0 else 0

    # Performance
    temps_utile_h    = temps_utile / 60
    volume_theorique = capacite_h * temps_utile_h
    volume_sorti     = equipe.volume_sorti          # conforme + declass
    performance = min(1.0, volume_sorti / volume_theorique) if volume_theorique > 0 else 0

    # Qualité : conforme / (conforme + declass) — les déchets ne sont pas du "produit"
    volume_conforme = equipe.volume_conforme
    qualite = volume_conforme / volume_sorti if volume_sorti > 0 else 0

    trs_global = disponibilite * performance * qualite * 100

    equipe.trs_disponibilite = round(disponibilite * 100, 1)
    equipe.trs_performance   = round(performance * 100, 1)
    equipe.trs_qualite       = round(qualite * 100, 1)
    equipe.trs_global        = round(trs_global, 1)

    return {
        'disponibilite':    equipe.trs_disponibilite,
        'performance':      equipe.trs_performance,
        'qualite':          equipe.trs_qualite,
        'trs_global':       equipe.trs_global,
        'duree_arrets':     duree_arrets,
        'temps_utile':      temps_utile,
        'volume_theorique': round(volume_theorique, 2),
    }


def decompose_dpq(equipe):
    """
    Retourne (D, P, Q) en proportions (0-1) sans muter l'équipe.
    Utilise les valeurs stockées si présentes, sinon recalcule à partir
    des volumes et arrêts. Contrairement à calcule_trs, ne modifie rien.
    """
    if (equipe.trs_disponibilite is not None and
        equipe.trs_performance is not None and
        equipe.trs_qualite is not None):
        return (equipe.trs_disponibilite / 100,
                equipe.trs_performance / 100,
                equipe.trs_qualite / 100)

    duree_poste  = _param_float('duree_poste', 480)
    capacite_h   = _param_float('capacite_equipe_h', 1.5625)
    duree_arrets = equipe.duree_arrets_impact
    temps_utile  = max(0, duree_poste - duree_arrets)
    d = temps_utile / duree_poste if duree_poste > 0 else 0
    vol_theo  = capacite_h * (temps_utile / 60)
    vol_sorti = equipe.volume_sorti
    p = min(1.0, vol_sorti / vol_theo) if vol_theo > 0 else 0
    q = (equipe.volume_conforme / vol_sorti) if vol_sorti > 0 else 0
    return (d, p, q)


# ── Pertes financières ────────────────────────────────────────────────────────

def _prix_production(prod):
    """Retourne le prix/m³ d'une production (snapshot ou paramètre courant)."""
    if prod.prix_snapshot:
        return prod.prix_snapshot
    cle = f'prix_{normalise_essence(prod.essence)}'
    return float(Parametre.get(cle, 0))


def calcule_pertes_equipe(equipe):
    """
    Décompose les causes probables en FCFA indicatifs (D/P/Q).

    Perte D : valeur non produite pendant les arrêts impactants.
    Perte P : sous-performance vs capacité théorique sur le temps utile.
    Perte Q : perte déclassé (70% récupéré par défaut) + déchets sans valeur V1.

    Returns:
        dict {'perte_d', 'perte_p', 'perte_q', 'perte_q_declass', 'perte_q_dechets',
              'total_attribution', 'total'}
    """
    duree_poste      = _param_float('duree_poste', 480)
    capacite_h       = _param_float('capacite_equipe_h', 1.5625)
    taux_revente     = _param_float('taux_revente_rebut', 0.70)
    valeur_dechets_m3 = _param_float('valeur_dechets_m3', 0)

    duree_arrets_impactants = sum(a.duree_impact_min for a in equipe.arrets)
    temps_utile_h = max(0, duree_poste - duree_arrets_impactants) / 60

    # Prix moyen pondéré par volume sorti (D et P sont machine-level)
    total_vol = equipe.volume_sorti
    if total_vol > 0 and equipe.productions:
        prix_moyen = sum(
            _prix_production(p) * (p.volume_conforme + p.volume_declass)
            for p in equipe.productions
        ) / total_vol
    else:
        prix_moyen = 0.0

    # Perte D : production perdue pendant les arrêts qui impactent réellement le poste
    perte_d = (duree_arrets_impactants / 60) * capacite_h * prix_moyen

    # Perte P : sous-performance sur le temps utile
    volume_theorique = temps_utile_h * capacite_h
    perte_p = max(0.0, volume_theorique - total_vol) * prix_moyen

    # Perte Q déclassé : valeur nette perdue sur les planches déclassées
    perte_q_declass = sum(
        p.volume_declass * _prix_production(p) * (1 - taux_revente)
        for p in equipe.productions
    )

    # Perte Q déchets : potentiel non valorisé, avec valeur résiduelle paramétrable (0 en V1)
    perte_q_dechets = sum(
        p.volume_dechets * max(0, _prix_production(p) - valeur_dechets_m3)
        for p in equipe.productions
    )

    perte_q = perte_q_declass + perte_q_dechets
    total_attribution = perte_d + perte_p + perte_q

    return {
        'perte_d':          round(perte_d, 0),
        'perte_p':          round(perte_p, 0),
        'perte_q':          round(perte_q, 0),
        'perte_q_declass':  round(perte_q_declass, 0),
        'perte_q_dechets':  round(perte_q_dechets, 0),
        'total_attribution': round(total_attribution, 0),
        'total':            round(total_attribution, 0),
    }


def calcule_pertes_fcfa(equipe):
    """Raccourci officiel — retourne la perte financière nette CA potentiel − CA réel."""
    return calcule_manque_gagner(equipe)['manque_a_gagner_estime']


# ── Manque à gagner estimé (P11) ─────────────────────────────────────────────

def calcule_manque_gagner(equipe):
    """
    Manque à gagner estimé = valeur potentielle cible − valeur réelle valorisée.

    Approche économique directe (CA potentiel − CA valorisé), distincte de la
    décomposition D/P/Q de calcule_pertes_equipe(). Évite le double comptage
    car chaque m³ est compté dans UNE seule catégorie (conforme ou déclassé).

    - valeur_potentielle = capacité par essence × créneau × prix, si les créneaux existent
      fallback : objectif_m3 × prix moyen pondéré des essences traitées
    - valeur_conforme    = Σ (vol_conforme_essence_i × prix_snapshot_essence_i)
    - valeur_declass     = Σ (vol_declass_essence_i × prix_snapshot_essence_i × taux_revente)
    - valeur_dechets     = Σ (vol_dechets × valeur_dechets_m3), 0 FCFA/m³ en V1
    - valeur_reelle      = valeur_conforme + valeur_declass + valeur_dechets
    - manque_a_gagner    = max(0, valeur_potentielle − valeur_reelle)

    D/P/Q restent disponibles via calcule_pertes_equipe() pour l'attribution
    causale (pourquoi le manque existe), pas comme indicateur principal.

    Référence : Jonsson & Lesshammar (1999) — distinction "loss measurement"
    (chiffrage direct) vs "loss attribution" (diagnostic D × P × Q).
    """
    objectif_m3       = _param_float('objectif_m3', 12.5)
    taux_revente      = _param_float('taux_revente_rebut', 0.70)
    valeur_dechets_m3 = _param_float('valeur_dechets_m3', 0)

    volume_cible = 0.0
    valeur_potentielle_creneaux = 0.0
    for p in equipe.productions:
        if p.duree_traitement_min > 0:
            cible_p = _capacite_h_essence(p.essence) * (p.duree_traitement_min / 60)
            volume_cible += cible_p
            valeur_potentielle_creneaux += cible_p * _prix_production(p)

    vol_total = equipe.volume_sorti
    if vol_total > 0 and equipe.productions:
        prix_ref = sum(
            _prix_production(p) * (p.volume_conforme + p.volume_declass)
            for p in equipe.productions
        ) / vol_total
    else:
        prix_ref = 0.0

    if volume_cible > 0:
        valeur_potentielle = valeur_potentielle_creneaux
        prix_ref = valeur_potentielle / volume_cible if volume_cible > 0 else 0.0
        mode_potentiel = 'capacite_par_essence'
    else:
        volume_cible = objectif_m3
        valeur_potentielle = objectif_m3 * prix_ref
        mode_potentiel = 'objectif_poste'

    valeur_conforme = sum(
        p.volume_conforme * _prix_production(p)
        for p in equipe.productions
    )
    valeur_declass = sum(
        p.volume_declass * _prix_production(p) * taux_revente
        for p in equipe.productions
    )
    valeur_dechets = sum(
        p.volume_dechets * valeur_dechets_m3
        for p in equipe.productions
    )
    valeur_reelle = valeur_conforme + valeur_declass + valeur_dechets
    manque = max(0.0, valeur_potentielle - valeur_reelle)

    detail = [
        {
            'essence': p.essence,
            'volume_conforme': round(p.volume_conforme, 2),
            'volume_declass':  round(p.volume_declass, 2),
            'valeur_conforme': round(p.volume_conforme * _prix_production(p), 0),
            'valeur_declass':  round(p.volume_declass * _prix_production(p) * taux_revente, 0),
            'valeur_dechets':  round(p.volume_dechets * valeur_dechets_m3, 0),
        }
        for p in equipe.productions
    ]

    return {
        'objectif_m3':             objectif_m3,
        'volume_cible_m3':         round(volume_cible, 2),
        'mode_potentiel':          mode_potentiel,
        'taux_revente_declass':    taux_revente,
        'valeur_dechets_m3':       valeur_dechets_m3,
        'prix_reference':          round(prix_ref, 0),
        'valeur_potentielle':      round(valeur_potentielle, 0),
        'valeur_conforme':         round(valeur_conforme, 0),
        'valeur_declass':          round(valeur_declass, 0),
        'valeur_dechets':          round(valeur_dechets, 0),
        'valeur_reelle_valorisee': round(valeur_reelle, 0),
        'manque_a_gagner_estime':  round(manque, 0),
        'detail_par_essence':      detail,
    }


def manque_a_gagner_agrege(equipes):
    """
    Agrège le manque à gagner sur une liste d'équipes (jour/semaine/mois/an).
    Retourne les mêmes clés que calcule_manque_gagner(), sommées.
    """
    cumul = {
        'valeur_potentielle':      0.0,
        'valeur_conforme':         0.0,
        'valeur_declass':          0.0,
        'valeur_reelle_valorisee': 0.0,
        'manque_a_gagner_estime':  0.0,
        'nb_postes':               0,
    }
    for e in equipes:
        m = calcule_manque_gagner(e)
        cumul['valeur_potentielle']      += m['valeur_potentielle']
        cumul['valeur_conforme']         += m['valeur_conforme']
        cumul['valeur_declass']          += m['valeur_declass']
        cumul['valeur_reelle_valorisee'] += m['valeur_reelle_valorisee']
        cumul['manque_a_gagner_estime']  += m['manque_a_gagner_estime']
        cumul['nb_postes']               += 1
    return {k: (round(v, 0) if isinstance(v, float) else v) for k, v in cumul.items()}


# ── Cascade économique (Chef V2 — Vue 1 « LE POINT ») ─────────────────────────

def cascade_economique(equipes):
    """
    Cascade économique RÉCONCILIANTE pour le profil Chef V2.

    Recompose les sorties existantes de calcule_manque_gagner() en barres qui
    somment EXACTEMENT, même après arrondi :

        potentiel − perte_volume − perte_qualite = reel

    `perte_volume` est calculé en RÉSIDUEL (manque − perte_qualite). C'est ce
    qui garantit la réconciliation : il absorbe tout écart d'arrondi, donc la
    cascade affichée « tombe toujours juste ». Aucun calcul métier nouveau —
    pur réagencement de l'existant (contrat verrouillé 2026-06-08).

    Distinction assumée (Jonsson & Lesshammar, 1999) :
    - cette cascade = MESURE économique (combien on perd), réconciliée ;
    - la décomposition D/P/Q de calcule_pertes_equipe() = ATTRIBUTION causale
      (pourquoi on perd probablement), indicative, NON additive au manque.

    Champs sémantiques :
    - perte_volume  = valeur du bois jamais valorisé (arrêts + cadence cumulés).
    - perte_qualite = perte nette sur le bois déclassé revendu sous le prix
      conforme = valeur plein-tarif du déclassé − valeur réellement récupérée.

    Returns: dict {statut, potentiel, reel, manque, perte_volume,
                   perte_qualite, reconcilie}.
        statut == 'pas_de_perte' quand la production dépasse la capacité cible
        (sur-performance) : aucune barre de perte, garde-fou contre l'absurde.
    """
    taux = _param_float('taux_revente_rebut', 0.70)
    P = Vc = Vd_net = Vdech = 0.0
    for e in equipes:
        m = calcule_manque_gagner(e)
        P      += m['valeur_potentielle']
        Vc     += m['valeur_conforme']
        Vd_net += m['valeur_declass']        # DÉJÀ net (× taux_revente)
        Vdech  += m['valeur_dechets']

    potentiel = int(round(P))
    reel      = int(round(Vc + Vd_net + Vdech))

    if potentiel <= reel:
        return {
            'statut':        'pas_de_perte',
            'potentiel':     potentiel,
            'reel':          reel,
            'manque':        0,
            'perte_volume':  0,
            'perte_qualite': 0,
            'reconcilie':    True,
        }

    manque = potentiel - reel

    # Perte qualité = valeur plein tarif du déclassé − valeur nette récupérée.
    vd_full = (Vd_net / taux) if taux > 0 else Vd_net
    perte_qualite = int(round(vd_full - Vd_net))
    perte_qualite = max(0, min(perte_qualite, manque))   # garde-fou borné [0, manque]
    perte_volume  = manque - perte_qualite               # résiduel → ferme toujours

    return {
        'statut':        'perte',
        'potentiel':     potentiel,
        'reel':          reel,
        'manque':        manque,
        'perte_volume':  perte_volume,
        'perte_qualite': perte_qualite,
        'reconcilie':    (potentiel - perte_volume - perte_qualite == reel),
    }


# ── Pareto ────────────────────────────────────────────────────────────────────

def pareto_arrets(equipes):
    """
    Calcule le Pareto des causes d'arrêt sur une liste d'équipes.
    """
    from collections import defaultdict
    cumul = defaultdict(lambda: {'duree': 0, 'count': 0, 'categorie': ''})

    for equipe in equipes:
        for arret in equipe.arrets:
            if arret.duree_min:
                cumul[arret.cause]['duree']    += arret.duree_min
                cumul[arret.cause]['count']    += 1
                cumul[arret.cause]['categorie'] = arret.categorie

    total = sum(v['duree'] for v in cumul.values())
    if total == 0:
        return []

    resultats = sorted(
        [{'cause': k, **v} for k, v in cumul.items()],
        key=lambda x: x['duree'],
        reverse=True
    )

    cumul_pct = 0
    for r in resultats:
        r['pct'] = round(r['duree'] / total * 100, 1)
        cumul_pct += r['pct']
        r['pct_cumule'] = round(cumul_pct, 1)

    return resultats


# ── Utilitaires ───────────────────────────────────────────────────────────────

def couleur_trs(trs):
    """Couleur Bootstrap selon le niveau de TRS (vert ≥70%, orange ≥50%, rouge <50%)."""
    if trs is None:
        return 'secondary'
    if trs >= 70:
        return 'success'
    if trs >= 50:
        return 'warning'
    return 'danger'
