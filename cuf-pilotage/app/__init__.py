"""
Application Factory — CUF Pilotage Chaîne 4.
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(saisie_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analyse_bp)

    with app.app_context():
        db.create_all()
        _init_donnees_defaut()

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

    db.session.commit()
