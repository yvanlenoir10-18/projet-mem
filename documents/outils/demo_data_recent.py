# -*- coding: utf-8 -*-
"""
demo_data.py — Jeu de DEMONSTRATION complet et RECENT pour l'app CUF.

But : tous les profils (operateur, chef, prod, PDG, admin) et tous les menus
(arrets/Pareto, qualite, pertes, production) sont peuples, sans dependre
d'aucun correctif de code, parce que les donnees sont datees des 30 derniers
jours (donc dans la fenetre par defaut de tous les tableaux de bord).

A lancer depuis le dossier cuf-pilotage :  python demo_data.py
"""
import random
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models import User, Equipe, Production, Arret, Parametre
from app.services.trs import calcule_trs
try:
    from app.models import AuditCorrection
except Exception:
    AuditCorrection = None

random.seed(42)  # reproductible

CAP = 2.473
DUREE = 480
ESSENCES = ['Ayous', 'Bilinga', 'Iroko', 'Movingui']
RENDEMENT = {'Ayous': 0.338, 'Bilinga': 0.233, 'Iroko': 0.304, 'Movingui': 0.309}
PRIX = {'Ayous': 180000, 'Bilinga': 280000, 'Iroko': 420000, 'Movingui': 320000}
# (cause, categorie, poids Pareto) — changement de lame dominant (memoire)
CATS = [
    ('Changement de lame', 'Reglage / outil', 0.55, 'Bicoupe'),
    ('Panne machine bicoupe', 'Panne machine', 0.20, 'Bicoupe'),
    ('Retard de releve', 'Organisationnelle', 0.15, 'Bicoupe'),
    ('Reglage mecanique', 'Mecanique', 0.10, 'Scie de tete'),
]
BASE_H = {'Matin': 6, 'Apres-midi': 14}
H_PROD = {'Matin': ('06:00', '14:00'), 'Apres-midi': ('14:00', '22:00')}


