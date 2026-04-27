"""
Service de calcul du TRS et des pertes financières — Scierie CUF, Chaîne 4.

TRS = Disponibilité × Performance × Qualité
Référence : Jonsson & Lesshammar (1999), fondateurs de l'OEE/TRS.

Pertes FCFA décomposées en 3 composantes :
  Perte D = arrêts non planifiés × capacité_h × prix_moyen_pondéré
  Perte P = (capacité_temps_utile − production_réelle) × prix_moyen_pondéré
  Perte Q = Σ(volume_sorti × %rebut × prix_essence × (1 − taux_revente))
"""
from ..models import Parametre, REBUT_NIVEAUX, normalise_essence


# ── TRS ──────────────────────────────────────────────────────────────────────

def calcule_trs(equipe):
    """
    Calcule et stocke les 3 composantes du TRS d'une équipe.
    Les arrêts sont partagés sur toute la durée du poste.
    La performance compare la production agrégée à la capacité théorique.
    """
    duree_poste = float(Parametre.get('duree_poste', 480))
    capacite_h  = float(Parametre.get('capacite_equipe_h', 1.5625))

    # Disponibilité
    duree_arrets = equipe.duree_totale_arrets
    temps_utile  = max(0, duree_poste - duree_arrets)
    disponibilite = temps_utile / duree_poste if duree_poste > 0 else 0

    # Performance
    temps_utile_h    = temps_utile / 60
    volume_theorique = capacite_h * temps_utile_h
    volume_sorti     = equipe.volume_sorti
    performance = min(1.0, volume_sorti / volume_theorique) if volume_theorique > 0 else 0

    # Qualité
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


# ── Pertes financières ────────────────────────────────────────────────────────

def _prix_production(prod):
    """Retourne le prix/m³ d'une production (snapshot ou paramètre courant)."""
    if prod.prix_snapshot:
        return prod.prix_snapshot
    cle = f'prix_{normalise_essence(prod.essence)}'
    return float(Parametre.get(cle, 0))


def calcule_pertes_equipe(equipe):
    """
    Décompose les pertes financières d'une équipe en FCFA (D + P + Q).

    Returns:
        dict {'perte_d', 'perte_p', 'perte_q', 'total'}
    """
    duree_poste   = float(Parametre.get('duree_poste', 480))
    capacite_h    = float(Parametre.get('capacite_equipe_h', 1.5625))
    taux_revente  = float(Parametre.get('taux_revente_rebut', 0.30))

    duree_arrets_non_planifies = sum(
        a.duree_min for a in equipe.arrets
        if a.duree_min and a.categorie != 'Maintenance planifiée'
    )
    duree_arrets_total = equipe.duree_totale_arrets
    temps_utile_h = max(0, duree_poste - duree_arrets_total) / 60

    # Prix moyen pondéré par volume (D et P sont machine-level)
    total_vol = equipe.volume_sorti
    if total_vol > 0 and equipe.productions:
        prix_moyen = sum(
            _prix_production(p) * p.volume_sorti
            for p in equipe.productions
        ) / total_vol
    else:
        prix_moyen = 0.0

    # Perte D : production perdue sur le temps d'arrêt non planifié
    perte_d = (duree_arrets_non_planifies / 60) * capacite_h * prix_moyen

    # Perte P : sous-performance sur le temps utile
    volume_theorique = temps_utile_h * capacite_h
    perte_p = max(0.0, volume_theorique - total_vol) * prix_moyen

    # Perte Q : valeur nette du rebut (après revente partielle) par essence
    perte_q = sum(
        p.volume_sorti * p.rebut_pct * _prix_production(p) * (1 - taux_revente)
        for p in equipe.productions
    )

    return {
        'perte_d': round(perte_d, 0),
        'perte_p': round(perte_p, 0),
        'perte_q': round(perte_q, 0),
        'total':   round(perte_d + perte_p + perte_q, 0),
    }


def calcule_pertes_fcfa(equipe):
    """Raccourci — retourne uniquement le montant total des pertes."""
    return calcule_pertes_equipe(equipe)['total']


# ── Pareto ────────────────────────────────────────────────────────────────────

def pareto_arrets(equipes):
    """
    Calcule le Pareto des causes d'arrêt sur une liste d'équipes.
    Interface inchangée : accepte tout objet ayant un attribut .arrets.
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
