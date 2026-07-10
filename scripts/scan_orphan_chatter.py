#!/usr/bin/env python3
"""Scan SI/HR modules for orphan chatter (message_follower_ids field on a model
that does NOT inherit mail.thread).

Usage:
    python scripts/scan_orphan_chatter.py [addons_path]

Catches the bug class that caused the AI Concierge mail.thread removal
regression in v19.0.14.0 — views referencing message_follower_ids /
message_ids on models that don't inherit mail.thread.

Exit code: 0 = OK, 1 = orphans found.
"""
import os
import re
import sys
import glob
import ast
import xml.etree.ElementTree as ET


def find_addons_path():
    """Find the addons/ directory relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, '..', 'addons')
    if os.path.isdir(candidate):
        return os.path.abspath(candidate)
    if os.path.isdir('addons'):
        return os.path.abspath('addons')
    return os.path.join(os.getcwd(), 'addons')


ADDONS = find_addons_path()


def parse_python_classes(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        _name = None
        _inherit = None
        has_mail_thread = False
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == '_name':
                        if isinstance(stmt.value, ast.Constant):
                            _name = stmt.value.value
                    if isinstance(tgt, ast.Name) and tgt.id == '_inherit':
                        if isinstance(stmt.value, ast.Constant):
                            _inherit = stmt.value.value
                            if _inherit == 'mail.thread':
                                has_mail_thread = True
                        elif isinstance(stmt.value, ast.List):
                            inherits_list = [e.value for e in stmt.value.elts
                                             if isinstance(e, ast.Constant)]
                            _inherit = inherits_list[0] if inherits_list else None
                            if 'mail.thread' in inherits_list:
                                has_mail_thread = True
        yield (node.name, _name, _inherit, has_mail_thread)


def main():
    addons_path = sys.argv[1] if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) else ADDONS

    si_modules = sorted([
        d for d in os.listdir(addons_path)
        if (d.startswith('l10n_si_') or d.startswith('l10n_hr_'))
        and os.path.isdir(os.path.join(addons_path, d))
    ])

    # Also include Odoo core modules so we know which models are core
    repo_root = os.path.dirname(addons_path)
    core_addons_path = os.path.join(repo_root, 'odoo', 'addons')
    all_modules = si_modules + (
        [d for d in os.listdir(core_addons_path)
         if os.path.isdir(os.path.join(core_addons_path, d))]
        if os.path.isdir(core_addons_path) else []
    )

    model_inherits_mail = {}
    for mod in all_modules:
        if mod in si_modules:
            model_paths = glob.glob(f'{addons_path}/{mod}/models/*.py')
        else:
            model_paths = glob.glob(f'{core_addons_path}/{mod}/models/*.py')
        for py in model_paths:
            try:
                text = open(py).read()
            except Exception:
                continue
            for _class, _name, _inherit, has_mt in parse_python_classes(text):
                key = _name or _inherit
                if key:
                    prev = model_inherits_mail.get(key, (False, None, None))
                    if has_mt or not prev[0]:
                        model_inherits_mail[key] = (has_mt, mod, py)

    view_models = {}
    for mod in si_modules:
        for xml in glob.glob(f'{addons_path}/{mod}/views/*.xml'):
            try:
                tree = ET.parse(xml)
            except Exception:
                continue
            for rec in tree.iter('record'):
                if rec.get('model') == 'ir.ui.view':
                    rec_id = rec.get('id')
                    m_field = rec.find('field[@name="model"]')
                    if m_field is not None:
                        view_models[rec_id] = m_field.text

    issues = []
    total_chatter_views = 0
    for mod in si_modules:
        for xml in glob.glob(f'{addons_path}/{mod}/views/*.xml'):
            try:
                tree = ET.parse(xml)
            except Exception:
                continue
            for rec in tree.iter('record'):
                if rec.get('model') != 'ir.ui.view':
                    continue
                rec_id = rec.get('id')
                model = view_models.get(rec_id)
                has_chatter = any(f.get('name') == 'message_follower_ids'
                                  for f in rec.iter('field'))
                if has_chatter:
                    total_chatter_views += 1
                    info = model_inherits_mail.get(model)
                    if info is None:
                        issues.append((mod, os.path.basename(xml), rec_id, model,
                                       'MODEL NOT FOUND'))
                    elif not info[0]:
                        issues.append((mod, os.path.basename(xml), rec_id, model,
                                       f'NO mail.thread in {info[2]}'))

    print(f'Scanned {len(si_modules)} SI/HR modules in {addons_path}')
    print(f'Tracked models: {len(model_inherits_mail)}')
    print(f'Views with chatter field: {total_chatter_views}')
    print()
    if not issues:
        print('OK: no orphan chatter found')
        return 0
    print(f'FOUND {len(issues)} potential orphan(s):')
    for i in issues:
        print(' -', i)
    return 1


if __name__ == '__main__':
    sys.exit(main())
