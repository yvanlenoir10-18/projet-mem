"""
Modèles de données — Scierie CUF, Chaîne 4.

Hiérarchie :
  Equipe  (1 poste de 8h)
    └─ Production[]  (1 ligne par essence traitée, avec sa fenêtre horaire)
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

STATUT_BROUILLON = 'brouillon'
STATUT_A_VERIFIER = 'a_verifier'
STATUT_A_CORRIGER = 'a_corriger'
STATUT_VALIDE_CHEF = 'valide_chef'
STATUT_VERROUILLE = 'verrouille'
STATUT_SOUMIS_LEGACY = 'soumis'

STATUTS_ANALYSES = (STATUT_VALIDE_CHEF, STATUT_VERROUILLE)
STATUTS_NON_ANALYSES = (STATUT_BROUILLON, STATUT_A_VERIFIER, STATUT_A_CORRIGER)


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

    @property
    def prenom(self):
        return self.nom.split()[0].title() if self.nom else ''

    @property
    def initiales(self):
        parts = self.nom.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return self.nom[:2].upper() if self.nom else '?'

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
    Les arrêts sont saisis au niveau du poste, puis rattachés aux essences
    par chevauchement horaire pour l'analyse par essence.
    """
    __tablename__ = 'equipe'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=date.today)
    numero_equipe = db.Column(db.String(10), nullable=False)   # 'Matin' | 'Apres-midi'
    effectif = db.Column(db.Integer, default=10)
    statut = db.Column(db.String(20), nullable=False, default='brouillon')
    operateur_nom = db.Column(db.String(100))
    rempli_par_nom = db.Column(db.String(100))
    mode_saisie = db.Column(db.String(20), nullable=False, default='directe')
    fiche_papier_signee = db.Column(db.Boolean, default=False)
    fiche_papier_fichier = db.Column(db.String(255))
    fiche_papier_nom_original = db.Column(db.String(255))
    fiche_papier_chargee_le = db.Column(db.DateTime)
    aucun_arret_confirme = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    cree_le    = db.Column(db.DateTime, default=datetime.utcnow)
    soumis_le  = db.Column(db.DateTime)
    modifie_le  = db.Column(db.DateTime)
    modifie_par = db.Column(db.String(100))
    correction_motif = db.Column(db.Text)
    correction_cible = db.Column(db.String(60))
    correction_demandee_par = db.Column(db.String(100))
    correction_demandee_le = db.Column(db.DateTime)

    trs_disponibilite = db.Column(db.Float)
    trs_performance = db.Column(db.Float)
    trs_qualite = db.Column(db.Float)
    trs_global = db.Column(db.Float)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    productions = db.relationship('Production', backref='equipe', lazy=True,
                                  cascade='all, delete-orphan')
    arrets = db.relationship('Arret', backref='equipe', lazy=True,
                             cascade='all, delete-orphan')
    audits_correction = db.relationship('AuditCorrection', backref='equipe', lazy=True,
                                         cascade='all, delete-orphan')

    @property
    def duree_totale_arrets(self):
        return sum(a.duree_min for a in self.arrets if a.duree_min)

    @property
    def duree_arrets_impact(self):
        """Durée qui impacte réellement le TRS."""
        return sum(a.duree_impact_min for a in self.arrets)

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
        if self.statut == STATUT_VERROUILLE:
            return True
        return False

    @property
    def est_validee_chef(self):
        return self.statut in STATUTS_ANALYSES

    def __repr__(self):
        return f'<Equipe {self.date} {self.numero_equipe} TRS={self.trs_global}%>'


class AuditCorrection(db.Model):
    """Journal d'audit des retours, corrections et resoumissions de fiche."""
    __tablename__ = 'audit_correction'

    id = db.Column(db.Integer, primary_key=True)
    equipe_id = db.Column(db.Integer, db.ForeignKey('equipe.id'), nullable=False)
    auteur_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    action = db.Column(db.String(40), nullable=False)
    auteur_nom = db.Column(db.String(100), nullable=False)
    auteur_role = db.Column(db.String(20), nullable=False)
    ancien_statut = db.Column(db.String(20))
    nouveau_statut = db.Column(db.String(20))
    motif = db.Column(db.Text)
    resume = db.Column(db.Text)
    anciennes_valeurs = db.Column(db.Text)
    nouvelles_valeurs = db.Column(db.Text)
    cree_le = db.Column(db.DateTime, default=datetime.utcnow)

    auteur = db.relationship('User', lazy=True)

    def __repr__(self):
        return f'<AuditCorrection {self.action} equipe={self.equipe_id}>'


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
    heure_debut = db.Column(db.String(5))
    heure_fin = db.Column(db.String(5))
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

    @property
    def duree_traitement_min(self):
        """Durée de traitement de l'essence, en minutes."""
        try:
            h_d, m_d = map(int, self.heure_debut.split(':'))
            h_f, m_f = map(int, self.heure_fin.split(':'))
            return max(0, (h_f * 60 + m_f) - (h_d * 60 + m_d))
        except (ValueError, AttributeError):
            return 0

    @property
    def creneau_traitement(self):
        if self.heure_debut and self.heure_fin:
            return f"{self.heure_debut} → {self.heure_fin}"
        return '—'

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
    duree_prevue_min = db.Column(db.Integer)

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

    @property
    def duree_impact_min(self):
        """
        Durée à intégrer au TRS.
        Une maintenance planifiée ne pénalise que le dépassement de la durée prévue.
        """
        duree = self.duree_min or 0
        if self.categorie == 'Maintenance planifiée':
            return max(0, duree - (self.duree_prevue_min or 0))
        return duree

    def __repr__(self):
        return f'<Arret {self.machine} {self.heure_debut}-{self.heure_fin} ({self.duree_min}min)>'
