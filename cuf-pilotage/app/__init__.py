"""
Application Factory — Wood_Pilot_Ebolowa, Chaîne 4 CUF.
"""
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from config import Config

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Connectez-vous pour accéder à cette page.'
    login_manager.login_message_category = 'warning'

    from .routes.auth import auth_bp
    from .routes.saisie import saisie_bp
    from .routes.dashboard import dashboard_bp
    from .routes.admin import admin_bp
    from .routes.analyse import analyse_bp
    from .routes.recommandations import recos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(saisie_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analyse_bp)
    app.register_blueprint(recos_bp)

    with app.app_context():
        db.create_all()
        _init_donnees_defaut()
        _seed_donnees_demo()

    from flask import render_template

    @app.errorhandler(404)
    def page_introuvable(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def erreur_serveur(e):
        return render_template('errors/500.html'), 500

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def _init_donnees_defaut():
    from .models import User, Parametre

    if not User.query.first():
        users = [
            {'nom': 'Agent Saisie', 'email': 'saisie@cuf.cm', 'role': 'admin', 'mdp': 'cuf2026'},
            {'nom': 'Chef Scierie', 'email': 'chef@cuf.cm',   'role': 'chef',  'mdp': 'cuf2026'},
            {'nom': 'Directeur',    'email': 'pdg@cuf.cm',    'role': 'pdg',   'mdp': 'cuf2026'},
        ]
        for u in users:
            utilisateur = User(nom=u['nom'], email=u['email'], role=u['role'])
            utilisateur.set_password(u['mdp'])
            db.session.add(utilisateur)

    if not Parametre.query.first():
        parametres = [
            # Prix de vente par essence (FCFA/m³)
            ('prix_ayous',         '85000',  'Prix de vente Ayous (FCFA/m³)'),
            ('prix_azobe',         '120000', 'Prix de vente Azobé (FCFA/m³)'),
            ('prix_iroko',         '110000', 'Prix de vente Iroko (FCFA/m³)'),
            ('prix_movingui',      '95000',  'Prix de vente Movingui (FCFA/m³)'),
            # Paramètres de production
            ('objectif_m3',        '12.5',   'Objectif de production par équipe (m³) — V1 provisoire'),
            ('duree_poste',        '480',    'Durée officielle d\'un poste (minutes)'),
            ('capacite_equipe_h',  '1.5625', 'Capacité théorique de la ligne (m³/heure) — 12.5m³/8h'),
            # Paramètre financier
            ('taux_revente_rebut', '0.30',   'Taux de revente locale du bois rebut (30%)'),
        ]
        for cle, valeur, desc in parametres:
            db.session.add(Parametre(cle=cle, valeur=valeur, description=desc))

    # P12 — Seuils des contrôles qualité de saisie (ajoutés sur instances existantes)
    seuils_controles = [
        ('seuil_trs_anomalie',               '40', 'TRS (%) sous lequel l\'absence d\'arrêt déclaré est suspecte'),
        ('seuil_arret_long_minutes',         '60', 'Durée (min) à partir de laquelle un commentaire est attendu'),
        ('seuil_arret_long_commentaire_min', '10', 'Longueur minimale (caractères) du commentaire pour un arrêt long'),
        ('seuil_declass_pct',                '30', 'Part (%) de volume déclassé déclenchant une alerte qualité'),
    ]
    for cle, valeur, desc in seuils_controles:
        if not Parametre.query.filter_by(cle=cle).first():
            db.session.add(Parametre(cle=cle, valeur=valeur, description=desc))

    # P14 — Seuils du moteur de recommandations + sources IA
    seuils_recos = [
        ('seuil_trs_critique',   '50',       'TRS (%) sous lequel une recommandation TRS_CRITIQUE est générée'),
        ('seuil_trs_moyen',      '60',       'TRS (%) sous lequel une recommandation TRS_MOYEN est générée'),
        ('seuil_manque_eleve',   '500000',   'Manque à gagner (FCFA) au-delà duquel MANQUE_ELEVE est générée'),
        ('seuil_anomalies_pct',  '30',       'Part (%) de postes avec anomalie déclenchant une recommandation'),
        ('reco_sources_externes','[]',        'JSON — liste d\'URLs chargées par l\'IA pour enrichir ses réponses'),
    ]
    for cle, valeur, desc in seuils_recos:
        if not Parametre.query.filter_by(cle=cle).first():
            db.session.add(Parametre(cle=cle, valeur=valeur, description=desc))

    db.session.commit()


def _seed_donnees_demo():
    """Crée des données de démonstration si aucune équipe n'existe."""
    from datetime import date as d, datetime
    from .models import Equipe, Production, Arret

    if Equipe.query.first():
        return

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        return

    specs = [
        # Mai 2026 — données courantes
        (d(2026, 5, 1), 'Matin', 'soumis', 68.0,
         [('Ayous', 8.0, 5.0, 0.5), ('Azobé', 5.0, 3.0, 0.3)],
         [('Bicoupe', '08:15', '09:00', 'Remplacement courroie', 'Mécanique'),
          ('Déligneuse', '10:30', '10:50', 'Attente opérateur', 'Organisationnelle')]),
        (d(2026, 5, 1), 'Apres-midi', 'soumis', 72.0,
         [('Iroko', 9.0, 6.0, 0.5)],
         []),
        (d(2026, 5, 2), 'Matin', 'soumis', 58.0,
         [('Movingui', 6.0, 3.5, 0.5), ('Ayous', 5.0, 3.0, 0.3)],
         [('Scie de tête', '07:30', '08:30', 'Tension lame', 'Mécanique'),
          ('Bicoupe', '10:00', '10:30', 'Pause non planifiée', 'Organisationnelle')]),
        (d(2026, 5, 2), 'Apres-midi', 'soumis', 74.0,
         [('Azobé', 7.0, 4.5, 0.4)],
         [('Ébouteuse', '15:00', '15:20', 'Réglage longueur', 'Maintenance planifiée')]),
        (d(2026, 5, 3), 'Matin', 'brouillon', None,
         [('Iroko', 5.0, 3.0, 0.3)],
         []),
        # Avril 2026 — pour le delta TRS et la tendance
        (d(2026, 4, 1), 'Matin', 'soumis', 60.0,
         [('Ayous', 8.0, 4.5, 0.4), ('Azobé', 5.0, 2.8, 0.3)],
         [('Bicoupe', '08:00', '09:15', 'Blocage grumes', 'Approvisionnement')]),
        (d(2026, 4, 1), 'Apres-midi', 'soumis', 65.0,
         [('Iroko', 8.0, 5.0, 0.5)],
         []),
        (d(2026, 4, 15), 'Matin', 'soumis', 63.0,
         [('Movingui', 7.0, 4.2, 0.4), ('Ayous', 4.0, 2.4, 0.2)],
         [('Bicoupe', '09:00', '09:45', 'Remplacement lame', 'Mécanique')]),
        # Mars 2026 — tendance
        (d(2026, 3, 10), 'Matin', 'soumis', 55.0,
         [('Ayous', 8.0, 4.0, 0.4)],
         [('Bicoupe', '08:00', '09:30', 'Panne moteur', 'Mécanique')]),
        # Février 2026 — tendance
        (d(2026, 2, 15), 'Matin', 'soumis', 62.0,
         [('Azobé', 9.0, 5.2, 0.5)],
         []),
    ]

    for (date_eq, num_eq, statut, trs, prods, arrets) in specs:
        eq = Equipe(
            date=date_eq,
            numero_equipe=num_eq,
            statut=statut,
            trs_global=trs,
            user_id=admin.id,
            soumis_le=datetime.utcnow() if statut in ('soumis', 'verrouille') else None,
        )
        db.session.add(eq)
        db.session.flush()

        for (essence, entree, conforme, declass) in prods:
            db.session.add(Production(
                equipe_id=eq.id,
                essence=essence,
                volume_entree=entree,
                volume_conforme=conforme,
                volume_declass=declass,
            ))

        for (machine, h_d, h_f, cause, categorie) in arrets:
            a = Arret(
                equipe_id=eq.id,
                machine=machine,
                heure_debut=h_d,
                heure_fin=h_f,
                cause=cause,
                categorie=categorie,
            )
            a.calcule_duree()
            db.session.add(a)

    db.session.commit()
