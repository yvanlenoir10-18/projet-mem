#!/usr/bin/env python3
"""
import_reel.py — Importe les données terrain réelles CUF (fichier Excel Suivi_bicoupe)
dans la base de l'app, en remplacement des données simulées.

PRINCIPE (défendable pour le mémoire) :
  Le fichier terrain consigne le TRS mesuré poste par poste (feuille 5 : Dispo/Perf/
  Qualité) et le détail minute des arrêts (panne / changement lame / retard relève),
  mais PAS les volumes en m³ (production en billons/colis).

  On reconstruit donc les entrées du modèle app par INVERSION des formules trs.py :
    - Disponibilité  D = (480 − minutes arrêt) / 480   → arrêts recréés à leur durée réelle
    - Performance    P = volume_sorti / (capacité × h_utiles)  → volume_sorti = P × cap × h
    - Qualité        Q = volume_conforme / volume_sorti        → conforme = Q × volume_sorti
  Les m³ affichés sont donc DÉRIVÉS des taux réellement mesurés, pas inventés.

HYPOTHÈSES EXPLICITES (à citer dans le mémoire) :
  H-a. capacité chaîne = 1,5625 m³/h (paramètre app, = 12,5 m³ / 8 h).
  H-b. rendement matière entrée→sortie = 62 % (cible Cameroun 60 %, cohérent pertes ~35-38 %)
       — sert uniquement à reconstituer volume_entree pour le rendement matière (fig. 18).
       N'affecte AUCUNE composante du TRS.
  H-c. 3 créneaux réels importés fidèlement (Matin / Après-midi / Nuit) : CUF tourne en 3×8.
  H-d. essences hors des 4 configurées (Bilinga, DABEMA, MOABI, FRAKE, SAPELLI, LIMBALI)
       regroupées sous « Autre » (prix = moyenne des 4 essences configurées).
"""
import sys
from datetime import datetime, date
from collections import defaultdict

import openpyxl

import os
_RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # racine du dépôt (documents/outils/..)
sys.path.insert(0, os.path.join(_RACINE, 'cuf-pilotage'))
from app import create_app, db
from app.models import Equipe, Production, Arret, Parametre
from app.services.trs import calcule_trs

# Données brutes terrain (feuille 5 = TRS mesuré ; feuille 8 = essences).
# Variable d'env CUF_XLSX pour ré-importer un autre relevé.
XLSX = os.environ.get(
    'CUF_XLSX',
    os.path.join(_RACINE, 'documents', 'collecte', 'Suivi_bicoupe_CUF_mai-juin-2026.xlsx'),
)

CAPACITE_H = 1.5625          # H-a
# H-b. Rendement matière DIFFÉRENCIÉ par essence selon la densité/dureté du bois
# (base : littérature filière — Ayous tendre rend + ; Azobé dense rend −), calibré
# autour du benchmark Cameroun 60 %. HYPOTHÈSE DE MODÉLISATION, non mesurée par CUF :
# le fichier terrain ne consigne pas les m³ d'entrée. N'affecte AUCUNE composante TRS.
RENDEMENT_ESSENCE = {
    'Ayous':    0.68,   # tendre, léger
    'Iroko':    0.60,   # mi-dur
    'Movingui': 0.57,   # dur
    'Bilinga':  0.53,   # dense (bois dur)
    'Autre':    0.58,   # mélange essences diverses (dont Azobé, minoritaire)
}
RENDEMENT_DEFAUT = 0.60
DUREE_POSTE = 480
USER_ID = 1                  # saisie@cuf.cm (opérateur)

# Mapping créneau Excel -> libellé app
CRENEAU_MAP = {'Matin': 'Matin', 'Après-midi': 'Apres-midi', 'Nuit': 'Nuit'}

# Normalisation essences (H-d). Bilinga remplace Azobé comme 4e essence
# configurée (cf. décision 2026-07-10) : Bilinga est majoritaire dans les
# relevés réels ; Azobé, minoritaire, bascule désormais dans « Autre ».
ESSENCES_CONFIG = {'ayous': 'Ayous', 'bilinga': 'Bilinga',
                   'iroko': 'Iroko', 'movingui': 'Movingui'}

def normalise_essence(nom):
    if not nom:
        return 'Autre'
    cle = nom.strip().lower()
    return ESSENCES_CONFIG.get(cle, 'Autre')

def num(v):
    """Convertit une cellule (str ou nombre) en float, 0 si vide."""
    if v is None:
        return 0.0
    if isinstance(v, str):
        v = v.strip().replace('%', '').replace(',', '.')
        if not v:
            return 0.0
    try:
        return float(v)
    except (ValueError, TypeError):
        return 0.0


