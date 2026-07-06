# Contributing to SI/HR Odoo Localization

Hvala za zanimanje za sodelovanje! 🇸🇮🇭🇷

## 🚀 Hitri začetek

### 1. Fork & clone
```bash
git clone git@github.com:your-username/odoo.git
cd odoo
git checkout 19.0
git remote add upstream git@github.com:markec12345678/odoo.git
```

### 2. Setup development environment
```bash
pip install pre-commit ruff black isort
pre-commit install
docker compose up -d  # PostgreSQL + Odoo 19
```

### 3. Create a branch
```bash
git checkout -b feature/your-feature-name
```

### 4. Make changes & test
```bash
# Run standalone unit tests
python3 .github/scripts/run_unit_tests.py

# Run E2E tests
python3 .github/scripts/run_e2e_tests.py

# Lint
ruff check addons/l10n_si_* addons/l10n_hr_*
```

### 5. Commit & push
```bash
git add -A
git commit -m "[IMP] l10n_si_hotel: add feature X"
git push origin feature/your-feature-name
```

### 6. Create Pull Request
- Base: `19.0`
- Title: `[IMP/MOV/FIX] module_name: description`
- Fill in the PR template

---

## 📝 Konvencije

### Commit messages
Uporabljaj [Odoo commit conventions](https://github.com/odoo/odoo/wiki/Contributing#commit):
- `[IMP]` — improvement to existing feature
- `[MOV]` — move code (no logic change)
- `[FIX]` — bug fix
- `[ADD]` — new module or feature
- `[REF]` — refactoring
- `[DOC]` — documentation only

Format: `[TAG] module_name: short description`
```
[IMP] l10n_si_hotel: add folio service line wizard
[FIX] l10n_si_fiscal: correct ZOI computation for storno invoices
[ADD] l10n_hr_einvoice: UBL 2.1 B2B e-invoice support
```

### Module naming
- SI modules: `l10n_si_<name>` (e.g. `l10n_si_hotel`)
- HR modules: `l10n_hr_<name>` (e.g. `l10n_hr_fiscal`)

### Manifest requirements
Every `__manifest__.py` must have:
```python
{
    'name': 'Module Name',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'depends': [...],
    'data': [...],
    'installable': True,
}
```

### Code style
- Python: Black formatting, 120 char line length
- Imports: isort with black profile
- Linting: ruff (F + E9 rules)
- XML: 4-space indentation, no trailing whitespace

### Testing
- Standalone tests: `.github/scripts/run_unit_tests.py`
- E2E tests: `.github/scripts/run_e2e_tests.py`
- Odoo ORM tests: `tests/test_*.py` with `@tagged('post_install', '-at_install')`

---

## 🏗️ Arhitektura

### Moduli po tierjih

| Tier | Category | Modules |
|------|----------|---------|
| 1 | SI Regulatory | l10n_si_fiscal, l10n_si_edi, l10n_si_reports, l10n_si_vat_validation, l10n_si_sequence, l10n_si_bank_parser |
| 2 | SI Enterprise | l10n_si_hr_payroll_community, l10n_si_sign, l10n_si_bank_sync, l10n_si_helpdesk_simple, l10n_si_fleet |
| 3 | SI Business ops | l10n_si_approvals, l10n_si_knowledge, l10n_si_customer_statements, etc. |
| 4 | SI Tourism | l10n_si_hotel, l10n_si_restaurant, l10n_si_camping, l10n_si_farm_tourism, l10n_si_tourist_tax, l10n_si_wellness, l10n_si_event_venue, l10n_si_etourism |
| 5 | SI Hotel ops | l10n_si_housekeeping, l10n_si_loyalty_program, l10n_si_mobile_app, etc. |
| 6 | SI Finance | l10n_si_revenue_management, l10n_si_review_management, l10n_si_hr_roster, l10n_si_procurement, l10n_si_budget_planning, l10n_si_accounting_advanced |
| 7 | SI Guest services | l10n_si_website_booking, l10n_si_payment_gateway, l10n_si_concierge_services, l10n_si_transport, l10n_si_sustainability, l10n_si_data_protection |
| 8 | SI Accounting | l10n_si_assets, l10n_si_intrastat, l10n_si_vies_return, l10n_si_year_end_close, l10n_si_audit_trail, etc. |
| HR | Croatian | l10n_hr_fiscal (CISF), l10n_hr_evisitor (HTZ), l10n_hr_pdv (VAT) |

### Odvisnosti

```
l10n_si (base)
├── l10n_si_vat_validation
│   └── l10n_si_sequence
│       └── l10n_si_fiscal (FURS ZOI/EOR)
│           ├── l10n_si_hotel (PMS)
│           │   ├── l10n_si_restaurant
│           │   ├── l10n_si_camping
│           │   └── l10n_si_etourism (AJPES)
│           └── l10n_si_pos_advanced
├── l10n_si_tourist_tax
│   └── l10n_si_etourism
└── l10n_si_accounting_advanced
    └── l10n_si_reports (REK-1, M4)

l10n_hr (base)
├── l10n_hr_fiscal (CISF ZKI/JIR)
│   ├── l10n_hr_evisitor (HTZ REST)
│   └── l10n_hr_pdv (VAT reporting)
```

---

## 🔒 Varnost

- **Nikoli ne committaj certifikatov** (.p12, .pfx, .pem, .key) — so v `.gitignore`
- **Nikoli ne committaj gesel** ali API ključev
- **Nikoli ne committaj produkcijskih podatkov**

---

## 📞 Kontakt

- GitHub Issues: https://github.com/markec12345678/odoo/issues
- Pull Requests: https://github.com/markec12345678/odoo/pulls

---

Hvala za prispevek! 🙏