def main():
    app = create_app()
    with app.app_context():
        # 1) Parametres alignes memoire
        def setp(k, v):
            p = Parametre.query.filter_by(cle=k).first()
            if p:
                p.valeur = str(v)
            else:
                db.session.add(Parametre(cle=k, valeur=str(v), description=k))
        setp('objectif_m3', 25)
        for k in ('capacite_equipe_h', 'capacite_ayous_h', 'capacite_iroko_h',
                  'capacite_movingui_h', 'capacite_bilinga_h'):
            setp(k, CAP)
        db.session.commit()

        # 2) Comptes (idempotent) — 3 operateurs
        def ensure_user(nom, email, role):
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(nom=nom, email=email, role=role)
                u.set_password('cuf2026')
                db.session.add(u)
            else:
                u.role = role
            if hasattr(u, 'actif'):
                u.actif = True
            return u
        ensure_user('Chef Scierie', 'chef@cuf.cm', 'chef')
        ensure_user('Chef de Production', 'prod@cuf.cm', 'prod')
        ensure_user('Directeur', 'pdg@cuf.cm', 'pdg')
        ensure_user('Administrateur', 'admin@cuf.cm', 'admin')
        ensure_user('Agent Saisie', 'saisie@cuf.cm', 'operateur')  # compte historique
        op1 = ensure_user('Edgar', 'edgar@cuf.cm', 'operateur')
        op2 = ensure_user('Messi', 'messi@cuf.cm', 'operateur')
        op3 = ensure_user('Gerve', 'gerve@cuf.cm', 'operateur')
        db.session.commit()
        ops = [op1, op2, op3]

        # 3) Purge des fiches (enfants d'abord — pas de cascade en bulk)
        Arret.query.delete()
        Production.query.delete()
        if AuditCorrection:
            AuditCorrection.query.delete()
        Equipe.query.delete()
        db.session.commit()

        # 4) Generation : periode du memoire (20 mai -> 23 juin 2026), chaque jour
        debut = date(2026, 5, 20)
        fin = date(2026, 6, 23)
        n_eq = n_prod = n_arr = 0
        fiches_par_op = {op.id: [] for op in ops}
        idx = 0
        jour = debut
        while jour <= fin:
            for poste in ('Matin', 'Apres-midi'):
                op = ops[idx % 3]
                idx += 1
                D = min(0.99, max(0.45, random.gauss(0.80, 0.10)))
                P = min(0.99, max(0.55, random.gauss(0.925, 0.06)))
                Q = min(0.99, max(0.60, random.gauss(0.849, 0.06)))
                temps_utile = round(D * DUREE)
                arret_total = DUREE - temps_utile
                vol_theo = CAP * (temps_utile / 60.0)
                volume_sorti = round(P * vol_theo, 3)
                volume_conforme = round(Q * volume_sorti, 3)
                volume_declass = round(volume_sorti - volume_conforme, 3)

                eq = Equipe(
                    date=jour, numero_equipe=poste, effectif=10,
                    statut='verrouille',
                    operateur_nom=op.nom, rempli_par_nom=op.nom,
                    mode_saisie='directe',
                    aucun_arret_confirme=(arret_total == 0),
                    soumis_le=datetime.utcnow(), user_id=op.id,
                )
                db.session.add(eq)
                db.session.flush()
                n_eq += 1
                fiches_par_op[op.id].append(eq)

                # Arrets repartis sur les categories (Pareto)
                curseur = BASE_H[poste] * 60
                if arret_total > 0:
                    reste = arret_total
                    for i, (cause, cat, poids, machine) in enumerate(CATS):
                        duree = reste if i == len(CATS) - 1 else int(round(arret_total * poids))
                        if duree <= 0:
                            continue
                        reste -= duree
                        deb = curseur % (24 * 60)
                        finm = (curseur + duree) % (24 * 60)
                        db.session.add(Arret(
                            equipe_id=eq.id, machine=machine,
                            heure_debut=f'{deb // 60:02d}:{deb % 60:02d}',
                            heure_fin=f'{finm // 60:02d}:{finm % 60:02d}',
                            duree_min=duree, cause=cause, categorie=cat,
                        ))
                        curseur += duree
                        n_arr += 1

                # Productions : 1 a 2 essences (Ayous dominant, Bilinga present)
                mix = random.choice([
                    {'Ayous': 1.0},
                    {'Ayous': 0.6, 'Bilinga': 0.4},
                    {'Iroko': 0.5, 'Movingui': 0.5},
                    {'Bilinga': 0.7, 'Ayous': 0.3},
                    {'Movingui': 1.0},
                ])
                total = sum(mix.values())
                hd, hf = H_PROD[poste]
                for ess, w in mix.items():
                    frac = w / total
                    v_sorti = round(volume_sorti * frac, 3)
                    v_conf = round(volume_conforme * frac, 3)
                    v_dec = round(volume_declass * frac, 3)
                    v_ent = round(v_sorti / RENDEMENT[ess], 3) if v_sorti > 0 else 0.0
                    db.session.add(Production(
                        equipe_id=eq.id, essence=ess,
                        volume_entree=v_ent, volume_conforme=v_conf,
                        volume_declass=v_dec, heure_debut=hd, heure_fin=hf,
                        prix_snapshot=PRIX[ess],
                    ))
                    n_prod += 1
            jour += timedelta(days=1)
        db.session.commit()

        # 5) Melange de statuts : chaque operateur a des fiches a chaque etape
        #    (les plus recentes deviennent pending pour illustrer le workflow)
        for op in ops:
            fs = sorted(fiches_par_op[op.id], key=lambda e: e.date, reverse=True)
            # 2 a corriger (renvoyees par le chef), 2 a verifier, 1 brouillon,
            # 1 validee chef ; le reste demeure verrouille (compte dans les KPI)
            plan = ([('a_corriger', 2), ('a_verifier', 2),
                     ('brouillon', 1), ('valide_chef', 1)])
            k = 0
            for statut, nb in plan:
                for _ in range(nb):
                    if k >= len(fs):
                        break
                    e = fs[k]; k += 1
                    e.statut = statut
                    if statut == 'a_corriger':
                        e.correction_motif = ("Volume conforme a reverifier : ecart "
                                              "avec le releve papier du poste.")
            db.session.commit()

        # 6) Recalcul TRS pour coherence tous chemins
        trs = []
        for e in Equipe.query.all():
            r = calcule_trs(e)
            if r.get('trs_global') is not None:
                trs.append(r['trs_global'])
        db.session.commit()

        from collections import Counter
        par_statut = Counter(e.statut for e in Equipe.query.all())
        moy = round(sum(trs) / len(trs), 1) if trs else 0
        print(f"Genere : {n_eq} fiches, {n_prod} productions, {n_arr} arrets")
        print(f"Periode : {debut} -> {fin} (chaque jour rempli)")
        print(f"Operateurs (mdp cuf2026) : edgar@cuf.cm, messi@cuf.cm, gerve@cuf.cm")
        print(f"Statuts : {dict(par_statut)}")
        print(f"TRS moyen : {moy} %")
        print("--- Donnees pretes : connecte-toi a n'importe quel profil ---")


if __name__ == '__main__':
    main()
