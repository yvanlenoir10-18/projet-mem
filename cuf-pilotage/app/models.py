"""
Modèles de données — Scierie CUF, Chaîne 4.

Chaque classe correspond à une table dans la base de données SQLite.
SQLAlchemy traduit automatiquement les classes Python en tables SQL.
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    Utilisateur de l'application.
    Trois rôles possibles : 'admin' (agent saisie), 'chef' (chef scierie), 'pdg'.
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')  # admin | chef | pdg
    actif = db.Column(db.Boolean, default=True)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    # Un utilisateur peut saisir plusieurs postes
    postes = db.relationship('Poste', backref='saisie_par', lazy=True)

    def set_password(self, mot_de_passe):
        """Chiffre le mot de passe avec bcrypt avant de le stocker."""
        self.password_hash = bcrypt.hashpw(
            mot_de_passe.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, mot_de_passe):
        """Vérifie si le mot de passe fourni correspond au hash stocké."""
        return bcrypt.checkpw(
            mot_de_passe.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def __repr__(self):
        return f'<User {self.nom} ({self.role})>'


class Parametre(db.Model):
    """
    Paramètres configurables de l'application.
    Stockés sous forme clé/valeur pour rester flexibles.
    Ex : 'prix_ayous' -> '85000', 'objectif_m3_poste' -> '25'
    """
    __tablename__ = 'parametre'

    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(50), unique=True, nullable=False)
    valeur = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200))
    mis_a_jour_le = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(cle, defaut=None):
        """Récupère la valeur d'un paramètre par sa clé."""
        p = Parametre.query.filter_by(cle=cle).first()
        return p.valeur if p else defaut

    def __repr__(self):
        return f'<Parametre {self.cle}={self.valeur}>'


class Poste(db.Model):
    """
    Un poste de travail de 8 heures sur la Chaîne 4.
    C'est l'unité de base de la collecte de données.
    TRS calculé automatiquement depuis les arrêts et les volumes.
    """
    __tablename__ = 'poste'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    numero_poste = db.Column(db.String(10), nullable=False)  # 'Matin' | 'Apres-midi'
    essence = db.Column(db.String(50), nullable=False)       # Ayous, Azobé, Iroko, Movingui

    # --- Données de production ---
    volume_entree = db.Column(db.Float, nullable=False)   # m³ grumes en entrée
    volume_sorti = db.Column(db.Float, nullable=False)    # m³ bois scié en sortie
    volume_rebut = db.Column(db.Float, default=0.0)       # m³ rebut/perte
    nb_planches_conformes = db.Column(db.Integer, default=0)
    nb_planches_defectueuses = db.Column(db.Integer, default=0)
    effectif = db.Column(db.Integer, default=10)          # Nb opérateurs présents

    # --- TRS calculé automatiquement ---
    trs_disponibilite = db.Column(db.Float)   # % de disponibilité
    trs_performance = db.Column(db.Float)     # % de performance
    trs_qualite = db.Column(db.Float)         # % de qualité
    trs_global = db.Column(db.Float)          # TRS = D × P × Q

    # --- Métadonnées ---
    notes = db.Column(db.Text)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Un poste contient plusieurs arrêts
    arrets = db.relationship('Arret', backref='poste', lazy=True,
                              cascade='all, delete-orphan')

    @property
    def duree_totale_arrets(self):
        """Somme en minutes de tous les arrêts du poste."""
        return sum(a.duree_min for a in self.arrets if a.duree_min)

    @property
    def rendement_matiere(self):
        """Volume scié / Volume entré × 100 (en %)."""
        if self.volume_entree and self.volume_entree > 0:
            return round((self.volume_sorti / self.volume_entree) * 100, 1)
        return 0

    @property
    def volume_conforme(self):
        """Volume scié moins le volume rebut."""
        return max(0, self.volume_sorti - self.volume_rebut)

    def __repr__(self):
        return f'<Poste {self.date} {self.numero_poste} {self.essence} TRS={self.trs_global}%>'


class Arret(db.Model):
    """
    Un arrêt machine survenu pendant un poste.
    La durée est calculée automatiquement depuis heure_debut et heure_fin.
    C'est la donnée la plus importante pour le Pareto et l'analyse des causes racines.
    """
    __tablename__ = 'arret'

    id = db.Column(db.Integer, primary_key=True)
    poste_id = db.Column(db.Integer, db.ForeignKey('poste.id'), nullable=False)

    # --- Identification de l'arrêt ---
    machine = db.Column(db.String(50), nullable=False)     # Bicoupe, Scie de tête, etc.
    heure_debut = db.Column(db.String(5), nullable=False)  # Format HH:MM ex: "07:30"
    heure_fin = db.Column(db.String(5), nullable=False)    # Format HH:MM ex: "08:15"
    duree_min = db.Column(db.Integer)                      # Calculée automatiquement

    # --- Analyse des causes ---
    cause = db.Column(db.String(200), nullable=False)      # Description détaillée
    categorie = db.Column(db.String(50), nullable=False)   # Mécanique | Organisationnelle | etc.
    notes = db.Column(db.Text)

    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    def calcule_duree(self):
        """
        Calcule automatiquement la durée en minutes depuis heure_debut et heure_fin.
        Ex: debut=07:30, fin=08:15 → durée=45 minutes
        """
        try:
            h_debut, m_debut = map(int, self.heure_debut.split(':'))
            h_fin, m_fin = map(int, self.heure_fin.split(':'))
            total_debut = h_debut * 60 + m_debut
            total_fin = h_fin * 60 + m_fin
            self.duree_min = max(0, total_fin - total_debut)
        except (ValueError, AttributeError):
            self.duree_min = 0

    def __repr__(self):
        return f'<Arret {self.machine} {self.heure_debut}-{self.heure_fin} ({self.duree_min}min) — {self.cause}>'
