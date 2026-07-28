"""
nicegui/app.py

A small dashboard for the CLIF->Prover9 pipeline. Replaces the old
boilerplate example files (main.py/homepage.py/theme.py/function.py/
class_ex.py), which import 'message' and 'menu' modules that don't exist
anywhere in this repo and would crash on startup.

Run from the repo root (so 'config' and 'db' are importable):
    python3 nicegui/app.py
Then open http://localhost:8080 -- the devcontainer already forwards this
port (see .devcontainer/devcontainer.json).

Pages:
  /              Environment + pipeline health (read-only, mirrors check_app.sh)
  /hierarchies   Browsable table of the 'hierarchies' MySQL table
"""

import os
import shutil
import subprocess
import sys

# allow running this file directly (python3 nicegui/app.py) while still
# importing 'config' and 'db' from the repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import config
from db import create_schema
from nicegui import ui


# ---------------------------------------------------------------------------
# Shared layout
# ---------------------------------------------------------------------------

def top_bar(active: str) -> None:
    with ui.header().classes('items-center justify-between'):
        ui.label('SEADOO Pipeline Dashboard').classes('text-lg font-bold')
        with ui.row():
            ui.link('Health', '/').classes(
                'text-white font-bold' if active == 'health' else 'text-white')
            ui.link('Hierarchies', '/hierarchies').classes(
                'text-white font-bold' if active == 'hierarchies' else 'text-white')


# ---------------------------------------------------------------------------
# Health checks (read-only; same checks as check_app.sh, surfaced in the UI)
# ---------------------------------------------------------------------------

def _check_path(path, label):
    ok = os.path.isdir(path) and bool(os.listdir(path)) if os.path.isdir(path) else False
    detail = path if ok else '{} not found or empty'.format(path)
    return label, ok, detail


def _check_binary(name):
    path = shutil.which(name)
    return name, path is not None, (path or 'not on PATH')


def _check_service(name):
    try:
        result = subprocess.run(['service', name, 'status'],
                                 capture_output=True, text=True, timeout=5)
        ok = result.returncode == 0
        detail = (result.stdout or result.stderr).strip().splitlines()[-1] if (result.stdout or result.stderr) else ''
        return name, ok, detail
    except Exception as exc:
        return name, False, str(exc)


def _check_import(module_name):
    try:
        __import__(module_name)
        return module_name, True, 'importable'
    except Exception as exc:
        return module_name, False, str(exc)


def _check_config():
    missing = [a for a in ('clif_repo', 'repo', 'hierarchy', 'db') if not hasattr(config, a)]
    if missing:
        return 'config.py', False, 'missing: {}'.format(', '.join(missing))
    return 'config.py', True, 'clif_repo={}'.format(config.clif_repo)


def _check_db():
    conn = create_schema.connect()
    if conn is None:
        return 'MySQL connection', False, 'could not connect -- check config.db'
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'hierarchies'")
        if cursor.fetchone() is None:
            return ('hierarchies table', False,
                    "does not exist -- run: PYTHONPATH=. python3 db/create_schema.py --no-insert")
        cursor.execute('SELECT COUNT(*) FROM hierarchies')
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hierarchies WHERE root_theory IS NOT NULL AND root_theory != ''")
        with_root = cursor.fetchone()[0]
        return ('hierarchies table', True,
                '{} rows, {} with root_theory set'.format(total, with_root))
    finally:
        conn.close()


def run_all_checks():
    checks = []
    checks.append(_check_path(os.path.expanduser('~/colore/ontologies'), 'COLORE checkout'))
    checks.append(_check_path(os.path.expanduser('~/macleod'), 'macleod config dir'))
    checks.append(_check_binary('prover9'))
    checks.append(_check_binary('mace4'))
    checks.append(_check_service('mariadb'))
    checks.append(_check_import('macleod.parsing.parser'))
    checks.append(_check_config())
    checks.append(_check_db())
    return checks


@ui.page('/')
def health_page():
    top_bar('health')
    ui.label('Environment + Pipeline Health').classes('text-xl font-bold mt-4')
    ui.label('Read-only -- mirrors check_app.sh. Refresh after fixing something.').classes('text-sm text-gray-500')

    results_column = ui.column().classes('w-full gap-2 mt-4')

    def render():
        results_column.clear()
        with results_column:
            for label, ok, detail in run_all_checks():
                with ui.row().classes('items-center gap-2'):
                    ui.icon('check_circle' if ok else 'cancel').classes(
                        'text-green-600' if ok else 'text-red-600')
                    ui.label(label).classes('font-medium w-48')
                    ui.label(detail).classes('text-sm text-gray-600')

    ui.button('Refresh', on_click=render, icon='refresh').classes('mt-2')
    render()


# ---------------------------------------------------------------------------
# Hierarchies browser
# ---------------------------------------------------------------------------

def fetch_hierarchies(search: str = ''):
    conn = create_schema.connect()
    if conn is None:
        return None, 'Could not connect to MySQL -- check config.db'
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'hierarchies'")
        if cursor.fetchone() is None:
            return None, "'hierarchies' table does not exist yet -- run populate_hierarchies.py first"
        query = ("SELECT hierarchy_name, root_theory, num_prim_relations, "
                  "relation_name, nondecomp_hierarchies FROM hierarchies")
        params = ()
        if search:
            query += " WHERE hierarchy_name LIKE %s"
            params = ('%{}%'.format(search),)
        query += " ORDER BY hierarchy_name"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows, None
    finally:
        conn.close()


@ui.page('/hierarchies')
def hierarchies_page():
    top_bar('hierarchies')
    ui.label('Hierarchies').classes('text-xl font-bold mt-4')
    ui.label('Metadata only -- the actual chain-decomposition poset stays in each '
             "hierarchy's chain_decomposition.csv.").classes('text-sm text-gray-500')

    columns = [
        {'name': 'hierarchy_name', 'label': 'Hierarchy', 'field': 'hierarchy_name', 'sortable': True, 'align': 'left'},
        {'name': 'root_theory', 'label': 'Root theory', 'field': 'root_theory', 'sortable': True, 'align': 'left'},
        {'name': 'num_prim_relations', 'label': '# Relations', 'field': 'num_prim_relations', 'sortable': True},
        {'name': 'relation_name', 'label': 'Relation', 'field': 'relation_name', 'align': 'left'},
        {'name': 'nondecomp_hierarchies', 'label': 'Decomposes into', 'field': 'nondecomp_hierarchies', 'align': 'left'},
    ]

    error_label = ui.label('').classes('text-red-600')
    table = ui.table(columns=columns, rows=[], row_key='hierarchy_name').classes('w-full mt-2')

    def render(search_value=''):
        rows, error = fetch_hierarchies(search_value)
        if error:
            error_label.set_text(error)
            table.rows = []
        else:
            error_label.set_text('')
            table.rows = [
                {
                    'hierarchy_name': r[0],
                    'root_theory': r[1] or '(none yet -- run sync.py)',
                    'num_prim_relations': r[2],
                    'relation_name': r[3] or '',
                    'nondecomp_hierarchies': r[4] or '',
                }
                for r in rows
            ]
        table.update()

    with ui.row().classes('mt-2 items-center gap-2'):
        search_input = ui.input(label='Filter by hierarchy name').classes('w-64')
        ui.button('Search', on_click=lambda: render(search_input.value), icon='search')
        ui.button('Clear', on_click=lambda: (search_input.set_value(''), render(''))[1])

    render()


ui.run(title='SEADOO Pipeline Dashboard', port=8080)