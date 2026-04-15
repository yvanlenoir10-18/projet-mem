"""
Données de test réalistes — Scierie CUF, Chaîne 4, Ebolowa.

Les valeurs sont basées sur le contexte réel du mémoire :
- Production réelle : 10 à 20 m³/poste
- Objectif affiché : 25 m³/poste
- TRS estimé < 60%
- Essences : Ayous, Azobé, Iroko, Movingui
- 2 postes par jour (Matin / Après-midi)
"""
from datetime import date, timedelta
from app import create_app
from app.models import db, Poste, Arret
from app.services.trs import calcule_trs

app = create_app()

# Données réalistes sur 3 semaines (21 jours = 42 postes, on en prend 16)
POSTES_TEST = [
    # --- Semaine 1 ---
    {
        'date': date.today() - timedelta(days=20),
        'numero_poste': 'Matin', 'essence': 'Ayous',
        'volume_entree': 32.0, 'volume_sorti': 14.5, 'volume_rebut': 1.2,
        'nb_conformes': 210, 'nb_defectueux': 18, 'effectif': 10,
        'notes': 'Démarrage difficile, lame émoussée',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '06:30', 'fin': '07:45',
             'cause': 'Remplacement lame émoussée', 'categorie': 'Maintenance planifiée'},
            {'machine': 'Bicoupe', 'debut': '11:20', 'fin': '11:50',
             'cause': 'Bourrage bois dans la lame', 'categorie': 'Mécanique'},
        ]
    },
    {
        'date': date.today() - timedelta(days=20),
        'numero_poste': 'Apres-midi', 'essence': 'Ayous',
        'volume_entree': 35.0, 'volume_sorti': 17.2, 'volume_rebut': 0.8,
        'nb_conformes': 250, 'nb_defectueux': 12, 'effectif': 9,
        'notes': 'Poste correct après changement de lame',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '15:10', 'fin': '15:40',
             'cause': 'Attente grumes — parc à grumes mal organisé', 'categorie': 'Approvisionnement'},
        ]
    },
    {
        'date': date.today() - timedelta(days=19),
        'numero_poste': 'Matin', 'essence': 'Iroko',
        'volume_entree': 28.0, 'volume_sorti': 11.0, 'volume_rebut': 2.5,
        'nb_conformes': 130, 'nb_defectueux': 35, 'effectif': 10,
        'notes': 'Iroko dur — beaucoup de rebuts, grumes noueuses',
        'arrets': [
            {'machine': 'Scie de tête', 'debut': '07:00', 'fin': '08:30',
             'cause': 'Panne moteur scie de tête', 'categorie': 'Mécanique'},
            {'machine': 'Bicoupe', 'debut': '10:15', 'fin': '10:45',
             'cause': 'Réglage bicoupe pour Iroko (essence plus dure)', 'categorie': 'Organisationnelle'},
            {'machine': 'Bicoupe', 'debut': '12:30', 'fin': '12:50',
             'cause': 'Grume avec corps étranger (clou)', 'categorie': 'Qualité matière'},
        ]
    },
    {
        'date': date.today() - timedelta(days=19),
        'numero_poste': 'Apres-midi', 'essence': 'Iroko',
        'volume_entree': 30.0, 'volume_sorti': 13.5, 'volume_rebut': 1.8,
        'nb_conformes': 185, 'nb_defectueux': 22, 'effectif': 10,
        'notes': '',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '14:00', 'fin': '14:25',
             'cause': 'Bourrage planches à la sortie bicoupe', 'categorie': 'Mécanique'},
        ]
    },
    # --- Semaine 1 suite ---
    {
        'date': date.today() - timedelta(days=17),
        'numero_poste': 'Matin', 'essence': 'Azobé',
        'volume_entree': 25.0, 'volume_sorti': 10.0, 'volume_rebut': 1.0,
        'nb_conformes': 110, 'nb_defectueux': 15, 'effectif': 8,
        'notes': 'Effectif réduit — 2 absents',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '06:00', 'fin': '07:30',
             'cause': 'Absence opérateur bicoupe — attente remplaçant', 'categorie': 'Organisationnelle'},
            {'machine': 'Déligneuse', 'debut': '09:40', 'fin': '10:10',
             'cause': 'Panne déligneuse — courroie cassée', 'categorie': 'Mécanique'},
        ]
    },
    {
        'date': date.today() - timedelta(days=17),
        'numero_poste': 'Apres-midi', 'essence': 'Azobé',
        'volume_entree': 27.0, 'volume_sorti': 15.8, 'volume_rebut': 0.6,
        'nb_conformes': 220, 'nb_defectueux': 8, 'effectif': 10,
        'notes': 'Bon poste — peu d\'arrêts',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '16:30', 'fin': '16:50',
             'cause': 'Affûtage lame préventif', 'categorie': 'Maintenance planifiée'},
        ]
    },
    # --- Semaine 2 ---
    {
        'date': date.today() - timedelta(days=14),
        'numero_poste': 'Matin', 'essence': 'Movingui',
        'volume_entree': 33.0, 'volume_sorti': 18.5, 'volume_rebut': 0.5,
        'nb_conformes': 280, 'nb_defectueux': 8, 'effectif': 10,
        'notes': 'Meilleur poste de la semaine — Movingui de bonne qualité',
        'arrets': []  # Aucun arrêt !
    },
    {
        'date': date.today() - timedelta(days=14),
        'numero_poste': 'Apres-midi', 'essence': 'Movingui',
        'volume_entree': 34.0, 'volume_sorti': 19.0, 'volume_rebut': 0.7,
        'nb_conformes': 290, 'nb_defectueux': 10, 'effectif': 10,
        'notes': '',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '18:10', 'fin': '18:30',
             'cause': 'Pause technique — transition équipe', 'categorie': 'Organisationnelle'},
        ]
    },
    {
        'date': date.today() - timedelta(days=13),
        'numero_poste': 'Matin', 'essence': 'Ayous',
        'volume_entree': 30.0, 'volume_sorti': 12.0, 'volume_rebut': 1.5,
        'nb_conformes': 165, 'nb_defectueux': 20, 'effectif': 9,
        'notes': 'Grumes de mauvaise qualité — beaucoup de nœuds',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '07:30', 'fin': '09:00',
             'cause': 'Panne hydraulique bicoupe', 'categorie': 'Mécanique'},
            {'machine': 'Bicoupe', 'debut': '11:00', 'fin': '11:30',
             'cause': 'Grumes trop petites — réglage nécessaire', 'categorie': 'Qualité matière'},
        ]
    },
    {
        'date': date.today() - timedelta(days=13),
        'numero_poste': 'Apres-midi', 'essence': 'Ayous',
        'volume_entree': 31.0, 'volume_sorti': 16.0, 'volume_rebut': 0.9,
        'nb_conformes': 230, 'nb_defectueux': 14, 'effectif': 10,
        'notes': '',
        'arrets': [
            {'machine': 'Scie de tête', 'debut': '14:30', 'fin': '15:00',
             'cause': 'Réglage hauteur de coupe scie de tête', 'categorie': 'Organisationnelle'},
        ]
    },
    # --- Semaine 3 (la plus récente) ---
    {
        'date': date.today() - timedelta(days=7),
        'numero_poste': 'Matin', 'essence': 'Iroko',
        'volume_entree': 29.0, 'volume_sorti': 13.0, 'volume_rebut': 2.0,
        'nb_conformes': 160, 'nb_defectueux': 28, 'effectif': 10,
        'notes': '',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '06:15', 'fin': '07:00',
             'cause': 'Remplacement lame émoussée', 'categorie': 'Maintenance planifiée'},
            {'machine': 'Bicoupe', 'debut': '10:45', 'fin': '11:15',
             'cause': 'Bourrage bois dans la lame', 'categorie': 'Mécanique'},
        ]
    },
    {
        'date': date.today() - timedelta(days=7),
        'numero_poste': 'Apres-midi', 'essence': 'Iroko',
        'volume_entree': 28.0, 'volume_sorti': 14.5, 'volume_rebut': 1.5,
        'nb_conformes': 195, 'nb_defectueux': 18, 'effectif': 10,
        'notes': '',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '15:30', 'fin': '16:00',
             'cause': 'Attente approvisionnement — grumes non prêtes', 'categorie': 'Approvisionnement'},
        ]
    },
    {
        'date': date.today() - timedelta(days=3),
        'numero_poste': 'Matin', 'essence': 'Movingui',
        'volume_entree': 36.0, 'volume_sorti': 20.0, 'volume_rebut': 0.4,
        'nb_conformes': 310, 'nb_defectueux': 6, 'effectif': 10,
        'notes': 'Meilleur poste du mois — bonne organisation, grumes bien triées',
        'arrets': []
    },
    {
        'date': date.today() - timedelta(days=3),
        'numero_poste': 'Apres-midi', 'essence': 'Azobé',
        'volume_entree': 26.0, 'volume_sorti': 11.5, 'volume_rebut': 1.1,
        'nb_conformes': 150, 'nb_defectueux': 16, 'effectif': 9,
        'notes': '',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '13:00', 'fin': '14:30',
             'cause': 'Panne hydraulique bicoupe', 'categorie': 'Mécanique'},
            {'machine': 'Bicoupe', 'debut': '17:20', 'fin': '17:50',
             'cause': 'Absence opérateur bicoupe', 'categorie': 'Organisationnelle'},
        ]
    },
    {
        'date': date.today() - timedelta(days=1),
        'numero_poste': 'Matin', 'essence': 'Ayous',
        'volume_entree': 33.0, 'volume_sorti': 16.8, 'volume_rebut': 0.7,
        'nb_conformes': 245, 'nb_defectueux': 11, 'effectif': 10,
        'notes': 'Poste d\'hier matin',
        'arrets': [
            {'machine': 'Bicoupe', 'debut': '09:00', 'fin': '09:30',
             'cause': 'Réglage bicoupe — changement diamètre grumes', 'categorie': 'Organisationnelle'},
        ]
    },
    {
        'date': date.today() - timedelta(days=1),
        'numero_poste': 'Apres-midi', 'essence': 'Ayous',
        'volume_entree': 34.0, 'volume_sorti': 17.5, 'volume_rebut': 0.6,
        'nb_conformes': 255, 'nb_defectueux': 9, 'effectif': 10,
        'notes': 'Poste d\'hier après-midi — correct',
        'arrets': [
            {'machine': 'Scie de tête', 'debut': '14:00', 'fin': '14:20',
             'cause': 'Affûtage préventif scie de tête', 'categorie': 'Maintenance planifiée'},
        ]
    },
]

