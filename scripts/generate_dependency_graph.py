#!/usr/bin/env python3
"""Generate a Mermaid dependency graph for all SI/HR modules.

Reads __manifest__.py from each l10n_si_* / l10n_hr_* module and generates
a Mermaid flowchart showing module dependencies. Output can be rendered
by GitHub, GitLab, or any Mermaid-compatible viewer.

Usage:
    python scripts/generate_dependency_graph.py [output_file]

Default output: docs/module-dependencies.md
"""
import ast
import os
import sys
import glob
from pathlib import Path


def find_addons_path():
    """Find the addons/ directory relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, '..', 'addons')
    if os.path.isdir(candidate):
        return os.path.abspath(candidate)
    if os.path.isdir('addons'):
        return os.path.abspath('addons')
    return None


def get_module_deps(manifest_path):
    """Extract 'depends' list from a module's __manifest__.py."""
    try:
        text = open(manifest_path, encoding='utf-8').read()
        manifest = ast.literal_eval(text)
        return manifest.get('depends', [])
    except Exception:
        return []


def get_module_info(manifest_path):
    """Extract name, summary, version from manifest."""
    try:
        text = open(manifest_path, encoding='utf-8').read()
        manifest = ast.literal_eval(text)
        return {
            'name': manifest.get('name', ''),
            'summary': manifest.get('summary', ''),
            'version': manifest.get('version', ''),
            'depends': manifest.get('depends', []),
        }
    except Exception:
        return None


def categorize_module(mod_name):
    """Categorize a module by its name prefix."""
    if mod_name.startswith('l10n_si_'):
        return 'SI'
    elif mod_name.startswith('l10n_hr_'):
        return 'HR'
    elif mod_name in ('base', 'mail', 'web', 'website'):
        return 'CORE'
    return 'OTHER'


def generate_merdiad_graph(modules, addons_path):
    """Generate Mermaid flowchart of module dependencies.

    Only shows SI/HR modules and their direct dependencies on other
    SI/HR modules (to keep the graph readable).
    """
    lines = ['```mermaid', 'graph TD']

    # Group modules by category for visual clarity
    si_modules = []
    hr_modules = []

    for mod_name, info in sorted(modules.items()):
        cat = categorize_module(mod_name)
        if cat == 'SI':
            si_modules.append(mod_name)
        elif cat == 'HR':
            hr_modules.append(mod_name)

    # Add nodes with styling
    for mod in si_modules:
        # Sanitize node ID (Mermaid doesn't like dots)
        node_id = mod.replace('.', '_').replace('-', '_')
        label = mod.replace('l10n_si_', '')
        lines.append(f'    {node_id}["{label}"]')

    for mod in hr_modules:
        node_id = mod.replace('.', '_').replace('-', '_')
        label = mod.replace('l10n_hr_', '')
        lines.append(f'    {node_id}["{label}"]')

    lines.append('')

    # Add edges (only SI/HR → SI/HR to keep graph clean)
    for mod_name, info in sorted(modules.items()):
        if categorize_module(mod_name) not in ('SI', 'HR'):
            continue
        node_id = mod_name.replace('.', '_').replace('-', '_')
        for dep in info.get('depends', []):
            if categorize_module(dep) in ('SI', 'HR'):
                dep_id = dep.replace('.', '_').replace('-', '_')
                lines.append(f'    {dep_id} --> {node_id}')

    # Add styling
    lines.append('')
    lines.append('    classDef siModule fill:#e1f5fe,stroke:#0288d1,stroke-width:2px')
    lines.append('    classDef hrModule fill:#fff3e0,stroke:#f57c00,stroke-width:2px')

    for mod in si_modules:
        node_id = mod.replace('.', '_').replace('-', '_')
        lines.append(f'    class {node_id} siModule')

    for mod in hr_modules:
        node_id = mod.replace('.', '_').replace('-', '_')
        lines.append(f'    class {node_id} hrModule')

    lines.append('```')
    return '\n'.join(lines)


def generate_stats(modules):
    """Generate statistics about module dependencies."""
    si_count = sum(1 for m in modules if categorize_module(m) == 'SI')
    hr_count = sum(1 for m in modules if categorize_module(m) == 'HR')

    # Count edges
    si_si_edges = 0
    si_hr_edges = 0
    hr_si_edges = 0
    hr_hr_edges = 0
    core_edges = 0

    for mod_name, info in modules.items():
        for dep in info.get('depends', []):
            mod_cat = categorize_module(mod_name)
            dep_cat = categorize_module(dep)
            if mod_cat == 'SI' and dep_cat == 'SI':
                si_si_edges += 1
            elif mod_cat == 'SI' and dep_cat == 'HR':
                si_hr_edges += 1
            elif mod_cat == 'HR' and dep_cat == 'SI':
                hr_si_edges += 1
            elif mod_cat == 'HR' and dep_cat == 'HR':
                hr_hr_edges += 1
            elif dep_cat == 'CORE':
                core_edges += 1

    # Most depended-upon modules
    dep_count = {}
    for mod_name, info in modules.items():
        for dep in info.get('depends', []):
            if categorize_module(dep) in ('SI', 'HR'):
                dep_count[dep] = dep_count.get(dep, 0) + 1

    top_deps = sorted(dep_count.items(), key=lambda x: x[1], reverse=True)[:10]

    stats = f"""## Statistics

| Metric | Value |
|--------|-------|
| Total SI modules | {si_count} |
| Total HR modules | {hr_count} |
| SI → SI dependencies | {si_si_edges} |
| SI → HR dependencies | {si_hr_edges} |
| HR → SI dependencies | {hr_si_edges} |
| HR → HR dependencies | {hr_hr_edges} |
| Dependencies on Odoo core | {core_edges} |

### Top 10 Most Depended-Upon Modules

| Module | Depended by (count) |
|--------|---------------------|
"""
    for mod, count in top_deps:
        stats += f'| `{mod}` | {count} |\n'

    return stats


def main():
    addons_path = find_addons_path()
    if not addons_path:
        print('ERROR: addons/ directory not found')
        return 1

    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    if not output_file:
        # Default: docs/module-dependencies.md relative to repo root
        # addons/ is at repo root, so repo root = dirname(addons_path)
        repo_root = os.path.dirname(addons_path)
        output_file = os.path.join(repo_root, 'docs', 'module-dependencies.md')

    # Collect all SI/HR modules
    modules = {}
    for mod_dir in sorted(os.listdir(addons_path)):
        if not (mod_dir.startswith('l10n_si_') or mod_dir.startswith('l10n_hr_')):
            continue
        manifest_path = os.path.join(addons_path, mod_dir, '__manifest__.py')
        if not os.path.exists(manifest_path):
            continue
        info = get_module_info(manifest_path)
        if info:
            modules[mod_dir] = info

    print(f'Found {len(modules)} SI/HR modules')

    # Generate Mermaid graph
    graph = generate_merdiad_graph(modules, addons_path)
    stats = generate_stats(modules)

    # Write output
    content = f"""# Module Dependency Graph

This document shows the dependencies between all SI/HR Odoo modules.
The graph is rendered automatically by GitHub (Mermaid syntax).

Blue nodes = Slovenian modules (l10n_si_*)
Orange nodes = Croatian modules (l10n_hr_*)

Arrows point from dependency to dependent (A --> B means B depends on A).

## Dependency Graph

{graph}

{stats}

---

*Generated by `scripts/generate_dependency_graph.py`*
"""

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'Graph written to: {output_file}')
    print(f'Size: {os.path.getsize(output_file):,} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
