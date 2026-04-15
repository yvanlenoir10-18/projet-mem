"""
Application Factory — CUF Pilotage Chaîne 4.

Le pattern Application Factory permet de créer l'application
de manière configurable : utile pour les tests et le déploiement.
"""
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from config import Config


login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Connectez-vous pour accéder à cette page.'
    login_manager.login_message_category = 'warning'

    # Enregistrer les blueprints (groupes de routes)
    from .routes.auth import auth_bp
    from .routes.saisie import saisie_bp
    from .routes.dashboard import dashboard_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(saisie_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)

    # Créer les tables si elles n'existent pas
    with app.app_context():
        db.create_all()
        _init_donnees_defaut()

    return app


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login appelle cette fonction pour retrouver un utilisateur par son ID."""
    return User.query.get(int(user_id))


def _init_donnees_defaut():
    """
    Insère les données de base au premier démarrage :
    - Un compte admin (agent de saisie)
    - Un compte chef scierie
    - Un compte PDG
    - Les paramètres CUF par défaut (prix, objectifs)
    """
    from .models import User, Parametre

    # Créer les utilisateurs par défaut s'ils n'existent pas
    if not User.query.first():
        users = [
            {'nom': 'Agent Saisie', 'email': 'saisie@cuf.cm', 'role': 'admin', 'mdp': 'cuf2026'},
            {'nom': 'Chef Scierie', 'email': 'chef@cuf.cm', 'role': 'chef', 'mdp': 'cuf2026'},
            {'nom': 'Directeur', 'email': 'pdg@cuf.cm', 'role': 'pdg', 'mdp': 'cuf2026'},
        ]
        for u in users:
            utilisateur = User(nom=u['nom'], email=u['email'], role=u['role'])
            utilisateur.set_password(u['mdp'])
            db.session.add(utilisateur)

    # Créer les paramètres par défaut s'ils n'existent pas
    if not Parametre.query.first():
        parametres = [
            ('prix_ayous',    '85000',  'Prix de vente Ayous (FCFA/m³)'),
            ('prix_azobe',    '120000', 'Prix de vente Azobé (FCFA/m³)'),
            ('prix_iroko',    '110000', 'Prix de vente Iroko (FCFA/m³)'),
            ('prix_movingui', '95000',  'Prix de vente Movingui (FCFA/m³)'),
            ('objectif_m3',   '25',     'Objectif production par poste (m³)'),
            ('duree_poste',   '480',    'Durée officielle d\'un poste (minutes)'),
            ('capacite_bicoupe', '4',   'Capacité théorique bicoupe (m³/heure)'),
        ]
        for cle, valeur, desc in parametres:
            db.session.add(Parametre(cle=cle, valeur=valeur, description=desc))

    db.session.commit()
