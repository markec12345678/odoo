#!/usr/bin/env python3
"""Generate i18n .pot template files for all l10n_si/l10n_hr modules.

Run: python scripts/generate_i18n.py
This creates .pot files that translators can use to create .po files
for Slovenian (sl_SI) and Croatian (hr_HR) translations.
"""
import os
import subprocess
import sys
from pathlib import Path


def generate_pot_for_module(module_path: Path):
    """Generate .pot file for a single module."""
    module_name = module_path.name
    i18n_dir = module_path / "i18n"
    i18n_dir.mkdir(exist_ok=True)
    
    pot_file = i18n_dir / f"{module_name}.pot"
    
    # Use odoo-bin to extract translatable strings
    cmd = [
        sys.executable, "odoo-bin",
        "--addons-path=addons",
        "-d", "pot_gen",
        "--i18n-export",
        "--modules", module_name,
        "--pot",
        "-o", str(pot_file),
        "--stop-after-init",
        "--without-demo=True",
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and pot_file.exists():
            return True
        return False
    except Exception:
        return False


def main():
    addons_dir = Path("addons")
    if not addons_dir.is_dir():
        print("Error: addons/ directory not found")
        sys.exit(1)
    
    print("=" * 60)
    print("Generating i18n .pot files for all l10n modules")
    print("=" * 60)
    
    count = 0
    for module_dir in sorted(addons_dir.glob("l10n_si_*")):
        if not module_dir.is_dir():
            continue
        print(f"  📦 {module_dir.name}...", end=" ")
        if generate_pot_for_module(module_dir):
            print("✅")
            count += 1
        else:
            print("⏭️ (skipped)")
    
    for module_dir in sorted(addons_dir.glob("l10n_hr_*")):
        if not module_dir.is_dir():
            continue
        print(f"  📦 {module_dir.name}...", end=" ")
        if generate_pot_for_module(module_dir):
            print("✅")
            count += 1
        else:
            print("⏭️ (skipped)")
    
    print(f"\nGenerated {count} .pot files")
    print("\nTo create translations:")
    print("  1. Copy .pot to .po (e.g. sl_SI.po)")
    print("  2. Translate strings in .po file")
    print("  3. Place in module/i18n/ directory")


if __name__ == "__main__":
    main()
