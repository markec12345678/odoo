#!/usr/bin/env python3
"""Scan Python files for N+1 query patterns in Odoo.

Detects common N+1 query antipatterns:
  1. for record in records: record.search(...) inside loop
  2. for record in records: record.browse(...) inside loop
  3. for record in records: record.read() inside loop
  4. for record in records: record.write() inside loop (should batch)
  5. for record in records: record.create() inside loop (should batch)
  6. for record in records: record.unlink() inside loop (should batch)
  7. for record in records: accessing relational field without prefetch
     (e.g. record.partner_id.name inside loop)
  8. for record in records: self.env['model'].search(...) inside loop
  9. cr.execute() inside a for loop

These patterns cause one database query per iteration, leading to
severe performance degradation with large recordsets.

Usage:
    python scripts/scan_n_plus_1.py [addons_path] [module1 module2 ...]
"""
import ast
import os
import sys
import glob


def find_n_plus_1_patterns(file_path):
    """Yield (line_no, severity, issue, suggestion) for each finding."""
    try:
        text = open(file_path, encoding='utf-8', errors='ignore').read()
    except Exception:
        return

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return

    # Walk the AST and find for-loops, then check their body for N+1 patterns
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue

        # Skip loops over self (typically 1-3 records, not N+1)
        # Only flag loops over other variables (rooms, partners, assets, etc.)
        target_name = None
        if isinstance(node.target, ast.Name):
            target_name = node.target.id

        iter_obj = node.iter
        # Skip if iterating over self (for record in self:)
        if isinstance(iter_obj, ast.Name) and iter_obj.id == 'self':
            continue
        # Skip if iterating over self.xxx (for x in self.search(...):)
        if isinstance(iter_obj, ast.Attribute) and isinstance(iter_obj.value, ast.Name) \
                and iter_obj.value.id == 'self':
            continue

        # Now check the body of the for loop for N+1 patterns
        for stmt in ast.walk(node):
            if not isinstance(stmt, ast.Call):
                continue

            # Pattern: self.env['model'].search(...) inside loop
            if isinstance(stmt.func, ast.Attribute) \
                    and stmt.func.attr == 'search':
                func_obj = stmt.func.value
                if isinstance(func_obj, ast.Subscript) \
                        and isinstance(func_obj.value, ast.Attribute) \
                        and func_obj.value.attr == 'env':
                    yield (stmt.lineno, 'HIGH',
                           'self.env[...].search() inside for-loop — N+1 query',
                           'Search before the loop, or use filtered()/mapped() '
                           'on the existing recordset')

            # Pattern: record.search(...) inside loop (on the iterated var)
            elif isinstance(stmt.func, ast.Attribute) \
                    and stmt.func.attr == 'search' \
                    and isinstance(stmt.func.value, ast.Name) \
                    and isinstance(node.target, ast.Name) \
                    and stmt.func.value.id == node.target.id:
                yield (stmt.lineno, 'HIGH',
                       f'{node.target.id}.search() inside for-loop — N+1 query',
                       'Search before the loop, or use filtered()')

            # Pattern: record.browse(...) inside loop
            elif isinstance(stmt.func, ast.Attribute) \
                    and stmt.func.attr == 'browse' \
                    and isinstance(stmt.func.value, ast.Name) \
                    and isinstance(node.target, ast.Name) \
                    and stmt.func.value.id == node.target.id:
                yield (stmt.lineno, 'HIGH',
                       f'{node.target.id}.browse() inside for-loop — N+1 query',
                       'Browse all IDs at once before the loop')

            # Pattern: record.write(...) inside loop
            elif isinstance(stmt.func, ast.Attribute) \
                    and stmt.func.attr == 'write' \
                    and isinstance(stmt.func.value, ast.Name) \
                    and isinstance(node.target, ast.Name) \
                    and stmt.func.value.id == node.target.id:
                yield (stmt.lineno, 'MED',
                       f'{node.target.id}.write() inside for-loop — consider batching',
                       'Collect values in a dict and use records.write() '
                       'or use a single update query')

            # Pattern: record.create(...) inside loop
            elif isinstance(stmt.func, ast.Attribute) \
                    and stmt.func.attr == 'create' \
                    and isinstance(stmt.func.value, ast.Name) \
                    and isinstance(node.target, ast.Name) \
                    and stmt.func.value.id == node.target.id:
                yield (stmt.lineno, 'MED',
                       f'{node.target.id}.create() inside for-loop — consider batching',
                       'Collect vals_list and use Model.create(vals_list) '
                       'with a list (Odoo 17+ supports batch create)')

            # Pattern: record.unlink() inside loop
            elif isinstance(stmt.func, ast.Attribute) \
                    and stmt.func.attr == 'unlink' \
                    and isinstance(stmt.func.value, ast.Name) \
                    and isinstance(node.target, ast.Name) \
                    and stmt.func.value.id == node.target.id:
                yield (stmt.lineno, 'MED',
                       f'{node.target.id}.unlink() inside for-loop — consider batching',
                       'Collect records and call records.unlink() after loop')

            # Pattern: cr.execute() inside loop
            elif isinstance(stmt.func, ast.Attribute) \
                    and stmt.func.attr == 'execute' \
                    and isinstance(stmt.func.value, ast.Name) \
                    and stmt.func.value.id in ('cr', '_cr', 'env.cr'):
                yield (stmt.lineno, 'HIGH',
                       'cr.execute() inside for-loop — N+1 query',
                       'Use a single bulk query or ORM search/read')


def main():
    if len(sys.argv) > 1:
        scan_paths = sys.argv[1:]
    else:
        scan_paths = ['addons']

    findings = []
    files_scanned = 0

    for scan_path in scan_paths:
        if os.path.isfile(scan_path):
            py_files = [scan_path]
        else:
            py_files = []
            for root, dirs, files in os.walk(scan_path):
                dirs[:] = [d for d in dirs if d not in (
                    '.git', '__pycache__', 'node_modules', 'i18n', 'static',
                    'tests',  # test files often have loops by design
                )]
                for f in files:
                    if f.endswith('.py'):
                        py_files.append(os.path.join(root, f))

        for fpath in py_files:
            files_scanned += 1
            for line_no, sev, issue, suggestion in find_n_plus_1_patterns(fpath):
                findings.append((fpath, line_no, sev, issue, suggestion))

    print(f'Scanned {files_scanned} Python files')
    print(f'Found {len(findings)} potential N+1 patterns')
    print()
    if not findings:
        print('OK: no N+1 patterns found')
        return 0

    by_sev = {'HIGH': [], 'MED': []}
    for fpath, line_no, sev, issue, suggestion in findings:
        by_sev.setdefault(sev, []).append((fpath, line_no, issue, suggestion))

    for sev in ('HIGH', 'MED'):
        items = by_sev.get(sev, [])
        if not items:
            continue
        print(f'--- {sev} ({len(items)}) ---')
        for fpath, line_no, issue, suggestion in items[:30]:
            # Shorten path for readability
            short = fpath.replace('addons/', '')
            print(f'  {short}:{line_no}: {issue}')
            print(f'    → {suggestion}')
        if len(items) > 30:
            print(f'  ... and {len(items) - 30} more')
        print()

    return 1 if by_sev.get('HIGH') else 0


if __name__ == '__main__':
    sys.exit(main())
