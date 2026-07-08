# Contributing to SI/HR Tourism Suite for Odoo 19

Thank you for your interest in contributing! This project is the most complete Slovenian and Croatian tourism ERP built on Odoo 19.

## 🚀 Ways to Contribute

### 1. Bug Reports
- Use [GitHub Issues](https://github.com/markec12345678/odoo/issues)
- Include: Odoo version, module name, error traceback, steps to reproduce
- Check existing issues first to avoid duplicates

### 2. Feature Requests
- Open an issue with `[FEATURE]` prefix
- Describe the use case and expected behavior
- Reference relevant legislation (ZDavPR-1, ZTur-1, etc.)

### 3. Code Contributions

#### Prerequisites
- Odoo 19 development environment
- Python 3.10+
- PostgreSQL 15+
- `ruff` for linting (`pip install ruff`)

#### Development Setup
```bash
git clone -b 19.0 https://github.com/markec12345678/odoo.git
cd odoo
pip install -r requirements.txt
pre-commit install
```

#### Coding Standards
- Follow [Odoo 19 coding guidelines](https://www.odoo.com/documentation/19.0/developer/howtos/code_guidelines.html)
- Use `ruff` for linting: `ruff check addons/l10n_si_*/`
- All XML views must use `<list>` (not `<tree>`)
- Use `invisible="..."` instead of `attrs="{'invisible': ...}"`
- Template files go in `'qweb'` manifest section, not `'data'`
- No `category_id` or `users` fields on `res.groups`
- No `numbercall` field on `ir.cron`

#### Pull Request Process
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit with conventional commits: `[IMP]`, `[FIX]`, `[ADD]`, `[REF]`
4. Push and open a PR to `19.0` branch
5. Ensure CI passes
6. Wait for review

### 4. Translations
- Slovenian (sl_SI) and Croatian (hr_HR) translations welcome
- Edit `.po` files in `addons/<module>/i18n/`
- Use [Weblate](https://translation.odoo-community.org/) for OCA modules

### 5. Documentation
- Improve README.md
- Add screenshots to `static/screenshots/`
- Write blog posts or tutorials

## 📋 Module Development Guidelines

### Manifest (`__manifest__.py`)
```python
{
    'name': 'Module Name',
    'summary': 'One-line summary',
    'version': '19.0.1.0.0',
    'category': 'Hospitality',
    'author': 'Your Name',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'l10n_si'],
    'data': [
        'security/ir.model.access.csv',
        'views/model_views.xml',
        'views/model_menu.xml',
    ],
    'qweb': [
        'reports/report_template.xml',  # Only <template> files!
    ],
    'installable': True,
}
```

### View Files
- Views before menus in `data` list
- Use `<list>` not `<tree>`
- Use `invisible="..."` not `attrs=`
- No `string=` on `<form>` or `<group>` in `<search>`

### Security Files
- `ir.model.access.csv` — model access rights
- No `category_id` on `res.groups`
- No `users` field on `res.groups`
- `domain` (not `domain_force`) on `ir.rule`

## 🧪 Testing
```bash
# Run unit tests
python odoo-bin --test-enable --test-tags=/l10n_si -d test_db --stop-after-init

# Run specific module tests
python odoo-bin --test-enable --test-tags=/l10n_si_fiscal -d test_db --stop-after-init
```

## 📜 License
By contributing, you agree that your contributions will be licensed under LGPL-3.

## 🙏 Recognition
Contributors will be listed in the README.md credits section.
