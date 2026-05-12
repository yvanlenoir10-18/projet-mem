"""
Configuration de l'application Wood_Pilot_Ebolowa.
Les valeurs sensibles (SECRET_KEY) doivent être définies
dans les variables d'environnement en production.
"""
import os

class Config:
    # Clé secrète pour signer les cookies de session
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cuf-ebolowa-2026-change-en-prod')

    # Base de données : SQLite en développement
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'cuf.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Durée d'un poste en minutes (paramètre métier CUF)
    DUREE_POSTE_MINUTES = 480  # 8 heures

    # Essences traitées sur la Chaîne 4
    ESSENCES = ['Ayous', 'Azobé', 'Iroko', 'Movingui']

    # Machines de la Chaîne 4
    MACHINES = [
        'Bicoupe',
        'Scie de tête',
        'Déligneuse',
        'Ébouteuse',
        'Dédoubleuse',
        'Autre'
    ]

    # Catégories de causes d'arrêt
    CATEGORIES_ARRET = [
        'Mécanique',
        'Organisationnelle',
        'Approvisionnement',
        'Qualité matière',
        'Maintenance planifiée',
        'Autre'
    ]
