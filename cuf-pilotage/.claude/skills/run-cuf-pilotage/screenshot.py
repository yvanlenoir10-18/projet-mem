#!/usr/bin/env python3
"""
screenshot.py — Prend des screenshots de l'app CUF Pilotage via Playwright.

Usage :
  python .claude/skills/run-cuf-pilotage/screenshot.py                  # toutes les vues
  python .claude/skills/run-cuf-pilotage/screenshot.py operateur         # profil opérateur uniquement
  python .claude/skills/run-cuf-pilotage/screenshot.py chef              # profil chef uniquement
  python .claude/skills/run-cuf-pilotage/screenshot.py <url-path>        # vue spécifique, ex: /analyse/arrets

Les screenshots sont sauvegardés dans .claude/skills/run-cuf-pilotage/screenshots/
et dans /tmp/cuf-ss/ (pour les vues ad-hoc).

Prérequis :
  pip install playwright
  # Chromium est disponible dans ce container à /opt/pw-browsers/chromium-1194/chrome-linux/chrome
"""

import asyncio
import os
import sys
from pathlib import Path

CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
BASE = 'http://127.0.0.1:5000'
SS_DIR = Path(__file__).parent / 'screenshots'
TMP_DIR = Path('/tmp/cuf-ss')

CREDENTIALS = {
    'operateur': ('saisie@cuf.cm', 'cuf2026'),
    'prod':      ('prod@cuf.cm',   'cuf2026'),
    'pdg':       ('pdg@cuf.cm',    'cuf2026'),
    'admin':     ('admin@cuf.cm',  'cuf2026'),
}

VIEWS = {
    'operateur': [
        ('02-operateur-accueil',   '/saisie/accueil'),
        ('03-formulaire-nouveau',  '/saisie/nouveau'),
        ('04-historique',          '/saisie/historique'),
    ],
    'prod': [
        ('05-prod-dashboard',      '/dashboard/prod'),
        ('06-analyse-arrets',      '/analyse/arrets'),
        ('07-recommandations',     '/recommandations/'),
        ('08-problemes',           '/problemes/'),
        ('prod-fiches',            '/dashboard/chef/fiches'),
        ('prod-machines',          '/dashboard/chef/machines'),
        ('prod-production',        '/dashboard/chef/production'),
        ('prod-qualite',           '/dashboard/chef/qualite'),
        ('prod-pertes',            '/dashboard/pertes'),
        ('prod-actions',           '/dashboard/chef/actions'),
    ],
    'pdg': [
        ('09-pdg-dashboard',       '/dashboard/pdg'),
    ],
    'admin': [
        ('10-admin-utilisateurs',  '/admin/utilisateurs'),
        ('admin-parametres',       '/admin/parametres'),
    ],
}


async def new_session(browser, width=1280, height=900):
    ctx = await browser.new_context(viewport={'width': width, 'height': height})
    return ctx, await ctx.new_page()


async def login(page, email, password):
    await page.goto(f'{BASE}/login')
    await page.fill('input[name="email"]', email)
    await page.fill('input[name="password"]', password)
    await page.click('button[type="submit"]')
    await page.wait_for_load_state('networkidle')


async def screenshot(page, path, full_page=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    await page.screenshot(path=str(path), full_page=full_page)
    print(f'  ✓ {path}')


async def shoot_role(browser, role, views, out_dir):
    email, password = CREDENTIALS[role]
    ctx, page = await new_session(browser)
    await login(page, email, password)
    for name, url_path in views:
        await page.goto(f'{BASE}{url_path}')
        await page.wait_for_load_state('networkidle')
        await screenshot(page, out_dir / f'{name}.png')
    await ctx.close()


async def shoot_url(browser, role, url_path, out_dir):
    email, password = CREDENTIALS[role]
    ctx, page = await new_session(browser)
    await login(page, email, password)
    await page.goto(f'{BASE}{url_path}')
    await page.wait_for_load_state('networkidle')
    slug = url_path.strip('/').replace('/', '-') or 'index'
    await screenshot(page, out_dir / f'{slug}.png')
    await ctx.close()


async def main():
    from playwright.async_api import async_playwright

    arg = sys.argv[1] if len(sys.argv) > 1 else 'all'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=CHROME)

        if arg == 'all':
            SS_DIR.mkdir(parents=True, exist_ok=True)
            # Login page (unauthenticated)
            ctx, page = await new_session(browser)
            await page.goto(f'{BASE}/login')
            await screenshot(page, SS_DIR / '01-login.png')
            await ctx.close()
            # All roles
            for role, views in VIEWS.items():
                print(f'--- {role} ---')
                await shoot_role(browser, role, views, SS_DIR)

        elif arg in VIEWS:
            SS_DIR.mkdir(parents=True, exist_ok=True)
            print(f'--- {arg} ---')
            await shoot_role(browser, arg, VIEWS[arg], SS_DIR)

        elif arg.startswith('/'):
            # Ad-hoc URL — guess the role from the path
            role = 'prod' if any(k in arg for k in ['dashboard', 'analyse', 'probleme', 'recommandation', 'admin']) else 'operateur'
            if 'admin' in arg:
                role = 'admin'
            if 'pdg' in arg:
                role = 'pdg'
            TMP_DIR.mkdir(parents=True, exist_ok=True)
            print(f'Shooting {arg} as {role}…')
            await shoot_url(browser, role, arg, TMP_DIR)

        else:
            print(f'Usage: {sys.argv[0]} [all | operateur | chef | pdg | admin | /url-path]')
            sys.exit(1)

        await browser.close()
        print('Done.')


if __name__ == '__main__':
    asyncio.run(main())