def main():
    wb = openpyxl.load_workbook(XLSX, data_only=True)

    # ── 1. Prix snapshot par essence (depuis Parametre) ──────────────────────
    app = create_app()
    with app.app_context():
        prix = {
            'Ayous':    num(Parametre.get('prix_ayous', 180000)),
            'Bilinga':  num(Parametre.get('prix_bilinga', 280000)),
            'Iroko':    num(Parametre.get('prix_iroko', 420000)),
            'Movingui': num(Parametre.get('prix_movingui', 320000)),
        }
        prix['Autre'] = round(sum(prix.values()) / len(prix))  # moyenne des 4

        # ── 2. Attribution essences par date (feuille 8) ─────────────────────
        ws8 = wb['8-PRODUCTION POSTE']
        essences_par_date = defaultdict(lambda: defaultdict(float))
        for r in range(5, ws8.max_row + 1):
            d = ws8.cell(r, 1).value
            if not isinstance(d, datetime):
                continue
            ess = normalise_essence(ws8.cell(r, 4).value)
            poids = num(ws8.cell(r, 7).value) + num(ws8.cell(r, 8).value)  # colis principal + récup
            poids = poids if poids > 0 else 1.0  # au moins 1 pour compter la présence
            essences_par_date[d.date()][ess] += poids

        # ── 3. Pannes détaillées par (date, équipe) — feuille 9 pour causes ──
        ws9 = wb['9-PANNES (version chef)']
        causes_bicoupe = {}   # date -> cause texte (si panne bicoupe ce jour)
        for r in range(5, ws9.max_row + 1):
            dtxt = ws9.cell(r, 1).value
            machine = (ws9.cell(r, 3).value or '').strip().lower()
            cause = ws9.cell(r, 7).value or ws9.cell(r, 6).value
            if dtxt and 'bicoupe' in machine and cause:
                causes_bicoupe[str(dtxt).strip()] = str(cause).strip()

        # ── 4. Purge des fiches simulées (garde users + params) ──────────────
        # IMPORTANT : delete() en masse NE déclenche PAS le cascade ORM.
        # On supprime explicitement les enfants d'abord (sinon orphelins +
        # réutilisation d'id SQLite -> les nouvelles fiches adoptent de vieux
        # arrêts/productions).
        from app.models import AuditCorrection
        n_old = Equipe.query.count()
        Arret.query.delete()
        Production.query.delete()
        AuditCorrection.query.delete()
        Equipe.query.delete()
        db.session.commit()
        print(f'Purge : {n_old} fiches simulées + enfants supprimés.')

        # ── 5. Import quart par quart depuis la feuille 5 (TRS) ──────────────
        ws5 = wb['5-TRS']
        n_eq = n_prod = n_arr = 0
        trs_vus = []

        for r in range(4, ws5.max_row + 1):
            d = ws5.cell(r, 1).value
            if not isinstance(d, datetime):
                continue
            creneau_xl = (ws5.cell(r, 2).value or '').strip()
            creneau = CRENEAU_MAP.get(creneau_xl)
            if not creneau:
                continue

            # Ancrage sur les composantes PUBLIÉES du fichier (colonnes 5/6/7),
            # robustes aux incohérences de saisie manuelle (marche>480, retard=979…).
            disp_pct    = num(ws5.cell(r, 5).value)      # % Disponibilité publiée
            perf_pct    = num(ws5.cell(r, 6).value)      # % Performance publiée
            qual_pct    = num(ws5.cell(r, 7).value)      # % Qualité publiée
            trs_excel   = num(ws5.cell(r, 8).value)      # % TRS publié (contrôle)
            chgt_lame   = num(ws5.cell(r, 9).value)      # min — poids cause
            panne       = num(ws5.cell(r, 10).value)     # min — poids cause
            retard      = num(ws5.cell(r, 11).value)     # min — poids cause

            disp = disp_pct / 100.0
            perf = perf_pct / 100.0
            qual = qual_pct / 100.0
            temps_utile = round(disp * DUREE_POSTE)
            temps_utile_h = temps_utile / 60.0
            vol_theo = CAPACITE_H * temps_utile_h
            arret_total = DUREE_POSTE - temps_utile

            volume_sorti = round(perf * vol_theo, 3)
            volume_conforme = round(qual * volume_sorti, 3)
            volume_declass = round(volume_sorti - volume_conforme, 3)

            # ── Equipe ──
            eq = Equipe(
                date=d.date(),
                numero_equipe=creneau,
                effectif=10,
                statut='verrouille',           # entre dans les KPI (STATUTS_ANALYSES)
                operateur_nom='Données terrain CUF',
                rempli_par_nom='Import Excel',
                mode_saisie='directe',
                aucun_arret_confirme=arret_total == 0,
                soumis_le=datetime.utcnow(),
                user_id=USER_ID,
            )
            db.session.add(eq)
            db.session.flush()
            n_eq += 1

            # ── Arrêts (durées réelles -> reproduit la Disponibilité) ──
            # Fenêtres horaires synthétiques dans le créneau pour heure_debut/fin
            base_h = {'Matin': 6, 'Apres-midi': 14, 'Nuit': 22}[creneau]
            curseur = base_h * 60  # minutes depuis minuit
            def add_arret(duree, cause, categorie):
                nonlocal curseur, n_arr
                if duree <= 0:
                    return
                deb = curseur % (24 * 60)
                fin = (curseur + int(duree)) % (24 * 60)
                a = Arret(
                    equipe_id=eq.id, machine='Bicoupe',
                    heure_debut=f'{deb//60:02d}:{deb%60:02d}',
                    heure_fin=f'{fin//60:02d}:{fin%60:02d}',
                    duree_min=int(round(duree)),
                    cause=cause, categorie=categorie,
                )
                db.session.add(a)
                curseur += int(duree)
                n_arr += 1

            dtxt_variants = [d.strftime('%d/%m'), d.strftime('%-d/%m')]
            cause_panne = 'Panne machine bicoupe'
            for v in dtxt_variants:
                if v in causes_bicoupe:
                    cause_panne = causes_bicoupe[v][:200]
                    break

            # Répartition du temps d'arrêt total (= 480 − temps utile publié) sur
            # les causes réelles, poids = minutes itemisées, mise à l'échelle pour
            # sommer EXACTEMENT à arret_total (reproduit la Disponibilité publiée).
            poids_causes = [
                (panne, cause_panne, 'Panne machine'),
                (chgt_lame, 'Changement de lame', 'Reglage / outil'),
                (retard, 'Retard de relève', 'Organisationnelle'),
            ]
            somme_poids = panne + chgt_lame + retard
            if arret_total > 0:
                if somme_poids > 0:
                    reste = arret_total
                    for i, (w, cause, cat) in enumerate(poids_causes):
                        if i == len(poids_causes) - 1:
                            duree = reste                  # reliquat -> somme exacte
                        else:
                            duree = round(arret_total * w / somme_poids)
                            reste -= duree
                        add_arret(duree, cause, cat)
                else:
                    add_arret(arret_total, 'Arrêt non catégorisé (relevé chef)', 'Autre')

            # ── Productions par essence (attribution feuille 8) ──
            mix = essences_par_date.get(d.date())
            if not mix:
                mix = {'Ayous': 1.0}     # défaut : essence dominante
            total_poids = sum(mix.values())
            heure_fin_prod = {'Matin': '14:00', 'Apres-midi': '22:00', 'Nuit': '06:00'}[creneau]
            heure_deb_prod = {'Matin': '06:00', 'Apres-midi': '14:00', 'Nuit': '22:00'}[creneau]
            for ess, poids in mix.items():
                frac = poids / total_poids
                v_sorti_e = round(volume_sorti * frac, 3)
                v_conf_e  = round(volume_conforme * frac, 3)
                v_dec_e   = round(volume_declass * frac, 3)
                rdt = RENDEMENT_ESSENCE.get(ess, RENDEMENT_DEFAUT)
                v_entree_e = round(v_sorti_e / rdt, 3) if v_sorti_e > 0 else 0.0
                p = Production(
                    equipe_id=eq.id, essence=ess,
                    volume_entree=v_entree_e,
                    volume_conforme=v_conf_e,
                    volume_declass=v_dec_e,
                    heure_debut=heure_deb_prod, heure_fin=heure_fin_prod,
                    prix_snapshot=prix.get(ess, prix['Autre']),
                )
                db.session.add(p)
                n_prod += 1

            db.session.flush()
            # ── TRS recalculé & stocké (cohérence tous chemins de code) ──
            res = calcule_trs(eq)
            trs_vus.append((d.date(), creneau, res['trs_global'], trs_excel))

        db.session.commit()
        print(f'Import : {n_eq} fiches · {n_prod} productions · {n_arr} arrêts.')

        # ── 6. Contrôle : TRS reconstruit vs TRS mesuré du fichier ──
        print('\nContrôle TRS reconstruit vs fichier (10 premiers quarts) :')
        ecarts = []
        for d, c, trs, trs_xl in trs_vus:
            ecarts.append(abs(trs - trs_xl))
        for d, c, trs, trs_xl in trs_vus[:10]:
            flag = 'OK' if abs(trs - trs_xl) <= 1.5 else '!!'
            print(f'  {d} {c:11s} reconstruit={trs:5.1f}% · fichier={trs_xl:4.0f}% [{flag}]')

        ecart_moy = round(sum(ecarts) / len(ecarts), 2)
        ecart_max = round(max(ecarts), 1)
        trs_moy = round(sum(t[2] for t in trs_vus) / len(trs_vus), 1)
        trs_moy_xl = round(sum(t[3] for t in trs_vus) / len(trs_vus), 1)
        print(f'\nÉcart moyen reconstruit vs fichier : {ecart_moy} pts · écart max : {ecart_max} pts')
        print(f'TRS moyen reconstruit : {trs_moy}% · TRS moyen fichier : {trs_moy_xl}%')
        dates = sorted(set(t[0] for t in trs_vus))
        print(f'Période : {dates[0]} → {dates[-1]} ({len(dates)} jours)')


if __name__ == '__main__':
    main()
