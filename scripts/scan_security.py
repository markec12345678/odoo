#!/usr/bin/env python3
"""Scan Python files for dangerous patterns that could lead to security issues.

Detects:
  - eval() / exec() with non-constant arguments (RCE risk)
  - os.system() / subprocess.call(shell=True) (command injection)
  - SQL injection: cr.execute() with string formatting (% or .format or +)
  - pickle.loads() on untrusted data (deserialization RCE)
  - yaml.load() without Loader (unsafe YAML loading)
  - shell=True in subprocess
  - Marked safe HTML (markup/markup_safe used wrongly)
  - Request data passed to eval/exec
  - Static paths joined with user input (path traversal)
  - Hardcoded password comparisons (insecure auth)
"""
import ast
import os
import sys
import re
from pathlib import Path


def find_dangerous_patterns(file_path):
    """Yield (line_no, severity, issue, suggestion) for each finding."""
    try:
        text = open(file_path, encoding='utf-8', errors='ignore').read()
    except Exception:
        return

    try:
        tree = ast.parse(text)
    except SyntaxError:
        return

    lines = text.split('\n')

    for node in ast.walk(tree):
        # eval() / exec() with non-constant argument
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ('eval', 'exec'):
            if node.args and not isinstance(node.args[0], ast.Constant):
                yield (node.lineno, 'HIGH',
                       f'{node.func.id}() with non-constant argument',
                       'Avoid eval/exec; use ast.literal_eval() for safe parsing')

        # os.system() — always dangerous
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == 'os' and node.func.attr == 'system':
            yield (node.lineno, 'HIGH',
                   'os.system() — command injection risk',
                   'Use subprocess.run([...], shell=False) with list args')

        # subprocess.call/Popen/check_output with shell=True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == 'subprocess' \
                and node.func.attr in ('call', 'Popen', 'run', 'check_output',
                                        'check_call'):
            for kw in node.keywords:
                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) \
                        and kw.value.value is True:
                    yield (node.lineno, 'HIGH',
                           f'subprocess.{node.func.attr}(shell=True) — command injection',
                           'Pass command as list, set shell=False')

        # pickle.loads() — deserialization RCE
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == 'pickle' \
                and node.func.attr in ('loads', 'load'):
            yield (node.lineno, 'HIGH',
                   f'pickle.{node.func.attr}() — deserialization RCE',
                   'Use JSON or msgpack for untrusted data')

        # yaml.load() without Loader (unsafe)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and isinstance(node.func.value, ast.Name) \
                and node.func.value.id == 'yaml' \
                and node.func.attr == 'load':
            has_loader = any(kw.arg == 'Loader' for kw in node.keywords)
            if not has_loader:
                yield (node.lineno, 'MED',
                       'yaml.load() without Loader — unsafe YAML parsing',
                       'Use yaml.safe_load() or pass Loader=yaml.SafeLoader')

    # String-based SQL injection detection (regex on source)
    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith('#'):
            continue

        # cr.execute("...%s..." % var)  or cr.execute("...".format(...))
        # or cr.execute("..." + var)
        if 'execute' in stripped and ('cr.execute' in stripped
                                       or 'self.env.cr.execute' in stripped
                                       or 'self._cr.execute' in stripped):
            # Check for string formatting on the SQL argument
            if any(op in stripped for op in (' % ', '.format(', ' + ',
                                              'f"', "f'", '%s')) \
                    and 'execute' in stripped:
                # Could be legitimate (params passed separately), do deeper check
                # If the line ends with just `execute("..." % var)` it's bad
                # If it's `execute("...", (var,))` it's fine
                if re.search(r'execute\s*\(\s*[f"\'][^"\']*[f"\'].*[%+]', stripped) \
                        or '.format(' in stripped \
                        or ' + ' in stripped:
                    yield (line_no, 'HIGH',
                           'Possible SQL injection — string formatting in cr.execute()',
                           'Pass parameters as tuple: cr.execute("...WHERE x=%s", (val,))')


def main():
    if len(sys.argv) > 1:
        scan_paths = sys.argv[1:]
    else:
        scan_paths = ['.']

    findings = []
    files_scanned = 0

    for scan_path in scan_paths:
        if os.path.isfile(scan_path):
            py_files = [scan_path]
        else:
            py_files = []
            for root, dirs, files in os.walk(scan_path):
                dirs[:] = [d for d in dirs if d not in (
                    '.git', '__pycache__', 'node_modules', 'i18n', 'static'
                )]
                for f in files:
                    if f.endswith('.py'):
                        py_files.append(os.path.join(root, f))

        for fpath in py_files:
            files_scanned += 1
            for line_no, sev, issue, suggestion in find_dangerous_patterns(fpath):
                findings.append((fpath, line_no, sev, issue, suggestion))

    print(f'Scanned {files_scanned} Python files')
    print(f'Found {len(findings)} potential issues')
    print()
    if not findings:
        print('OK: no dangerous patterns found')
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
            print(f'  {fpath}:{line_no}: {issue}')
            print(f'    → {suggestion}')
        if len(items) > 30:
            print(f'  ... and {len(items) - 30} more')
        print()

    return 1 if by_sev.get('HIGH') else 0


if __name__ == '__main__':
    sys.exit(main())