def inserer_donnees():
    with app.app_context():
        # Effacer les données existantes (pour repartir propre)
        Arret.query.delete()
        Poste.query.delete()
        db.session.commit()
        print("Base nettoyée.")

        for i, data in enumerate(POSTES_TEST):
            poste = Poste(
                date=data['date'],
                numero_poste=data['numero_poste'],
                essence=data['essence'],
                volume_entree=data['volume_entree'],
                volume_sorti=data['volume_sorti'],
                volume_rebut=data['volume_rebut'],
                nb_planches_conformes=data['nb_conformes'],
                nb_planches_defectueuses=data['nb_defectueux'],
                effectif=data['effectif'],
                notes=data['notes'],
                user_id=1  # Agent de saisie
            )
            db.session.add(poste)
            db.session.flush()

            for a in data['arrets']:
                arret = Arret(
                    poste_id=poste.id,
                    machine=a['machine'],
                    heure_debut=a['debut'],
                    heure_fin=a['fin'],
                    cause=a['cause'],
                    categorie=a['categorie']
                )
                arret.calcule_duree()
                db.session.add(arret)

            db.session.flush()
            calcule_trs(poste)

            duree_arrets = poste.duree_totale_arrets
            print(f"  Poste {i+1:02d} | {poste.date} {poste.numero_poste:12s} | "
                  f"{poste.essence:9s} | {poste.volume_sorti:5.1f} m³ | "
                  f"Arrêts: {duree_arrets:3d} min | "
                  f"TRS: {poste.trs_global:5.1f}% "
                  f"(D={poste.trs_disponibilite}% P={poste.trs_performance}% Q={poste.trs_qualite}%)")

        db.session.commit()
        print(f"\n✓ {len(POSTES_TEST)} postes insérés avec succès.")


if __name__ == '__main__':
    inserer_donnees()
