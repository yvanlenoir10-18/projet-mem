# -*- coding: utf-8 -*-
"""
setup_demo.py — INSTALLATION DEMO CUF en une fois.
  A. applique les correctifs d'affichage (tous les menus/profils montrent les donnees)
  B. genere un jeu de donnees complet : operateurs Edgar/Messi/Gerve, 20 mai -> 23 juin
A lancer depuis le dossier cuf-pilotage :  python setup_demo.py
"""
import io, os, re, random
from datetime import datetime, date, timedelta

# ───────────────────────────── A. CORRECTIFS CODE ─────────────────────────────
def _read(p):
    with io.open(p, "r", encoding="utf-8") as f: return f.read()
def _write(p, s):
    with io.open(p, "w", encoding="utf-8") as f: f.write(s)

def patch(path, old, new):
    if not os.path.exists(path):
        print("  INTROUVABLE :", path); return
    s = _read(path)
    if old not in s:
        print("  deja ok :", os.path.basename(path)); return
    _write(path, s.replace(old, new)); print("  OK (%d) : %s" % (s.count(old), os.path.basename(path)))

def patch_re(path, pattern, repl, tag=""):
    if not os.path.exists(path):
        print("  INTROUVABLE :", path); return
    s = _read(path); s2, n = re.subn(pattern, repl, s)
    if n == 0:
        print("  deja ok / motif absent :", os.path.basename(path), tag); return
    _write(path, s2); print("  OK (%d) : %s %s" % (n, os.path.basename(path), tag))

APP = "app"
UTILS   = os.path.join(APP, "utils.py")
AUTH    = os.path.join(APP, "routes", "auth.py")
DASH    = os.path.join(APP, "routes", "dashboard.py")
SAISIE  = os.path.join(APP, "routes", "saisie.py")
ANALYSE = os.path.join(APP, "routes", "analyse.py")
BASEH   = os.path.join(APP, "templates", "base.html")
ACCUEIL = os.path.join(APP, "templates", "saisie", "accueil_operateur.html")

def appliquer_correctifs():
    print("== A. Correctifs d'affichage ==")
    nl = "\r\n" if os.path.exists(DASH) and "\r\n" in _read(DASH) else "\n"

    # 1) profil prod -> cockpit riche
    patch(UTILS, "dashboard.vue_prod", "dashboard.vue_chef")
    patch(AUTH,  "dashboard.vue_prod", "dashboard.vue_chef")
    patch_re(DASH,
        r"@roles_required\('chef', 'admin'\)(\r?\n)def vue_chef\(\):",
        r"@roles_required('chef', 'prod', 'admin')\1def vue_chef():", "(prod cockpit)")
    patch(BASEH, "dashboard.vue_prod", "dashboard.vue_chef")

    # 2) accueil operateur -> liste choisissable
    patch(ACCUEIL,
        "{{ url_for('saisie.modifier_equipe', equipe_id=a_corriger[0].id) }}{% if a_corriger[0].correction_cible %}#{{ a_corriger[0].correction_cible }}{% endif %}",
        "{{ url_for('saisie.historique', statut='a_corriger') }}")

    # 4) pool partage operateurs
    patch(SAISIE, "        return equipe.user_id == current_user.id",
                  "        return current_user.role in ('operateur', 'chef', 'admin')")
    patch(SAISIE, "STATUT_A_CORRIGER) and equipe.user_id == current_user.id",
                  "STATUT_A_CORRIGER) and current_user.role in ('operateur', 'chef', 'admin')")
    patch(SAISIE, "base_query = Equipe.query.filter(Equipe.user_id == current_user.id)",
                  "base_query = Equipe.query")
    patch(SAISIE, "        query = query.filter(Equipe.user_id == current_user.id)",
                  "        pass  # operateur : pool partage")
    patch(SAISIE, "if current_user.role == 'operateur' and equipe.user_id != current_user.id:",
                  "if False and equipe.user_id != current_user.id:")
    patch(SAISIE, "if current_user.role == 'operateur' and source.user_id != current_user.id:",
                  "if False and source.user_id != current_user.id:")

    # 6) sous-pages : periode par defaut = toutes les dates
    patch(ANALYSE, "jours     = int(request.args.get('jours', 30))",
                   "jours     = int(request.args.get('jours', 0))")
    patch(DASH, "jours = request.args.get('jours', 30)",
                "jours = request.args.get('jours', 0)")

    # 5) + 7) Replis mensuels (PDG / pertes / export) : NE PLUS INJECTER.
    #     dashboard.py (HEAD) embarque deja des replis surs (_q / _derniere) et
    #     les donnees vont jusqu'a aujourd'hui : le mois courant a toujours des
    #     lignes, donc ces replis sont du code mort. Les injecter en plus des
    #     replis existants creait des blocs empiles et une UnboundLocalError '_d'
    #     sur /dashboard/pertes selon l'ordre d'application. On les retire ici et
    #     on nettoie tout bloc '_d' deja injecte par une ancienne execution.
    contenu = _read(DASH)
    lignes = contenu.split(nl)
    sortie = []
    i = 0
    retires = 0
    while i < len(lignes):
        s = lignes[i].strip()
        if s.startswith("# Repli") and ("Repli PDG" in s or "Repli mensuel" in s):
            i += 1
            while i < len(lignes) and lignes[i].strip() != "":
                i += 1
            if i < len(lignes) and lignes[i].strip() == "":
                i += 1
            retires += 1
            continue
        sortie.append(lignes[i]); i += 1
    if retires:
        _write(DASH, nl.join(sortie)); print("  OK : %d bloc(s) '_d' retire(s) de dashboard.py" % retires)
    else:
        print("  deja ok : dashboard.py (aucun repli '_d' a retirer)")

    # 3) cockpit chef : repli periode si fenetre recente vide
    contenu = _read(DASH)
    if "jours_explicite = request.args.get('jours')" not in contenu:
        bloc_new = nl.join([
            "    else:",
            "        jours_explicite = request.args.get('jours') is not None",
            "        equipes = _get_equipes_periode(jours)",
            "        mode_mois = False",
            "        if not equipes and not jours_explicite:",
            "            equipes = Equipe.query.filter(",
            "                Equipe.statut.in_(_STATUTS_ANALYSES)",
            "            ).order_by(Equipe.date.desc()).all()",
            "        if equipes and not jours_explicite and (aujourd_hui - min(e.date for e in equipes)).days > jours:",
            "            debut_hist = min(e.date for e in equipes)",
            '            label_periode = "Toutes les dates"',
            "            jours = (aujourd_hui - debut_hist).days + 1",
            "            trace_debut, trace_fin = debut_hist, None",
            "        else:",
            '            label_periode = f"{jours} derniers jours"',
            "            trace_debut, trace_fin = aujourd_hui - timedelta(days=jours), None",
        ])
        pat = (r"    else:\r?\n"
               r"        equipes = _get_equipes_periode\(jours\)\r?\n"
               r"        label_periode = f\"\{jours\} derniers jours\"\r?\n"
               r"        mode_mois = False\r?\n"
               r"        trace_debut, trace_fin = aujourd_hui - timedelta\(days=jours\), None")
        c2, n = re.subn(pat, lambda m: bloc_new, contenu, count=1)
        if n:
            _write(DASH, c2); print("  OK (1) : dashboard.py (repli periode)")
        else:
            print("  motif periode absent")


