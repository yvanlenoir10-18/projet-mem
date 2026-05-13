"""
Moteur de recommandations — Couche 1 : règles déterministes.

Analyse les équipes d'une période et génère des recommandations prioritaires
basées sur les métriques observées : TRS, manque à gagner, anomalies de saisie,
tendance hebdomadaire.

Référence : Kankkunen & Holopainen (2024) — daily management UPM Plywood.
Les recommandations opérationnelles doivent être formulées à partir des données
terrain réelles, pas de benchmarks théoriques abstraits. Sans delta vs période
précédente, le PDG ne peut pas distinguer un problème nouveau d'un problème
chronique (Laine 2024).
"""
from datetime import date, timedelta
from ..models import Parametre


_REGLES = [
    {
        'code':      'TRS_CRITIQUE',
        'titre':     'TRS critique — intervention urgente',
        'icone':     'bi-speedometer2',
        'couleur':   'terracotta',
        'priorite':  3,
        'roles':     ['chef', 'admin'],
        'solutions': [
            {
                'titre': 'Analyser le Pareto des arrêts de la bicoupe',
                'detail': (
                    'La bicoupe est le goulot de la chaîne 4 — tout arrêt sur cette machine '
                    'arrête toute la production. Identifier les 3 causes les plus fréquentes '
                    'sur les 30 derniers jours et planifier des actions correctives ciblées. '
                    'Un TRS bas sans arrêts saisis indique des micro-arrêts non documentés.'
                ),
            },
            {
                'titre': 'Standardiser les procédures de démarrage de poste',
                'detail': (
                    'Un démarrage mal maîtrisé génère 15 à 45 minutes de perte de performance '
                    'à chaque poste. Définir un protocole en 5 étapes (tension lame, réglage '
                    'guide, essai sur rebut, vérification opérateur, départ chronométré) et '
                    'l\'afficher plastifié en cabine de commande.'
                ),
            },
            {
                'titre': 'Instaurer une fiche de maintenance préventive hebdomadaire',
                'detail': (
                    'Planifier 30 minutes de maintenance préventive en début de semaine : '
                    'tension et affûtage des lames, lubrification des guides, nettoyage des '
                    'copeaux dans le carter. La maintenance préventive réduit les pannes '
                    'imprévues de 40 à 60 % selon Mncwango & Mdunge (2025).'
                ),
            },
        ],
    },
    {
        'code':      'TRS_MOYEN',
        'titre':     'TRS sous l\'objectif — amélioration possible',
        'icone':     'bi-graph-up-arrow',
        'couleur':   'ochre',
        'priorite':  2,
        'roles':     ['chef', 'admin'],
        'solutions': [
            {
                'titre': 'Cibler les 3 premières causes d\'arrêt du Pareto',
                'detail': (
                    'Les 3 premières causes d\'arrêt représentent en général 70 à 80 % du '
                    'temps perdu. Consulter la vue Pareto du tableau de bord chef et planifier '
                    'une action corrective sur chaque cause avant la fin de la semaine.'
                ),
            },
            {
                'titre': 'Regrouper les lots par essence pour réduire les transitions',
                'detail': (
                    'Chaque changement d\'essence (ex. Ayous → Azobé) nécessite un '
                    'recalibrage de la bicoupe : vitesse d\'avance, pression de coupe, '
                    'réglage du guide. Regrouper les lots de même essence et établir un '
                    'ordre de traitement : bois tendres en début de poste (Ayous), bois '
                    'durs en fin (Azobé, Iroko).'
                ),
            },
            {
                'titre': 'Former les opérateurs aux réglages rapides après arrêt',
                'detail': (
                    'Les opérateurs qui maîtrisent les réglages fins réduisent les temps '
                    'de remise en route de 30 à 50 %. Organiser une session pratique de '
                    '2 heures sur le réglage de la bicoupe selon la section des grumes, '
                    'animée par le chef de production ou le mécanicien référent.'
                ),
            },
        ],
    },
    {
        'code':      'MANQUE_ELEVE',
        'titre':     'Manque à gagner élevé — impact financier significatif',
        'icone':     'bi-cash-stack',
        'couleur':   'terracotta',
        'priorite':  3,
        'roles':     ['pdg', 'admin'],
        'solutions': [
            {
                'titre': 'Prioriser les essences à haute valeur en début de poste',
                'detail': (
                    'L\'Azobé (120 000 FCFA/m³) et l\'Iroko (110 000 FCFA/m³) génèrent '
                    '30 à 40 % de valeur supplémentaire par m³ par rapport à l\'Ayous. '
                    'Traiter ces essences quand les opérateurs sont les plus vigilants '
                    '(début de poste) réduit le déclassé et maximise la valeur produite.'
                ),
            },
            {
                'titre': 'Réduire le taux de déclassé par le contrôle des lames',
                'detail': (
                    'Une lame émoussée augmente le taux de déclassé de 15 à 25 % selon '
                    'Danwé et al. (2012) sur les scieries camerounaises. Définir un seuil '
                    'de remplacement en m³ débités (ex. toutes les 100 m³) plutôt qu\'en '
                    'nombre de jours — la production variable rend le critère temporel peu '
                    'fiable.'
                ),
            },
            {
                'titre': 'Optimiser le plan de débit selon la section des grumes',
                'detail': (
                    'Un plan de débit adapté à la section de la grume peut réduire les '
                    'pertes matière de 10 à 15 %. Pour chaque grume entrante, choisir le '
                    'plan (plateau central, plot) qui maximise le rendement conforme selon '
                    'son diamètre et ses défauts apparents.'
                ),
            },
        ],
    },
    {
        'code':      'ARRETS_NON_DOCUMENTES',
        'titre':     'Arrêts non documentés — données insuffisantes pour agir',
        'icone':     'bi-file-earmark-x',
        'couleur':   'ochre',
        'priorite':  2,
        'roles':     ['chef', 'admin'],
        'solutions': [
            {
                'titre': 'Former les chefs de poste à la documentation des arrêts',
                'detail': (
                    'Un arrêt non documenté est une opportunité d\'amélioration perdue. '
                    'Former chaque chef de poste à saisir systématiquement : machine, '
                    'heure début/fin, cause et mesure prise. La formation sur des cas '
                    'réels extraits de l\'historique de CUF est plus efficace qu\'une '
                    'formation théorique générique.'
                ),
            },
            {
                'titre': 'Afficher un rappel visuel en cabine',
                'detail': (
                    'Placer une affiche plastifiée A4 à côté de la tablette de saisie : '
                    '"Tout arrêt > 10 min doit être documenté avant la fin du poste." '
                    'Ce rappel visuel simple augmente le taux de conformité de 50 à 70 % '
                    'dans les études de management visuel terrain (Laine 2024).'
                ),
            },
            {
                'titre': 'Instituer une revue hebdomadaire des saisies incomplètes',
                'detail': (
                    'Chaque lundi matin, le chef production examine les alertes R2 de la '
                    'semaine précédente avec les chefs de poste concernés. Cette revue '
                    'rapide de 15 minutes crée une responsabilisation progressive et '
                    'améliore la qualité des saisies futures sans sanction immédiate.'
                ),
            },
        ],
    },
    {
        'code':      'DECLASS_EXCESSIF',
        'titre':     'Déclassé excessif — perte qualité matière',
        'icone':     'bi-exclamation-diamond',
        'couleur':   'terracotta',
        'priorite':  3,
        'roles':     ['chef', 'pdg', 'admin'],
        'solutions': [
            {
                'titre': 'Vérifier et remplacer les lames de la bicoupe',
                'detail': (
                    'Une lame émoussée ou mal affûtée est la première cause de déclassé '
                    'excessif dans les scieries camerounaises (Danwé et al. 2012). Instaurer '
                    'un suivi du volume débité par lame et définir un seuil de remplacement '
                    'préventif plutôt que de remplacer en urgence après la casse.'
                ),
            },
            {
                'titre': 'Contrôler la qualité des grumes à l\'entrée du parc',
                'detail': (
                    'Les grumes avec nœuds importants, poches de résine ou défauts de '
                    'rectitude génèrent davantage de déclassé. Instaurer un tri visuel '
                    'rapide au parc à grumes pour orienter les grumes défectueuses vers '
                    'des plans de débit adaptés (chevrons, bois de palette) et préserver '
                    'les meilleures grumes pour les sciages nobles.'
                ),
            },
            {
                'titre': 'Fiche de réglage par essence en cabine de bicoupe',
                'detail': (
                    'L\'Azobé et l\'Iroko sont des bois durs qui nécessitent une vitesse '
                    'd\'avance réduite et une pression de coupe plus élevée. Afficher à '
                    'la bicoupe une fiche plastifiée avec les réglages par essence, pour '
                    'que chaque opérateur applique les bons paramètres sans approximation.'
                ),
            },
        ],
    },
    {
        'code':      'SAISIES_INCOHERENTES',
        'titre':     'Saisies incohérentes — fiabilité des données à améliorer',
        'icone':     'bi-shield-exclamation',
        'couleur':   'ochre',
        'priorite':  1,
        'roles':     ['chef', 'admin'],
        'solutions': [
            {
                'titre': 'Session de formation pratique sur la saisie',
                'detail': (
                    'Réunir tous les chefs de poste pour 1 heure : présentation des 4 règles '
                    'de cohérence, exercices sur des cas réels extraits de l\'historique CUF, '
                    'questions/réponses. La formation sur des exemples concrets du site est '
                    'significativement plus efficace que les formations théoriques génériques.'
                ),
            },
            {
                'titre': 'Validation superviseur pour les saisies à risque',
                'detail': (
                    'Le chef de production vérifie les saisies signalées en anomalie (TRS '
                    '< 50 % ou volume = 0) avant soumission définitive. Cette vérification '
                    'ne prend que 2 minutes mais évite d\'intégrer des données erronées '
                    'dans les calculs de performance.'
                ),
            },
            {
                'titre': 'Ajouter des exemples concrets dans le formulaire',
                'detail': (
                    'Pour les champs les plus souvent mal remplis (commentaire d\'arrêt, '
                    'volume déclassé), ajouter un texte d\'aide : "Exemple : Remplacement '
                    'courroie principale, bicoupe arrêtée 45 min." Les exemples concrets '
                    'réduisent les erreurs de saisie de 40 à 60 % selon Mncwango & Mdunge.'
                ),
            },
        ],
    },
    {
        'code':      'TENDANCE_NEGATIVE',
        'titre':     'Tendance baissière — dérive à corriger rapidement',
        'icone':     'bi-graph-down-arrow',
        'couleur':   'terracotta',
        'priorite':  3,
        'roles':     ['pdg', 'admin'],
        'solutions': [
            {
                'titre': 'Réunion flash de 15 minutes en début de semaine',
                'detail': (
                    'Une réunion debout avec le chef de production, un chef de poste et '
                    'un opérateur senior suffit pour identifier la cause principale de la '
                    'dérive. L\'objectif n\'est pas un diagnostic complet mais une action '
                    'immédiate testable dès le même jour (Kankkunen & Holopainen 2024).'
                ),
            },
            {
                'titre': 'Vérifier si le mix d\'essences a changé entre les deux périodes',
                'detail': (
                    'Une semaine avec davantage d\'Azobé ou d\'Iroko (bois durs) peut '
                    'expliquer une baisse du TRS sans défaillance organisationnelle. '
                    'Comparer le mix d\'essences des deux semaines dans l\'historique '
                    'avant de conclure à une dérive opérationnelle.'
                ),
            },
            {
                'titre': 'Comparer le TRS par shift pour isoler la source',
                'detail': (
                    'Une baisse concentrée sur le shift Matin ou Après-midi pointe vers '
                    'un facteur humain ou d\'encadrement. Comparer les TRS par shift sur '
                    'les deux périodes dans le tableau de bord chef — si la dérive est '
                    'localisée, l\'action corrective est ciblée et rapide.'
                ),
            },
        ],
    },
]

