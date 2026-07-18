# -*- coding: utf-8 -*-
"""Repare dashboard.py : retire les blocs de repli mensuel qui plantent (_d non lie).
A lancer depuis le dossier cuf-pilotage : py repair_dashboard.py
Les donnees vont jusqu'a aujourd'hui -> le mois courant a toujours des lignes,
donc ces replis sont du code mort. On les enleve, l'erreur disparait."""
import io, os, re, ast, sys

def trouver_dashboard():
    # 1) chemin standard depuis cuf-pilotage
    p = os.path.join("app", "routes", "dashboard.py")
    if os.path.exists(p):
        return p
    # 2) a cote du script (au cas ou lance ailleurs)
    ici = os.path.dirname(os.path.abspath(__file__))
    p2 = os.path.join(ici, "app", "routes", "dashboard.py")
    if os.path.exists(p2):
        return p2
    return None

def main():
    dash = trouver_dashboard()
    if not dash:
        print("INTROUVABLE : app\\routes\\dashboard.py")
        print(" -> ouvre PowerShell DANS le dossier cuf-pilotage, puis relance.")
        return 1

    s = io.open(dash, "r", encoding="utf-8").read()
    nl = "\r\n" if "\r\n" in s else "\n"

    # --- Passe 1 : retirer les blocs commentes de repli mensuel ---
    lignes = s.split(nl)
    out = []
    i = 0
    retires = 0
    while i < len(lignes):
        strip = lignes[i].strip()
        est_repli = strip.startswith("# Repli") and (
            "PDG" in strip or "mensuel" in strip or "mois courant" in strip)
        if est_repli:
            i += 1
            while i < len(lignes) and lignes[i].strip() != "":
                i += 1
            if i < len(lignes) and lignes[i].strip() == "":
                i += 1
            retires += 1
            continue
        out.append(lignes[i]); i += 1
    s = nl.join(out)

    # --- Passe 2 (filet de securite) : retirer un bloc _d orphelin eventuel ---
    # ex.: "if not _e:\n  _d = Equipe...\n  if _d:\n    mois, annee = _d..."
    s = re.sub(
        r"[ \t]*if not _e:\r?\n(?:[ \t]+.*\r?\n)*?[ \t]+mois, annee = _d\.date\.month.*\r?\n"
        r"(?:[ \t]+debut = .*\r?\n)?(?:[ \t]+fin\s*=.*\r?\n)?",
        "", s)

    io.open(dash, "w", encoding="utf-8").write(s)

    # --- Verification : le fichier compile-t-il, reste-t-il des _d nus ? ---
    try:
        ast.parse(s)
    except SyntaxError as e:
        print("ATTENTION : erreur de syntaxe apres reparation : %s" % e)
        return 2

    nus = re.findall(r"(?:^|[^A-Za-z0-9_])_d(?:$|[^A-Za-z0-9_])", s)
    print("OK : %d bloc(s) de repli retire(s)." % retires)
    print("Variables '_d' nues restantes : %d (doit etre 0)" % len(nus))
    print("Syntaxe : VALIDE.")
    print("")
    print("Relance l'application :  py run.py   (puis ouvre /dashboard/pertes)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
