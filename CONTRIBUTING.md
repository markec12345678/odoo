# Contributing to Odoo Slovenian Tourism Suite

Thank you for your interest in contributing! This document covers guidelines for contributing to the 55 custom `l10n_si_*` modules.

## Quick Start

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/odoo.git
cd odoo
git remote add upstream https://github.com/markec12345678/odoo.git

# Create a feature branch
git checkout -b feature/my-new-feature 19.0

# Make changes, test, commit
python3 -m py_compile addons/l10n_si_my_module/models/*.py
ruff check addons/l10n_si_my_module/
git add -A
git commit -m "[ADD] l10n_si_my_module: new feature description"

# Push and create PR
git push origin feature/my-new-feature
```

## Branching Strategy

| Branch | Purpose |
|--------|---------|
| `19.0` | Main development branch (stable) |
| `feature/*` | New features (merge into `19.0`) |
| `fix/*` | Bug fixes (merge into `19.0`) |
| `hotfix/*` | Critical production fixes (merge into `19.0`) |

## Coding Standards

### Python

- Follow [Odoo coding guidelines](https://www.odoo.com/documentation/19.0/developer/reference/coding_guidelines.html)
- Target Python 3.10+ (use `from __future__ import annotations` where needed)
- Use `ruff` for linting (config in `ruff.toml`):

```bash
ruff check addons/l10n_si_*/
ruff format addons/l10n_si_*/
```

### XML

- Always validate with `xml.etree.ElementTree` before committing
- Use `&amp;` `&lt;` `&gt;` for special characters in XML attributes
- Escape `&` in domain filters: `[('field', '&amp;', 'value')]`

### Module structure

```
l10n_si_my_module/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── my_model.py
├── views/
│   └── my_model_views.xml
├── security/
│   └── ir.model.access.csv
├── data/
│   └── my_data.xml
├── reports/
│   └── my_report.xml
├── wizard/
│   ├── __init__.py
│   └── my_wizard.py
└── tests/
    ├── __init__.py
    └── test_my_model.py
```

### Manifest requirements

Every `__manifest__.py` must include:

```python
{
    'name': 'Module Name',
    'summary': 'One-line description',
    'version': '19.0.1.0.0',  # Must start with 19.0.
    'category': 'Category/Subcategory',
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'l10n_si'],
    'data': [
        'security/ir.model.access.csv',
        'views/my_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'countries': ['si'],  # For SI-specific modules
}
```

### Commit messages

Use Odoo conventional commit prefixes:

| Prefix | Usage |
|--------|-------|
| `[ADD]` | New module or major feature |
| `[IMP]` | Improvement to existing code |
| `[FIX]` | Bug fix |
| `[REF]` | Refactoring (no functional change) |
| `[REM]` | Removal of code/files |
| `[MOV]` | Moving files (no change) |
| `[MERGE]` | Merge commit |
| `[CLA]` | Contributor License Agreement |
| `[I18N]` | Translation updates |

Example: `[IMP] l10n_si_fiscal: add retry logic for FURS submission failures`

### Testing

- Every module with business logic must include tests under `tests/`
- Use `@tagged('post_install', '-at_install')` for tests that need all modules installed
- Use `TransactionCase` for unit tests, `HttpCase` for controller tests
- Run tests before every PR:

```bash
./odoo-bin -d testdb -i l10n_si_my_module \
    --test-enable --test-tags=/l10n_si_my_module \
    --stop-after-init
```

### Security

- **Never commit** API keys, passwords, `.p12` certificates, or tokens
- Use `ir.config_parameter` for storing secrets at runtime
- Always add `security/ir.model.access.csv` with proper ACLs
- Use `groups=` attribute on fields that contain sensitive data
- Add record rules for multi-company isolation

## Pull Request Process

1. **Search** existing PRs for duplicates
2. **Create** a PR against the `19.0` branch
3. **Describe** what changed and why
4. **Link** any related issues
5. **Ensure** all tests pass and `ruff check` is clean
6. **Request** review from a maintainer
7. **Address** review feedback
8. **Squash** commits if requested before merge

## Upstream Synchronization

To sync with upstream Odoo:

```bash
git remote add upstream https://github.com/odoo/odoo.git
git fetch upstream
git checkout 19.0
git merge upstream/19.0
# Resolve conflicts
./odoo-bin -d testdb -u all --stop-after-init
# Run tests
git push origin 19.0
```

## Reporting Issues

- **Bugs**: Use GitHub Issues with the `bug` label
- **Feature requests**: Use GitHub Issues with the `enhancement` label
- **Security vulnerabilities**: Use GitHub private vulnerability reporting (do NOT open public issues)
- **Questions**: Use GitHub Discussions

## License

By contributing, you agree that your contributions will be licensed under the LGPL-3.0 license.
