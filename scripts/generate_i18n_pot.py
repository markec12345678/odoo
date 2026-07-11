#!/usr/bin/env python3
"""Generate .pot translation template files for Odoo modules.

Extracts translatable strings from:
- Python files: fields.Char(string='...'), help='...', _(_('...'))
- XML files: <field name="string">...</field>, string="...", label="..."

Usage:
    python scripts/generate_i18n_pot.py [module1 module2 ...]

If no modules specified, generates for all l10n_si_* / l10n_hr_* modules
that don't already have an i18n/ directory with a .pot file.
"""
import ast
import os
import re
import sys
import glob
from pathlib import Path


# Standard POT header
POT_HEADER = '''# Translation of Odoo Server.
# This file contains the translation of the following modules:
# 	{module}
#
msgid ""
msgstr ""
"Project-Id-Version: Odoo Server 19.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2026-07-11 10:00:00+0000\\n"
"PO-Revision-Date: 2026-07-11 10:00:00+0000\\n"
"Last-Translator: \\n"
"Language-Team: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: \\n"
"Plural-Forms: \\n"

#. module: {module}
#: {module}
msgid "{module}"
msgstr ""

'''


def extract_strings_from_python(filepath):
    """Extract translatable strings from a Python file using AST.

    Looks for:
    - fields.X(string='...')
    - fields.X(help='...')
    - _('...')
    - _("...")
    - Selection([...]) string values in tuples
    """
    strings = set()
    try:
        text = open(filepath, encoding='utf-8').read()
    except Exception:
        return strings

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return strings

    for node in ast.walk(tree):
        # Look for keyword arguments named 'string' or 'help' with string values
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg in ('string', 'help', 'summary', 'description') \
                        and isinstance(kw.value, ast.Constant) \
                        and isinstance(kw.value.value, str):
                    strings.add(kw.value.value)

        # Look for _() calls
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == '_':
            if node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str):
                strings.add(node.args[0].value)

    return strings


def extract_strings_from_xml(filepath):
    """Extract translatable strings from an XML file.

    Looks for:
    - string="..." attributes
    - label="..." attributes
    - title="..." attributes
    - text content of <field name="name">...</field>
    - text content of <menuitem name="...">...</menuitem>
    - text content of <group string="...">
    - text content of <page string="...">
    - text content of <button string="...">
    """
    strings = set()
    try:
        text = open(filepath, encoding='utf-8').read()
    except Exception:
        return strings

    # Extract from attributes: string="...", label="...", title="..."
    # Use regex to find all attribute values
    for attr in ('string', 'label', 'title', 'name', 'placeholder', 'help'):
        # Match attr="value" or attr='value'
        pattern = rf'\b{attr}\s*=\s*"([^"]+)"'
        for m in re.finditer(pattern, text):
            val = m.group(1)
            # Skip non-translatable values (field names, model names, etc.)
            if attr == 'name':
                # Only translate name attributes that look like user-facing labels
                # Skip field names (lowercase with underscores), model names, etc.
                if val.isidentifier() or '.' in val or val.startswith('ir.') \
                        or val.startswith('model_') or val.startswith('view_'):
                    continue
                # Skip XML ids
                if '_' in val and val.replace('_', '').isalnum() and val.islower():
                    continue
            strings.add(val)

        pattern = rf"\b{attr}\s*=\s*'([^']+)'"
        for m in re.finditer(pattern, text):
            val = m.group(1)
            if attr == 'name':
                if val.isidentifier() or '.' in val or val.startswith('ir.') \
                        or val.startswith('model_') or val.startswith('view_'):
                    continue
                if '_' in val and val.replace('_', '').isalnum() and val.islower():
                    continue
            strings.add(val)

    return strings


def generate_pot_for_module(module_name, addons_path='.'):
    """Generate a .pot file for the given module."""
    mod_path = os.path.join(addons_path, module_name)
    if not os.path.isdir(mod_path):
        print(f'  SKIP: {module_name} — directory not found')
        return False

    # Collect all translatable strings
    all_strings = set()

    # Scan Python files
    for py_file in glob.glob(f'{mod_path}/models/*.py') + \
                    glob.glob(f'{mod_path}/controllers/*.py') + \
                    glob.glob(f'{mod_path}/wizard/*.py') + \
                    glob.glob(f'{mod_path}/*.py'):
        if os.path.basename(py_file) == '__init__.py':
            continue
        all_strings.update(extract_strings_from_python(py_file))

    # Scan XML files
    for xml_file in glob.glob(f'{mod_path}/views/*.xml') + \
                     glob.glob(f'{mod_path}/data/*.xml') + \
                     glob.glob(f'{mod_path}/reports/*.xml') + \
                     glob.glob(f'{mod_path}/wizard/*.xml') + \
                     glob.glob(f'{mod_path}/security/*.xml'):
        all_strings.update(extract_strings_from_xml(xml_file))

    if not all_strings:
        print(f'  SKIP: {module_name} — no translatable strings found')
        return False

    # Sort strings for deterministic output
    sorted_strings = sorted(all_strings, key=lambda s: s.lower())

    # Generate .pot content
    pot_content = POT_HEADER.format(module=module_name)

    for s in sorted_strings:
        # Escape special characters in msgid
        escaped = s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        pot_content += f'#: {module_name}\n'
        pot_content += f'msgid "{escaped}"\n'
        pot_content += f'msgstr ""\n\n'

    # Write .pot file
    i18n_dir = os.path.join(mod_path, 'i18n')
    os.makedirs(i18n_dir, exist_ok=True)
    pot_path = os.path.join(i18n_dir, f'{module_name}.pot')
    with open(pot_path, 'w', encoding='utf-8') as f:
        f.write(pot_content)

    print(f'  ✅ {module_name}: {len(sorted_strings)} strings → {pot_path}')
    return True


def main():
    if len(sys.argv) > 1:
        modules = sys.argv[1:]
        addons_path = 'addons'
    else:
        # Auto-detect all SI/HR modules without .pot files
        addons_path = 'addons'
        modules = []
        for d in sorted(os.listdir(addons_path)):
            if not (d.startswith('l10n_si_') or d.startswith('l10n_hr_')):
                continue
            mod_path = os.path.join(addons_path, d)
            if not os.path.isdir(mod_path):
                continue
            pot_path = os.path.join(mod_path, 'i18n', f'{d}.pot')
            if not os.path.exists(pot_path):
                modules.append(d)

    print(f'Generating .pot files for {len(modules)} module(s)...\n')

    generated = 0
    for mod in modules:
        if generate_pot_for_module(mod, addons_path):
            generated += 1

    print(f'\nDone: {generated}/{len(modules)} modules got .pot files')
    return 0 if generated > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
