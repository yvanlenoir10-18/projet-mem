"""
Modèles de données — Scierie CUF, Chaîne 4.

Hiérarchie :
  Equipe  (1 poste de 8h)
    └─ Production[]  (1 ligne par essence traitée)
    └─ Arret[]       (arrêts machine partagés sur toute l'équipe)

Volumes Production (3 catégories explicites) :
  volume_entree   → grumes entrant dans la scie
  volume_conforme → planches satisfaisant les contrats (prix plein)
  volume_declass  → planches vendues localement à prix réduit
  volume_dechets  → sciure/dosses/chutes (calculé : entree - conforme - declass)
"""
import unicodedata
from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import bcrypt

db = SQLAlchemy()


def normalise_essence(nom):
    """Supprime les accents pour former la clé du paramètre prix."""
    nfkd = unicodedata.normalize('NFKD', nom.lower())
    return nfkd.encode('ASCII', 'ignore').decode()


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='admin')
    actif = db.Column(db.Boolean, default=True)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    equipes = db.relationship('Equipe', backref='saisie_par', lazy=True)

    def set_password(self, mot_de_passe):
        self.password_hash = bcrypt.hashpw(
            mot_de_passe.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, mot_de_passe):
        return bcrypt.checkpw(
            mot_de_passe.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def __repr__(self):
        return f'<User {self.nom} ({self.role})>'


class Parametre(db.Model):
    __tablename__ = 'parametre'

    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(50), unique=True, nullable=False)
    valeur = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200))
    mis_a_jour_le = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(cle, defaut=None):
        p = Parametre.query.filter_by(cle=cle).first()
        return p.valeur if p else defaut

    def __repr__(self):
        return f'<Parametre {self.cle}={self.valeur}>'


class Equipe(db.Model):
    """
    Un poste de travail de 8 heures sur la Chaîne 4.
    Une équipe peut traiter plusieurs essences via Production[].
    Les arrêts sont partagés (même ligne de sciage physique).
    """
    __tablename__ = 'equipe'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    numero_equipe = db.Column(db.String(10), nullable=False)   # 'Matin' | 'Apres-midi'
    effectif = db.Column(db.Integer, default=10)
    statut = db.Column(db.String(20), nullable=False, default='brouillon')
    notes = db.Column(db.Text)

    cree_le    = db.Column(db.DateTime, default=datetime.utcnow)
    soumis_le  = db.Column(db.DateTime)
    modifie_le  = db.Column(db.DateTime)
    modifie_par = db.Column(db.String(100))

    trs_disponibilite = db.Column(db.Float)
    trs_performance = db.Column(db.Float)
    trs_qualite = db.Column(db.Float)
    trs_global = db.Column(db.Float)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    productions = db.relationship('Production', backref='equipe', lazy=True,
                                  cascade='all, delete-orphan')
    arrets = db.relationship('Arret', backref='equipe', lazy=True,
                             cascade='all, delete-orphan')

    @property
    def duree_totale_arrets(self):
        return sum(a.duree_min for a in self.arrets if a.duree_min)

    @property
    def volume_entree(self):
        return round(sum(p.volume_entree for p in self.productions), 3)

    @property
    def volume_sorti(self):
        """Total planches (conformes + déclassées) — base du TRS Performance."""
        return round(sum(p.volume_conforme + p.volume_declass for p in self.productions), 3)

    @property
    def volume_conforme(self):
        """Planches satisfaisant les contrats."""
        return round(sum(p.volume_conforme for p in self.productions), 3)

    @property
    def volume_declass(self):
        """Planches déclassées vendues localement."""
        return round(sum(p.volume_declass for p in self.productions), 3)

    @property
    def volume_dechets(self):
        """Déchets inutilisables (sciure, dosses, chutes)."""
        return round(sum(p.volume_dechets for p in self.productions), 3)

    @property
    def essences_label(self):
        return ', '.join(p.essence for p in self.productions)

    @property
    def est_verrouille(self):
        if self.statut == 'verrouille':
            return True
        if self.soumis_le and self.statut == 'soumis':
            return (datetime.utcnow() - self.soumis_le) > timedelta(days=3)
        return False

    def __repr__(self):
        return f'<Equipe {self.date} {self.numero_equipe} TRS={self.trs_global}%>'


class Production(db.Model):
    """
    Une ligne de production par essence dans une équipe.
    Trois volumes explicites : conforme (contrats), declass (local), dechets (calculé).
    prix_snapshot est figé à la soumission pour des pertes FCFA cohérentes.
    """
    __tablename__ = 'production'

    id = db.Column(db.Integer, primary_key=True)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'), nullable=False)

    essence = db.Column(db.String(50), nullable=False)
    volume_entree = db.Column(db.Float, nullable=False)
    volume_conforme = db.Column(db.Float, nullable=False, default=0.0)
    volume_declass = db.Column(db.Float, nullable=False, default=0.0)
    prix_snapshot = db.Column(db.Float)

    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def volume_dechets(self):
        """Sciure, dosses, chutes = entree - conforme - declass."""
        return max(0.0, round(self.volume_entree - self.volume_conforme - self.volume_declass, 3))

    @property
    def rendement_matiere(self):
        """(conforme + declass) / entree × 100 — rendement matière réel."""
        total_planches = self.volume_conforme + self.volume_declass
        if self.volume_entree and self.volume_entree > 0:
            return round((total_planches / self.volume_entree) * 100, 1)
        return 0

    def __repr__(self):
        return f'<Production {self.essence} conf={self.volume_conforme}m³ dec={self.volume_declass}m³>'


class Arret(db.Model):
    """
    Un arrêt machine survenu pendant une équipe.
    Lié à l'équipe entière (la bicoupe est le goulot commun à toutes les essences).
    """
    __tablename__ = 'arret'

    id = db.Column(db.Integer, primary_key=True)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'), nullable=False)

    machine = db.Column(db.String(50), nullable=False)
    heure_debut = db.Column(db.String(5), nullable=False)
    heure_fin = db.Column(db.String(5), nullable=False)
    duree_min = db.Column(db.Integer)

    cause = db.Column(db.String(200), nullable=False)
    categorie = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)

    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    def calcule_duree(self):
        try:
            h_d, m_d = map(int, self.heure_debut.split(':'))
            h_f, m_f = map(int, self.heure_fin.split(':'))
            self.duree_min = max(0, (h_f * 60 + m_f) - (h_d * 60 + m_d))
        except (ValueError, AttributeError):
            self.duree_min = 0

    def __repr__(self):
        return f'<Arret {self.machine} {self.heure_debut}-{self.heure_fin} ({self.duree_min}min)>'