_INDEX_REGLES = {r['code']: r for r in _REGLES}


def analyse_recommandations(equipes):
    """
    Analyse une liste d'équipes et retourne les recommandations actives,
    triées par priorité décroissante.

    Retourne une liste de dicts (copie enrichie des _REGLES) avec un champ
    'contexte' contenant les métriques ayant déclenché la règle.
    """
    if not equipes:
        return []

    from .trs import manque_a_gagner_agrege
    from .controles_saisie import detecte_anomalies

    nb_postes = len(equipes)
    trs_vals  = [e.trs_global for e in equipes if e.trs_global is not None]
    trs_moyen = round(sum(trs_vals) / len(trs_vals), 1) if trs_vals else None

    manque = manque_a_gagner_agrege(equipes).get('manque_a_gagner_estime', 0.0)

    # Comptage des anomalies par code
    nb_r1 = nb_r2 = nb_r3 = nb_r4 = 0
    for e in equipes:
        for a in detecte_anomalies(e):
            if   a['code'] == 'R1': nb_r1 += 1
            elif a['code'] == 'R2': nb_r2 += 1
            elif a['code'] == 'R3': nb_r3 += 1
            elif a['code'] == 'R4': nb_r4 += 1

    pct_r2    = round(nb_r2 / nb_postes * 100, 1)
    pct_r3    = round(nb_r3 / nb_postes * 100, 1)
    pct_r1_r4 = round((nb_r1 + nb_r4) / nb_postes * 100, 1)

    # Seuils configurables via Parametre
    seuil_trs_critique  = float(Parametre.get('seuil_trs_critique',   '50'))
    seuil_trs_moyen     = float(Parametre.get('seuil_trs_moyen',      '60'))
    seuil_manque        = float(Parametre.get('seuil_manque_eleve',   '500000'))
    seuil_anomalie_pct  = float(Parametre.get('seuil_anomalies_pct',  '30'))

    contexte = {
        'trs_moyen':  trs_moyen,
        'manque':     manque,
        'nb_postes':  nb_postes,
        'pct_r2':     pct_r2,
        'pct_r3':     pct_r3,
        'pct_r1_r4':  pct_r1_r4,
    }

    actives = []

    # TRS critique ou moyen (mutuellement exclusifs)
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

    if pct_r1_r4 > 20.0:
        actives.append('SAISIES_INCOHERENTES')

    # Tendance négative : manque à gagner en hausse > 10 % cette semaine vs précédente
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
        regle['contexte'] = contexte
        result.append(regle)

    result.sort(key=lambda r: r['priorite'], reverse=True)
    return result


def top_n_recommandations(equipes, role, n=3):
    """Retourne les n recommandations les plus prioritaires pour un rôle donné."""
    all_recos = analyse_recommandations(equipes)
    return [r for r in all_recos if role in r['roles']][:n]
