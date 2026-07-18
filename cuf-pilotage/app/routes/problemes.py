"""
Résolution guidée — Ishikawa 6M + 5 Pourquoi.

Le module aide le chef à passer d'un symptôme terrain à une cause racine
défendable, puis à une action légère suivie.
"""
from collections import Counter, defaultdict
from datetime import datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from ..models import db, Equipe, IshikawaCause, PourquoiNiveau, Probleme
from ..utils import roles_required


problemes_bp = Blueprint('problemes', __name__, url_prefix='/problemes')

CATEGORIES_6M = ['Machine', "Main d'oeuvre", 'Matière', 'Méthode', 'Milieu', 'Mesure']
STATUTS_PROBLEME = {
    'ouvert': 'Ouvert',
    'en_analyse': 'En analyse',
    'cause_identifiee': 'Cause identifiée',
    'clos': 'Clos',
}
STATUTS_ACTION = {
    'a_faire': 'À faire',
    'en_cours': 'En cours',
    'fait': 'Fait',
    'abandonne': 'Abandonné',
    'classe_sans_action': 'Classé sans action',
}
ORIGINES = {
    'manuel': 'Saisie manuelle',
    'fiche': 'Fiche opérateur',
    'pareto': 'Pareto arrêts',
    'recommandation': 'Recommandation',
    'machine': 'Machines & Arrêts',
}
LABELS_RECO = {
    'TRS_CRITIQUE': 'TRS critique',
    'ARRETS_NON_DOCUMENTES': 'Arrêts non documentés',
    'DECLASS_EXCESSIF': 'Déclassé excessif',
}
STATUTS_OUVERTS = ('ouvert', 'en_analyse', 'cause_identifiee')


def _nettoie(valeur, limite=None):
    texte = (valeur or '').strip()
    return texte[:limite] if limite else texte


def _probleme_or_404(probleme_id):
    return Probleme.query.get_or_404(probleme_id)


def _cause_or_404(probleme_id, cause_id):
    cause = IshikawaCause.query.filter_by(id=cause_id, probleme_id=probleme_id).first()
    if not cause:
        abort(404)
    return cause


def _question_niveau(cause, niveau):
    if niveau == 1:
        return f"Pourquoi {cause.description.strip()} ?"
    precedent = PourquoiNiveau.query.filter_by(cause_id=cause.id, niveau=niveau - 1).first()
    base = (precedent.reponse if precedent else '').strip()
    return f"Pourquoi {base} ?" if base else f"Pourquoi cette cause persiste-t-elle ?"


def _niveaux_pourquoi(cause):
    existants = {p.niveau: p for p in cause.pourquois}
    niveaux = []
    debloque = True
    for niveau in range(1, 6):
        p = existants.get(niveau)
        question = p.question if p else _question_niveau(cause, niveau)
        reponse = (p.reponse or '') if p else ''
        if niveau > 1:
            precedent = existants.get(niveau - 1)
            debloque = bool(precedent and (precedent.reponse or '').strip())
        niveaux.append({
            'niveau': niveau,
            'question': question,
            'reponse': reponse,
            'debloque': debloque,
            'complete': bool(reponse.strip()),
        })
    return niveaux


def _profondeur_cause(cause):
    return sum(1 for p in cause.pourquois if (p.reponse or '').strip())


def _solidite_analyse(probleme, cause=None):
    causes = list(probleme.causes)
    profondeurs = [_profondeur_cause(c) for c in causes]
    profondeur = _profondeur_cause(cause) if cause else (max(profondeurs) if profondeurs else 0)
    if len(causes) >= 3 and profondeur >= 3:
        return {
            'label': 'Analyse solide',
            'couleur': 'success',
            'detail': 'Plusieurs causes explorées et au moins 3 pourquoi renseignés.',
        }
    if len(causes) >= 1 and profondeur >= 1:
        return {
            'label': 'Analyse correcte',
            'couleur': 'warning',
            'detail': 'Cause explorée, mais l’analyse gagnerait à aller plus loin.',
        }
    return {
        'label': 'Analyse légère',
        'couleur': 'secondary',
        'detail': 'Ajoute au moins une cause et un pourquoi avant de retenir la racine.',
    }


