"""
Service de calcul du TRS (Taux de Rendement Synthétique).

Formule : TRS = Disponibilité × Performance × Qualité
Référence : Jonsson & Lesshammar (1999), fondateurs de l'OEE/TRS en industrie.

Ce module est le cœur métier de l'application.
Il est appelé automatiquement après chaque saisie de poste.
"""
from ..models import Parametre


def calcule_trs(poste):
    """
    Calcule et met à jour les 3 composantes du TRS d'un poste.

    Args:
        poste: objet Poste avec ses arrêts déjà liés

    Returns:
        dict avec les 4 valeurs calculées (D, P, Q, TRS global)
    """
    duree_poste = float(Parametre.get('duree_poste', 480))       # minutes
    capacite_h  = float(Parametre.get('capacite_bicoupe', 4))    # m³/heure

    # --- 1. DISPONIBILITÉ ---
    # Temps pendant lequel la bicoupe était opérationnelle
    duree_arrets = sum(a.duree_min for a in poste.arrets if a.duree_min)
    temps_utile  = max(0, duree_poste - duree_arrets)
    disponibilite = temps_utile / duree_poste if duree_poste > 0 else 0

    # --- 2. PERFORMANCE ---
    # Rapport entre production réelle et production théorique
    # pendant le temps où la machine tournait
    temps_utile_h    = temps_utile / 60
    volume_theorique = capacite_h * temps_utile_h
    if volume_theorique > 0:
        performance = min(1.0, poste.volume_sorti / volume_theorique)
    else:
        performance = 0

    # --- 3. QUALITÉ ---
    # Part du volume produit qui est conforme (sans rebut)
    volume_conforme = max(0, poste.volume_sorti - poste.volume_rebut)
    if poste.volume_sorti > 0:
        qualite = volume_conforme / poste.volume_sorti
    else:
        qualite = 0

    # --- 4. TRS GLOBAL ---
    trs_global = disponibilite * performance * qualite * 100

    # Mettre à jour l'objet poste
    poste.trs_disponibilite = round(disponibilite * 100, 1)
    poste.trs_performance   = round(performance * 100, 1)
    poste.trs_qualite       = round(qualite * 100, 1)
    poste.trs_global        = round(trs_global, 1)

    return {
        'disponibilite': poste.trs_disponibilite,
        'performance':   poste.trs_performance,
        'qualite':       poste.trs_qualite,
        'trs_global':    poste.trs_global,
        'duree_arrets':  duree_arrets,
        'temps_utile':   temps_utile,
        'volume_theorique': round(volume_theorique, 2),
    }


def calcule_pertes_fcfa(poste):
    """
    Calcule la perte financière d'un poste en FCFA.
    Perte = (Objectif m³ - Produit réel m³) × Prix/m³ de l'essence.
    """
    objectif = float(Parametre.get('objectif_m3', 25))
    prix_cle  = f'prix_{poste.essence.lower()}'
    prix_m3   = float(Parametre.get(prix_cle, 0))

    production_perdue = max(0, objectif - poste.volume_sorti)
    return round(production_perdue * prix_m3, 0)


def pareto_arrets(postes):
    """
    Calcule le Pareto des causes d'arrêt sur une liste de postes.
    Retourne les causes triées par durée cumulée décroissante.
    Principe 80/20 : identifier les quelques causes qui causent la majorité des pertes.

    Args:
        postes: liste d'objets Poste

    Returns:
        liste de dicts {'cause', 'categorie', 'duree_totale', 'nb_occurrences', 'pct_cumule'}
    """
    from collections import defaultdict

    cumul = defaultdict(lambda: {'duree': 0, 'count': 0, 'categorie': ''})

    for poste in postes:
        for arret in poste.arrets:
            if arret.duree_min:
                cumul[arret.cause]['duree']    += arret.duree_min
                cumul[arret.cause]['count']    += 1
                cumul[arret.cause]['categorie'] = arret.categorie

    total = sum(v['duree'] for v in cumul.values())
    if total == 0:
        return []

    # Trier par durée décroissante
    resultats = sorted(
        [{'cause': k, **v} for k, v in cumul.items()],
        key=lambda x: x['duree'],
        reverse=True
    )

    # Ajouter le pourcentage cumulé (pour la courbe Pareto)
    cumul_pct = 0
    for r in resultats:
        r['pct'] = round(r['duree'] / total * 100, 1)
        cumul_pct += r['pct']
        r['pct_cumule'] = round(cumul_pct, 1)

    return resultats


def couleur_trs(trs):
    """
    Retourne la couleur Bootstrap selon le niveau de TRS.
    Vert > 70%, Orange 50-70%, Rouge < 50%.
    """
    if trs is None:
        return 'secondary'
    if trs >= 70:
        return 'success'
    if trs >= 50:
        return 'warning'
    return 'danger'
