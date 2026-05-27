"""
Configuration de l'application wood_pilot.
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

    # Sécurité uploads : fiche papier PDF/photo, limite simple pour éviter les gros fichiers terrain.
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 8 * 1024 * 1024))

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
        'Panne machine',
        'Réglage / outil',
        'Mécanique',
        'Organisationnelle',
        'Approvisionnement',
        'Qualité matière',
        'Maintenance planifiée',
        'Énergie / réseau',
        'Autre'
    ]

    # Causes simples proposées à l'opérateur. La catégorie est remplie automatiquement.
    CAUSES_ARRET_PREDEFINIES = [
        {
            'cause': 'Panne machine',
            'categorie': 'Panne machine',
            'exemple': 'Moteur, roulement, courroie, capteur ou organe machine en panne.'
        },
        {
            'cause': 'Changement de lame',
            'categorie': 'Réglage / outil',
            'exemple': 'Remplacement normal ou urgent de lame, outil usé ou cassé.'
        },
        {
            'cause': 'Réglage machine',
            'categorie': 'Réglage / outil',
            'exemple': 'Ajustement de coupe, réglage longueur, alignement ou calibrage.'
        },
        {
            'cause': 'Manque de bois',
            'categorie': 'Approvisionnement',
            'exemple': 'La machine attend les grumes ou les pièces à l’entrée.'
        },
        {
            'cause': 'Bourrage / blocage bois',
            'categorie': 'Approvisionnement',
            'exemple': 'Grume ou pièce coincée, alimentation bloquée, évacuation saturée.'
        },
        {
            'cause': 'Maintenance prévue',
            'categorie': 'Maintenance planifiée',
            'exemple': 'Entretien planifié. Renseigner la durée prévue si elle est connue.',
            'duree_prevue_min': 30
        },
        {
            'cause': 'Qualité bois',
            'categorie': 'Qualité matière',
            'exemple': 'Grumes trop fendues, défauts matière, corps étrangers, bois difficile.'
        },
        {
            'cause': 'Coupure énergie',
            'categorie': 'Énergie / réseau',
            'exemple': 'Coupure électrique, baisse tension, air comprimé ou réseau indisponible.'
        },
        {
            'cause': 'Attente consigne / opérateur',
            'categorie': 'Organisationnelle',
            'exemple': 'Attente décision, absence opérateur, changement d’équipe ou consigne.'
        },
        {
            'cause': 'Nettoyage poste',
            'categorie': 'Organisationnelle',
            'exemple': 'Nettoyage machine, dégagement zone, rangement nécessaire.'
        },
        {
            'cause': 'Autre',
            'categorie': 'Autre',
            'exemple': 'Situation non prévue dans la liste. Décrire précisément dans la note.'
        },
    ]
