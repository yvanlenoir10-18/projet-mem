"""
Application Factory — wood_pilot.
"""
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from .models import db, User
from config import Config

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)
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
    from .routes.problemes import problemes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(saisie_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analyse_bp)
    app.register_blueprint(recos_bp)
    app.register_blueprint(problemes_bp)

    with app.app_context():
        db.create_all()
        _ensure_schema()
        _init_donnees_defaut()
        _repair_seed_roles()
        _seed_donnees_demo()

    @app.errorhandler(404)
    def page_introuvable(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(CSRFError)
    def erreur_csrf(e):
        message = "Session expirée ou formulaire invalide. Rechargez la page puis réessayez."
        if request.path.startswith('/recommandations/ai/') or (
            request.path.startswith('/problemes/') and (request.is_json or request.method == 'DELETE')
        ):
            return jsonify({'erreur': message}), 400
        flash(message, 'danger')
        return redirect(request.referrer or url_for('auth.login'))

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
            {'nom': 'Agent Saisie',    'email': 'saisie@cuf.cm', 'role': 'operateur', 'mdp': 'cuf2026'},
            {'nom': 'Chef Scierie',    'email': 'chef@cuf.cm',   'role': 'chef',      'mdp': 'cuf2026'},
            {'nom': 'Directeur',       'email': 'pdg@cuf.cm',    'role': 'pdg',       'mdp': 'cuf2026'},
            {'nom': 'Administrateur',  'email': 'admin@cuf.cm',  'role': 'admin',     'mdp': 'cuf2026'},
        ]
        for u in users:
            utilisateur = User(nom=u['nom'], email=u['email'], role=u['role'])
            utilisateur.set_password(u['mdp'])
            db.session.add(utilisateur)

    # Compte Chef de Production — profil autonome (rôle 'prod').
    # Idempotent : créé même sur une base déjà initialisée.
    if not User.query.filter_by(email='prod@cuf.cm').first():
        chef_prod = User(nom='Chef de Production', email='prod@cuf.cm', role='prod')
        chef_prod.set_password('cuf2026')
        db.session.add(chef_prod)

    if not Parametre.query.first():
        parametres = [
            # Prix de vente par essence (FCFA/m³) — alignés sur les prix de
            # référence figés dans les fiches (snapshots), pour cohérence entre
            # l'historique et les saisies futures.
            ('prix_ayous',         '180000', 'Prix de vente Ayous (FCFA/m³)'),
            ('prix_bilinga',         '280000', 'Prix de vente Bilinga (FCFA/m³)'),
            ('prix_iroko',         '420000', 'Prix de vente Iroko (FCFA/m³)'),
            ('prix_movingui',      '320000', 'Prix de vente Movingui (FCFA/m³)'),
            # Paramètres de production
            ('objectif_m3',        '12.5',   'Objectif de production par équipe (m³) — V1 provisoire'),
            ('duree_poste',        '480',    'Durée officielle d\'un poste (minutes)'),
            ('capacite_equipe_h',  '1.5625', 'Capacité théorique par défaut de la ligne (m³/heure) — 12.5m³/8h'),
            ('capacite_ayous_h',   '1.5625', 'Capacité théorique Ayous (m³/heure)'),
            ('capacite_bilinga_h',   '1.5625', 'Capacité théorique Bilinga (m³/heure)'),
            ('capacite_iroko_h',   '1.5625', 'Capacité théorique Iroko (m³/heure)'),
            ('capacite_movingui_h','1.5625', 'Capacité théorique Movingui (m³/heure)'),
            # Paramètre financier
            ('taux_revente_rebut', '0.70',   'Taux de revente locale du bois déclassé (70%)'),
            ('valeur_dechets_m3',  '0',      'Valeur résiduelle des déchets en V1 (FCFA/m³)'),
        ]
        for cle, valeur, desc in parametres:
            db.session.add(Parametre(cle=cle, valeur=valeur, description=desc))

    parametres_p2 = [
        ('taux_revente_rebut', '0.70', 'Taux de revente locale du bois déclassé (70%)'),
        ('valeur_dechets_m3',  '0',    'Valeur résiduelle des déchets en V1 (FCFA/m³)'),
        ('capacite_ayous_h',   '1.5625', 'Capacité théorique Ayous (m³/heure)'),
        ('capacite_bilinga_h',   '1.5625', 'Capacité théorique Bilinga (m³/heure)'),
        ('capacite_iroko_h',   '1.5625', 'Capacité théorique Iroko (m³/heure)'),
        ('capacite_movingui_h','1.5625', 'Capacité théorique Movingui (m³/heure)'),
    ]
    for cle, valeur, desc in parametres_p2:
        p = Parametre.query.filter_by(cle=cle).first()
        if not p:
            db.session.add(Parametre(cle=cle, valeur=valeur, description=desc))
        else:
            p.description = desc
            if cle == 'taux_revente_rebut' and p.valeur.strip() in ('0.30', '0.3'):
                p.valeur = valeur

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

    # F5 — Horaires standards par créneau (préremplissage du 1er passage)
    horaires_creneaux = [
        ('shift_matin_debut',     '06:00', 'Heure de début standard du poste Matin'),
        ('shift_matin_fin',       '14:00', 'Heure de fin standard du poste Matin'),
        ('shift_apresmidi_debut', '14:00', 'Heure de début standard du poste Après-midi'),
        ('shift_apresmidi_fin',   '22:00', 'Heure de fin standard du poste Après-midi'),
    ]
    for cle, valeur, desc in horaires_creneaux:
        if not Parametre.query.filter_by(cle=cle).first():
            db.session.add(Parametre(cle=cle, valeur=valeur, description=desc))

    # F6 — Objectif hebdomadaire de régularité de saisie (nb de postes/semaine, pas le TRS)
    if not Parametre.query.filter_by(cle='objectif_postes_semaine').first():
        db.session.add(Parametre(
            cle='objectif_postes_semaine', valeur='5',
            description='Objectif de régularité : nombre de postes saisis par semaine'))

    db.session.commit()