def _interpretation_h2(categorie):
    if categorie == 'Machine':
        return {
            'famille': 'Technique',
            'confirme_h2': False,
            'texte': "Cause plutôt technique : H2 n'est pas confirmée par ce cas.",
        }
    if categorie == 'Matière':
        return {
            'famille': 'Matière première',
            'confirme_h2': False,
            'texte': "Cause liée à la matière : ce cas nuance H2.",
        }
    return {
        'famille': 'Organisationnelle / process',
        'confirme_h2': True,
        'texte': "Cause principalement organisationnelle : ce cas appuie H2.",
    }


def _grouped_causes(probleme):
    grouped = {cat: [] for cat in CATEGORIES_6M}
    for cause in sorted(probleme.causes, key=lambda c: (CATEGORIES_6M.index(c.categorie_6m), c.cree_le)):
        grouped.setdefault(cause.categorie_6m, []).append(cause)
    return grouped


def _form_data(source):
    def get(name, default='', limite=None):
        return _nettoie(source.get(name, default), limite)

    equipe_id = get('equipe_id')
    try:
        equipe_id = int(equipe_id) if equipe_id else None
    except ValueError:
        equipe_id = None

    origine_type = get('origine_type', 'manuel') or 'manuel'
    if origine_type not in ORIGINES:
        origine_type = 'manuel'

    return {
        'titre': get('titre', limite=200),
        'description': get('description'),
        'contexte_quoi': get('contexte_quoi'),
        'contexte_quand': get('contexte_quand'),
        'contexte_ou': get('contexte_ou'),
        'contexte_combien': get('contexte_combien'),
        'origine_type': origine_type,
        'origine_label': get('origine_label', limite=200),
        'origine_url': get('origine_url', limite=300),
        'equipe_id': equipe_id,
        'pareto_cause': get('pareto_cause', limite=200),
        'reco_code': get('reco_code', limite=50),
    }


def _prefill_args():
    data = _form_data(request.args)
    reco_label = LABELS_RECO.get(data['reco_code'], data['reco_code'])
    if not data['titre']:
        if data['pareto_cause']:
            data['titre'] = f"Analyser : {data['pareto_cause']}"
        elif data['reco_code']:
            data['titre'] = f"Analyser : {reco_label}"
        elif data['origine_label']:
            data['titre'] = f"Analyser : {data['origine_label']}"
    if data['reco_code'] and not data['origine_label']:
        data['origine_label'] = reco_label
    return data


def _doublon_ouvert(data):
    conditions = []
    if data.get('equipe_id'):
        conditions.append(Probleme.equipe_id == data['equipe_id'])
    if data.get('pareto_cause'):
        conditions.append(Probleme.pareto_cause == data['pareto_cause'])
    if data.get('reco_code'):
        conditions.append(Probleme.reco_code == data['reco_code'])
    if data.get('origine_label'):
        conditions.append(Probleme.origine_label == data['origine_label'])
    if not conditions:
        return None
    return Probleme.query.filter(
        Probleme.statut.in_(STATUTS_OUVERTS),
        or_(*conditions),
    ).order_by(Probleme.cree_le.desc()).first()


def _stats_liste(problemes):
    par_statut = Counter(p.statut for p in problemes)
    racines = [p.cause_racine for p in problemes if p.cause_racine]
    par_6m = Counter(c.categorie_6m for c in racines)
    org = sum(par_6m.get(cat, 0) for cat in ("Main d'oeuvre", 'Méthode', 'Milieu', 'Mesure'))
    technique = par_6m.get('Machine', 0)
    matiere = par_6m.get('Matière', 0)
    total_racines = len(racines)
    return {
        'par_statut': {k: par_statut.get(k, 0) for k in STATUTS_PROBLEME},
        'par_6m': {cat: par_6m.get(cat, 0) for cat in CATEGORIES_6M},
        'total': len(problemes),
        'total_racines': total_racines,
        'organisationnel': org,
        'technique': technique,
        'matiere': matiere,
        'pct_organisationnel': round((org / total_racines) * 100, 1) if total_racines else 0,
    }