# ───────────────────────────── B. DONNEES DEMO ─────────────────────────────
CAP = 2.473
DUREE = 480
RENDEMENT = {'Ayous': 0.338, 'Bilinga': 0.233, 'Iroko': 0.304, 'Movingui': 0.309}
PRIX = {'Ayous': 407149, 'Bilinga': 446051, 'Iroko': 262833, 'Movingui': 262383}
CATS = [('Changement de lame', 'Reglage / outil', 0.55, 'Bicoupe'),
        ('Panne machine bicoupe', 'Panne machine', 0.20, 'Bicoupe'),
        ('Retard de releve', 'Organisationnelle', 0.15, 'Bicoupe'),
        ('Reglage mecanique', 'Mecanique', 0.10, 'Scie de tete')]
BASE_H = {'Matin': 6, 'Apres-midi': 14}
H_PROD = {'Matin': ('06:00', '14:00'), 'Apres-midi': ('14:00', '22:00')}

def generer_donnees():
    print("== B. Generation des donnees ==")
    random.seed(42)
    from app import create_app, db
    from app.models import User, Equipe, Production, Arret, Parametre
    from app.services.trs import calcule_trs
    try:
        from app.models import AuditCorrection
    except Exception:
        AuditCorrection = None

    app = create_app()
    with app.app_context():
        def setp(k, v):
            p = Parametre.query.filter_by(cle=k).first()
            if p: p.valeur = str(v)
            else: db.session.add(Parametre(cle=k, valeur=str(v), description=k))
        setp('objectif_m3', 25)
        for k in ('capacite_equipe_h','capacite_ayous_h','capacite_iroko_h','capacite_movingui_h','capacite_bilinga_h'):
            setp(k, CAP)
        for _ess, _p in PRIX.items():   # prix FOB export -> parametres admin
            setp('prix_' + _ess.lower(), _p)
        db.session.commit()

        def ensure_user(nom, email, role):
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(nom=nom, email=email, role=role); u.set_password('cuf2026'); db.session.add(u)
            else:
                u.role = role
            if hasattr(u, 'actif'): u.actif = True
            return u
        ensure_user('Chef Scierie', 'chef@cuf.cm', 'chef')
        ensure_user('Chef de Production', 'prod@cuf.cm', 'prod')
        ensure_user('Directeur', 'pdg@cuf.cm', 'pdg')
        ensure_user('Administrateur', 'admin@cuf.cm', 'admin')
        ensure_user('Agent Saisie', 'saisie@cuf.cm', 'operateur')
        op1 = ensure_user('Edgar', 'edgar@cuf.cm', 'operateur')
        op2 = ensure_user('Messi', 'messi@cuf.cm', 'operateur')
        op3 = ensure_user('Gerve', 'gerve@cuf.cm', 'operateur')
        db.session.commit()
        ops = [op1, op2, op3]

        Arret.query.delete(); Production.query.delete()
        if AuditCorrection: AuditCorrection.query.delete()
        Equipe.query.delete(); db.session.commit()

        debut = date(2026, 5, 20); fin = date.today()  # rempli jusqu'a aujourd'hui
        n_eq = n_prod = n_arr = 0
        fiches_par_op = {op.id: [] for op in ops}
        idx = 0; jour = debut
        while jour <= fin:
            for poste in ('Matin', 'Apres-midi'):
                op = ops[idx % 3]; idx += 1
                D = min(0.99, max(0.45, random.gauss(0.80, 0.10)))
                P = min(0.99, max(0.55, random.gauss(0.925, 0.06)))
                Q = min(0.99, max(0.60, random.gauss(0.849, 0.06)))
                tu = round(D * DUREE); arret_total = DUREE - tu
                vol_theo = CAP * (tu / 60.0)
                vs = round(P * vol_theo, 3); vc = round(Q * vs, 3); vd = round(vs - vc, 3)
                eq = Equipe(date=jour, numero_equipe=poste, effectif=10, statut='verrouille',
                            operateur_nom=op.nom, rempli_par_nom=op.nom, mode_saisie='directe',
                            aucun_arret_confirme=(arret_total == 0), soumis_le=datetime.utcnow(), user_id=op.id)
                db.session.add(eq); db.session.flush(); n_eq += 1
                fiches_par_op[op.id].append(eq)
                curseur = BASE_H[poste] * 60
                if arret_total > 0:
                    reste = arret_total
                    for i, (cause, cat, poids, machine) in enumerate(CATS):
                        d = reste if i == len(CATS) - 1 else int(round(arret_total * poids))
                        if d <= 0: continue
                        reste -= d; deb = curseur % 1440; f2 = (curseur + d) % 1440
                        db.session.add(Arret(equipe_id=eq.id, machine=machine,
                            heure_debut=f'{deb//60:02d}:{deb%60:02d}', heure_fin=f'{f2//60:02d}:{f2%60:02d}',
                            duree_min=d, cause=cause, categorie=cat)); curseur += d; n_arr += 1
                mix = random.choice([{'Ayous':1.0},{'Ayous':0.6,'Bilinga':0.4},{'Iroko':0.5,'Movingui':0.5},
                                     {'Bilinga':0.7,'Ayous':0.3},{'Movingui':1.0}])
                tot = sum(mix.values()); items = list(mix.items()); n_ess = len(items)
                base_min = BASE_H[poste] * 60; slot = 480 // n_ess
                for i, (ess, w) in enumerate(items):
                    fr = w / tot; v_s = round(vs*fr,3); v_c = round(vc*fr,3); v_d = round(vd*fr,3)
                    v_e = round(v_s / RENDEMENT[ess], 3) if v_s > 0 else 0.0
                    d0 = base_min + i * slot
                    d1 = base_min + 480 if i == n_ess - 1 else base_min + (i + 1) * slot
                    hd = f'{d0//60:02d}:{d0%60:02d}'; hf = f'{d1//60:02d}:{d1%60:02d}'
                    db.session.add(Production(equipe_id=eq.id, essence=ess, volume_entree=v_e,
                        volume_conforme=v_c, volume_declass=v_d, heure_debut=hd, heure_fin=hf,
                        prix_snapshot=None)); n_prod += 1  # pas de prix fige -> l'admin pilote les prix
            jour += timedelta(days=1)
        db.session.commit()

        for op in ops:
            fs = sorted(fiches_par_op[op.id], key=lambda e: e.date, reverse=True)
            k = 0
            for statut, nb in [('a_corriger',2),('a_verifier',2),('brouillon',1),('valide_chef',1)]:
                for _ in range(nb):
                    if k >= len(fs): break
                    e = fs[k]; k += 1; e.statut = statut
                    if statut == 'a_corriger':
                        e.correction_motif = "Volume conforme a reverifier : ecart avec le releve papier."
            db.session.commit()

        for e in Equipe.query.all():
            calcule_trs(e)
        db.session.commit()
        from collections import Counter
        c = Counter(e.statut for e in Equipe.query.all())
        print(f"  {n_eq} fiches, {n_prod} productions, {n_arr} arrets · {debut} -> {fin}")
        print(f"  operateurs (mdp cuf2026) : edgar@cuf.cm, messi@cuf.cm, gerve@cuf.cm")
        print(f"  statuts : {dict(c)}")


if __name__ == '__main__':
    appliquer_correctifs()
    generer_donnees()
    print("--- TERMINE : relance l'app (python run.py) puis connecte-toi a n'importe quel profil ---")