def _repair_seed_roles():
    """Corrige les rôles mal attribués lors des premiers seeds et ajoute les comptes manquants.

    Cas connu : Agent Saisie (saisie@cuf.cm) se retrouve avec role='admin'
    si la DB a été créée avant la liste de seed corrigée.
    """
    from .models import User

    # Corriger le rôle de Agent Saisie si nécessaire
    saisie = User.query.filter_by(email='saisie@cuf.cm').first()
    if saisie and saisie.role != 'operateur':
        saisie.role = 'operateur'
        db.session.flush()

    # Créer le compte admin s'il est absent
    if not User.query.filter_by(email='admin@cuf.cm').first():
        admin = User(nom='Administrateur', email='admin@cuf.cm', role='admin')
        admin.set_password('cuf2026')
        db.session.add(admin)
        db.session.flush()

    # Migrer prod@cuf.cm de role='chef' → 'prod' si la DB a été créée avant P63
    prod_user = User.query.filter_by(email='prod@cuf.cm').first()
    if prod_user and prod_user.role != 'prod':
        prod_user.role = 'prod'
        db.session.flush()

    db.session.commit()


def _ensure_schema():
    """Ajoute les colonnes légères manquantes sur les bases SQLite existantes."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    tables = set(inspector.get_table_names())
    if 'production' not in tables:
        return

    colonnes = {col['name'] for col in inspector.get_columns('production')}
    ajouts = []
    if 'heure_debut' not in colonnes:
        ajouts.append("ALTER TABLE production ADD COLUMN heure_debut VARCHAR(5)")
    if 'heure_fin' not in colonnes:
        ajouts.append("ALTER TABLE production ADD COLUMN heure_fin VARCHAR(5)")

    if 'equipe' in tables:
        colonnes_equipe = {col['name'] for col in inspector.get_columns('equipe')}
        if 'operateur_nom' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN operateur_nom VARCHAR(100)")
        if 'rempli_par_nom' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN rempli_par_nom VARCHAR(100)")
        if 'mode_saisie' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN mode_saisie VARCHAR(20) DEFAULT 'directe'")
        if 'fiche_papier_signee' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN fiche_papier_signee BOOLEAN DEFAULT 0")
        if 'fiche_papier_fichier' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN fiche_papier_fichier VARCHAR(255)")
        if 'fiche_papier_nom_original' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN fiche_papier_nom_original VARCHAR(255)")
        if 'fiche_papier_chargee_le' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN fiche_papier_chargee_le DATETIME")
        if 'aucun_arret_confirme' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN aucun_arret_confirme BOOLEAN DEFAULT 0")
        if 'correction_motif' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN correction_motif TEXT")
        if 'correction_cible' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN correction_cible VARCHAR(60)")
        if 'correction_demandee_par' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN correction_demandee_par VARCHAR(100)")
        if 'correction_demandee_le' not in colonnes_equipe:
            ajouts.append("ALTER TABLE equipe ADD COLUMN correction_demandee_le DATETIME")

    if 'arret' in tables:
        colonnes_arret = {col['name'] for col in inspector.get_columns('arret')}
        if 'duree_prevue_min' not in colonnes_arret:
            ajouts.append("ALTER TABLE arret ADD COLUMN duree_prevue_min INTEGER")

    if 'action_chef' in tables:
        colonnes_action_chef = {col['name'] for col in inspector.get_columns('action_chef')}
        if 'note_resultat' not in colonnes_action_chef:
            ajouts.append("ALTER TABLE action_chef ADD COLUMN note_resultat TEXT")
        if 'prescription_initiale' not in colonnes_action_chef:
            ajouts.append("ALTER TABLE action_chef ADD COLUMN prescription_initiale TEXT")
        if 'indicateur_suivi' not in colonnes_action_chef:
            ajouts.append("ALTER TABLE action_chef ADD COLUMN indicateur_suivi VARCHAR(200)")
        if 'date_verification_prevue' not in colonnes_action_chef:
            ajouts.append("ALTER TABLE action_chef ADD COLUMN date_verification_prevue DATE")
        if 'reco_code' not in colonnes_action_chef:
            ajouts.append("ALTER TABLE action_chef ADD COLUMN reco_code VARCHAR(50)")

    if not ajouts:
        return

    with db.engine.begin() as conn:
        for sql in ajouts:
            conn.execute(text(sql))


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
        (d(2026, 5, 1), 'Matin', 'valide_chef', 68.0,
         [('Ayous', 8.0, 5.0, 0.5), ('Bilinga', 5.0, 3.0, 0.3)],
         [('Bicoupe', '08:15', '09:00', 'Remplacement courroie', 'Mécanique'),
          ('Déligneuse', '10:30', '10:50', 'Attente opérateur', 'Organisationnelle')]),
        (d(2026, 5, 1), 'Apres-midi', 'valide_chef', 72.0,
         [('Iroko', 9.0, 6.0, 0.5)],
         []),
        (d(2026, 5, 2), 'Matin', 'valide_chef', 58.0,
         [('Movingui', 6.0, 3.5, 0.5), ('Ayous', 5.0, 3.0, 0.3)],
         [('Scie de tête', '07:30', '08:30', 'Tension lame', 'Mécanique'),
          ('Bicoupe', '10:00', '10:30', 'Pause non planifiée', 'Organisationnelle')]),
        (d(2026, 5, 2), 'Apres-midi', 'valide_chef', 74.0,
         [('Bilinga', 7.0, 4.5, 0.4)],
         [('Ébouteuse', '15:00', '15:20', 'Réglage longueur', 'Maintenance planifiée')]),
        (d(2026, 5, 3), 'Matin', 'brouillon', None,
         [('Iroko', 5.0, 3.0, 0.3)],
         []),
        # Avril 2026 — pour le delta TRS et la tendance
        (d(2026, 4, 1), 'Matin', 'valide_chef', 60.0,
         [('Ayous', 8.0, 4.5, 0.4), ('Bilinga', 5.0, 2.8, 0.3)],
         [('Bicoupe', '08:00', '09:15', 'Blocage grumes', 'Approvisionnement')]),
        (d(2026, 4, 1), 'Apres-midi', 'valide_chef', 65.0,
         [('Iroko', 8.0, 5.0, 0.5)],
         []),
        (d(2026, 4, 15), 'Matin', 'valide_chef', 63.0,
         [('Movingui', 7.0, 4.2, 0.4), ('Ayous', 4.0, 2.4, 0.2)],
         [('Bicoupe', '09:00', '09:45', 'Remplacement lame', 'Mécanique')]),
        # Mars 2026 — tendance
        (d(2026, 3, 10), 'Matin', 'valide_chef', 55.0,
         [('Ayous', 8.0, 4.0, 0.4)],
         [('Bicoupe', '08:00', '09:30', 'Panne moteur', 'Mécanique')]),
        # Février 2026 — tendance
        (d(2026, 2, 15), 'Matin', 'valide_chef', 62.0,
         [('Bilinga', 9.0, 5.2, 0.5)],
         []),
    ]

    def _fmt(minutes):
        h, m = divmod(minutes, 60)
        return f"{h:02d}:{m:02d}"

    def _creneaux(numero_equipe, nb_prods):
        debut = 6 * 60 if numero_equipe == 'Matin' else 14 * 60
        duree = 480 // max(1, nb_prods)
        return [(_fmt(debut + i * duree), _fmt(debut + (i + 1) * duree))
                for i in range(nb_prods)]

    for (date_eq, num_eq, statut, trs, prods, arrets) in specs:
        eq = Equipe(
            date=date_eq,
            numero_equipe=num_eq,
            operateur_nom='Opérateur Démo',
            rempli_par_nom='Opérateur Démo',
            statut=statut,
            trs_global=trs,
            user_id=admin.id,
            soumis_le=datetime.utcnow() if statut in ('valide_chef', 'soumis', 'verrouille') else None,
        )
        db.session.add(eq)
        db.session.flush()

        for idx, (essence, entree, conforme, declass) in enumerate(prods):
            h_debut, h_fin = _creneaux(num_eq, len(prods))[idx]
            db.session.add(Production(
                equipe_id=eq.id,
                essence=essence,
                heure_debut=h_debut,
                heure_fin=h_fin,
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