@problemes_bp.route('/')
@login_required
@roles_required('chef', 'prod', 'admin')
def liste():
    statut = _nettoie(request.args.get('statut', 'ouverts'))
    query = Probleme.query
    if statut == 'ouverts':
        query = query.filter(Probleme.statut.in_(STATUTS_OUVERTS))
    elif statut in STATUTS_PROBLEME:
        query = query.filter(Probleme.statut == statut)
    elif statut != 'tous':
        statut = 'ouverts'
        query = query.filter(Probleme.statut.in_(STATUTS_OUVERTS))

    problemes = query.order_by(Probleme.cree_le.desc()).all()
    tous = Probleme.query.order_by(Probleme.cree_le.desc()).all()
    return render_template(
        'problemes/liste.html',
        problemes=problemes,
        stats=_stats_liste(tous),
        statut=statut,
        statuts=STATUTS_PROBLEME,
        origines=ORIGINES,
        interpretation_h2=_interpretation_h2,
    )


@problemes_bp.route('/nouveau', methods=['GET', 'POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def nouveau():
    data = _prefill_args() if request.method == 'GET' else _form_data(request.form)
    doublon = _doublon_ouvert(data)

    if request.method == 'POST':
        if not data['titre']:
            flash("Le titre du problème est obligatoire.", 'danger')
        elif doublon and request.form.get('ignorer_doublon') != '1':
            flash("Un problème similaire est déjà ouvert. Vérifie-le avant de créer un doublon.", 'warning')
        else:
            probleme = Probleme(
                titre=data['titre'],
                description=data['description'],
                contexte_quoi=data['contexte_quoi'],
                contexte_quand=data['contexte_quand'],
                contexte_ou=data['contexte_ou'],
                contexte_combien=data['contexte_combien'],
                origine_type=data['origine_type'],
                origine_label=data['origine_label'],
                origine_url=data['origine_url'],
                equipe_id=data['equipe_id'],
                pareto_cause=data['pareto_cause'],
                reco_code=data['reco_code'],
                cree_par_id=current_user.id,
            )
            db.session.add(probleme)
            db.session.commit()
            flash("Problème créé. Ajoute maintenant les causes possibles sur le 6M.", 'success')
            return redirect(url_for('problemes.ishikawa', probleme_id=probleme.id))

    return render_template(
        'problemes/nouveau.html',
        data=data,
        doublon=doublon,
        origines=ORIGINES,
    )


@problemes_bp.route('/<int:probleme_id>/etape/2')
@login_required
@roles_required('chef', 'prod', 'admin')
def ishikawa(probleme_id):
    probleme = _probleme_or_404(probleme_id)
    return render_template(
        'problemes/ishikawa.html',
        probleme=probleme,
        categories=CATEGORIES_6M,
        grouped_causes=_grouped_causes(probleme),
        solidite=_solidite_analyse(probleme),
    )


@problemes_bp.route('/<int:probleme_id>/etape/2/cause', methods=['POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def ajouter_cause(probleme_id):
    probleme = _probleme_or_404(probleme_id)
    payload = request.get_json(silent=True) or {}
    categorie = _nettoie(payload.get('categorie_6m'), 30)
    description = _nettoie(payload.get('description'), 500)
    if categorie not in CATEGORIES_6M:
        return jsonify({'erreur': 'Catégorie 6M invalide.'}), 400
    if not description:
        return jsonify({'erreur': 'La description de la cause est obligatoire.'}), 400

    cause = IshikawaCause(
        probleme_id=probleme.id,
        categorie_6m=categorie,
        description=description,
    )
    db.session.add(cause)
    if probleme.statut == 'ouvert':
        probleme.statut = 'en_analyse'
    db.session.commit()
    return jsonify({
        'id': cause.id,
        'categorie_6m': cause.categorie_6m,
        'description': cause.description,
        'url_pourquoi': url_for('problemes.pourquoi', probleme_id=probleme.id, cause_id=cause.id),
        'solidite': _solidite_analyse(probleme),
    })


@problemes_bp.route('/<int:probleme_id>/cause/<int:cause_id>', methods=['DELETE'])
@login_required
@roles_required('chef', 'prod', 'admin')
def supprimer_cause(probleme_id, cause_id):
    probleme = _probleme_or_404(probleme_id)
    cause = _cause_or_404(probleme.id, cause_id)
    etait_racine = cause.est_racine or probleme.cause_racine_selectionnee_id == cause.id
    restantes = IshikawaCause.query.filter(
        IshikawaCause.probleme_id == probleme.id,
        IshikawaCause.id != cause.id,
    ).count()
    db.session.delete(cause)
    if etait_racine:
        probleme.cause_racine_selectionnee_id = None
        probleme.statut = 'en_analyse' if restantes else 'ouvert'
    elif restantes == 0 and probleme.statut == 'en_analyse':
        probleme.statut = 'ouvert'
    db.session.commit()
    return jsonify({'ok': True, 'solidite': _solidite_analyse(probleme)})


@problemes_bp.route('/<int:probleme_id>/etape/3/<int:cause_id>')
@login_required
@roles_required('chef', 'prod', 'admin')
def pourquoi(probleme_id, cause_id):
    probleme = _probleme_or_404(probleme_id)
    cause = _cause_or_404(probleme.id, cause_id)
    return render_template(
        'problemes/pourquoi.html',
        probleme=probleme,
        cause=cause,
        niveaux=_niveaux_pourquoi(cause),
        solidite=_solidite_analyse(probleme, cause),
    )


@problemes_bp.route('/<int:probleme_id>/etape/3/<int:cause_id>/pourquoi', methods=['POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def sauver_pourquoi(probleme_id, cause_id):
    probleme = _probleme_or_404(probleme_id)
    cause = _cause_or_404(probleme.id, cause_id)
    payload = request.get_json(silent=True) or {}
    try:
        niveau = int(payload.get('niveau'))
    except (TypeError, ValueError):
        return jsonify({'erreur': 'Niveau invalide.'}), 400
    if niveau < 1 or niveau > 5:
        return jsonify({'erreur': 'Le niveau doit être compris entre 1 et 5.'}), 400
    reponse = _nettoie(payload.get('reponse'))
    if not reponse:
        return jsonify({'erreur': 'La réponse est obligatoire.'}), 400
    if niveau > 1:
        precedent = PourquoiNiveau.query.filter_by(cause_id=cause.id, niveau=niveau - 1).first()
        if not precedent or not (precedent.reponse or '').strip():
            return jsonify({'erreur': 'Réponds d’abord au niveau précédent.'}), 400

    question = _question_niveau(cause, niveau)
    item = PourquoiNiveau.query.filter_by(cause_id=cause.id, niveau=niveau).first()
    ancienne_reponse = (item.reponse or '').strip() if item else ''
    if not item:
        item = PourquoiNiveau(cause_id=cause.id, niveau=niveau, question=question)
        db.session.add(item)
    item.question = question
    item.reponse = reponse

    if ancienne_reponse and ancienne_reponse != reponse:
        PourquoiNiveau.query.filter(
            PourquoiNiveau.cause_id == cause.id,
            PourquoiNiveau.niveau > niveau,
        ).delete(synchronize_session=False)

    db.session.commit()

    question_suivante = _question_niveau(cause, niveau + 1) if niveau < 5 else ''
    return jsonify({
        'niveau': niveau,
        'question': item.question,
        'reponse': item.reponse,
        'question_suivante': question_suivante,
        'solidite': _solidite_analyse(probleme, cause),
    })


@problemes_bp.route('/<int:probleme_id>/etape/4', methods=['GET', 'POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def selectionner_racine(probleme_id):
    probleme = _probleme_or_404(probleme_id)
    causes = sorted(probleme.causes, key=lambda c: (CATEGORIES_6M.index(c.categorie_6m), c.cree_le))
    if request.method == 'POST':
        try:
            cause_id = int(request.form.get('cause_racine_id', ''))
        except ValueError:
            cause_id = 0
        cause = next((c for c in causes if c.id == cause_id), None)
        if not cause:
            flash("Sélectionne une cause racine.", 'danger')
        elif _profondeur_cause(cause) < 1:
            flash("La cause racine doit avoir au moins une réponse dans les 5 Pourquoi.", 'danger')
        else:
            statut_action = _nettoie(request.form.get('statut_action'), 30) or 'a_faire'
            if statut_action not in STATUTS_ACTION:
                statut_action = 'a_faire'
            actions = _nettoie(request.form.get('actions_correctives'))
            motif_sans_action = _nettoie(request.form.get('classe_sans_action_motif'))
            if statut_action == 'classe_sans_action' and not motif_sans_action:
                flash("Le motif est obligatoire si le problème est classé sans action.", 'danger')
            elif statut_action != 'classe_sans_action' and not actions:
                flash("Décris l'action décidée ou classe le problème sans action avec un motif.", 'danger')
            else:
                for c in causes:
                    c.est_racine = (c.id == cause.id)
                probleme.cause_racine_selectionnee_id = cause.id
                probleme.actions_correctives = actions
                probleme.responsable_action = _nettoie(request.form.get('responsable_action'), 120)
                probleme.statut_action = statut_action
                probleme.classe_sans_action_motif = motif_sans_action if statut_action == 'classe_sans_action' else None
                delai = _nettoie(request.form.get('delai_action'))
                if delai:
                    try:
                        probleme.delai_action = datetime.strptime(delai, '%Y-%m-%d').date()
                    except ValueError:
                        probleme.delai_action = None
                else:
                    probleme.delai_action = None
                probleme.statut = 'cause_identifiee'
                db.session.commit()
                flash("Cause racine enregistrée. Le rapport A3 est prêt.", 'success')
                return redirect(url_for('problemes.rapport', probleme_id=probleme.id))

    return render_template(
        'problemes/selectionner_racine.html',
        probleme=probleme,
        causes=causes,
        statuts_action=STATUTS_ACTION,
        solidite=_solidite_analyse(probleme),
    )


@problemes_bp.route('/<int:probleme_id>/rapport')
@login_required
@roles_required('chef', 'prod', 'admin')
def rapport(probleme_id):
    probleme = _probleme_or_404(probleme_id)
    racine = probleme.cause_racine
    return render_template(
        'problemes/rapport.html',
        probleme=probleme,
        grouped_causes=_grouped_causes(probleme),
        racine=racine,
        niveaux=_niveaux_pourquoi(racine) if racine else [],
        interpretation_h2=_interpretation_h2(racine.categorie_6m) if racine else None,
        statuts_action=STATUTS_ACTION,
        origines=ORIGINES,
    )


@problemes_bp.route('/<int:probleme_id>/clore', methods=['POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def clore(probleme_id):
    probleme = _probleme_or_404(probleme_id)
    if probleme.statut != 'cause_identifiee':
        flash("Le problème doit avoir une cause racine avant clôture.", 'warning')
    else:
        probleme.statut = 'clos'
        db.session.commit()
        flash("Problème clôturé.", 'success')
    return redirect(url_for('problemes.rapport', probleme_id=probleme.id))


@problemes_bp.route('/<int:probleme_id>/rouvrir', methods=['POST'])
@login_required
@roles_required('chef', 'prod', 'admin')
def rouvrir(probleme_id):
    probleme = _probleme_or_404(probleme_id)
    if probleme.statut == 'clos':
        probleme.statut = 'ouvert'
        db.session.commit()
        flash("Problème rouvert.", 'success')
    return redirect(url_for('problemes.ishikawa', probleme_id=probleme.id))


@problemes_bp.route('/<int:probleme_id>')
@login_required
@roles_required('chef', 'prod', 'admin')
def detail(probleme_id):
    probleme = _probleme_or_404(probleme_id)
    if probleme.statut in ('cause_identifiee', 'clos'):
        return redirect(url_for('problemes.rapport', probleme_id=probleme.id))
    return redirect(url_for('problemes.ishikawa', probleme_id=probleme.id))
