# Odoo 19.0 — Slovenian Tourism & Hospitality Suite

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](./LICENSE)
[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-875A7B.svg)](https://www.odoo.com)
[![Modules](https://img.shields.io/badge/Custom%20Modules-70-green.svg)](./addons/l10n_si_README.md)
[![Python](https://img.shields.io/badge/Python-3.10%20%E2%80%93%203.14-blue.svg)](./requirements.txt)
[![Branch](https://img.shields.io/badge/branch-19.0-blue.svg)]()

> **Fork of Odoo Community Edition 19.0** with 70 custom Slovenian localization modules covering regulatory compliance (FURS, eRačun, AJPES, Intrastat, VIES, GDPR), tourism vertical (hotels, restaurants, camps, farms, wellness, events), enterprise feature replacements (payroll, eIDAS signing, bank sync, helpdesk, fleet), back-office operations (housekeeping, HR roster, procurement, budget, accounting), and guest experience (booking engine, payment gateway, AI concierge, mobile PWA, loyalty).

---

## Table of Contents

1. [Overview](#overview)
2. [License](#license)
3. [Module Catalog](#module-catalog)
4. [System Requirements](#system-requirements)
5. [Installation](#installation)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Contributing](#contributing)
10. [Security](#security)
11. [Changelog](#changelog)
12. [Legal References](#legal-references)
13. [Support](#support)
14. [Credits](#credits)

---

## Overview

This repository is a **fork of the official Odoo Community 19.0** source tree, extended with **70 custom addons** (`l10n_si_*`) developed specifically for the **Slovenian tourism and hospitality market**.

### What's included

| Category | Count | Highlights |
|----------|-------|------------|
| Regulatory compliance | 6 | FURS ZOI/EOR, eSLOG 2.0 e-Račun, CAMT.053 bank parser, AJPES/REK-1/M4 reports, VAT validation, invoice numbering |
| Enterprise replacement | 5 | Slovenian payroll (ZDoh-2/ZPrD), eIDAS digital signing, bank sync, helpdesk, fleet |
| Business operations | 11 | Approvals, knowledge base, customer statements, subscriptions, field service, maintenance, quality control, timesheet approval, OCR, marketing automation, WhatsApp |
| Tourism vertical | 14 | Hotel PMS, restaurant (KOT), camping, farm tourism, tourist tax, event venue, accommodation blocks, equipment rental, vendor booking, contracts, wellness, channel manager, POS, AI concierge |
| Hotel operations | 6 | Housekeeping, maintenance requests, executive dashboard, loyalty program, group bookings, mobile PWA |
| Finance & HR | 6 | Revenue management (yield), review aggregation, HR roster (ZDR-1), procurement, budget planning, SRS accounting |
| Guest services & compliance | 6 | Website booking engine, payment gateway, concierge, transport, sustainability (Green Key), GDPR |
| Accounting, audit & hotel ops | 15 | Fixed assets, Intrastat, VIES, year-end close, audit trail, gift vouchers, minibar, laundry, partner portal, multi-company, weather, competitor pricing, accessibility, kitchen display, pets |
| **Total custom modules** | **70** | **~20,000 lines of Python** |

### What this fork is NOT

- **Not Odoo Enterprise** — Enterprise-only modules are not included. All custom modules are LGPL-3.0 licensed.
- **Not a security-hardened fork** — No security patches beyond upstream Odoo 19.0. Apply upstream patches via `git merge upstream/19.0`.
- **Not production-ready out of the box** — Modules require configuration (FURS certificates, bank APIs, etc.) before production use.

---

## License

This repository is licensed under the **GNU Lesser General Public License v3.0 (LGPL-3.0)**.

- The Odoo framework and all upstream modules are Copyright (c) 2004-2026 Odoo S.A. — see [`LICENSE`](./LICENSE) and [`COPYRIGHT`](./COPYRIGHT).
- All custom `l10n_si_*` modules are Copyright (c) 2026 markec12345678 — see individual `__manifest__.py` files.

### What LGPL-3.0 means

| You can | You must |
|---------|----------|
| Use commercially | Keep the LGPL license on modified LGPL files |
| Modify source code | Disclose source changes (via VCS history or changelog) |
| Distribute copies | Include the LICENSE and COPYRIGHT files |
| Sublicense | Attribute original authors (Odoo S.A. + markec12345678) |
| Sell as part of a larger product | Larger product may use any license, but LGPL modules must remain LGPL |

Custom modules you write on top of this repository may use **any license** — LGPL applies only to the Odoo source and our `l10n_si_*` modules.

### Third-party licenses

| Component | License | Source |
|-----------|---------|--------|
| Odoo Community | LGPL-3.0 | https://github.com/odoo/odoo |
| OCA/vertical-hotel (hotel module basis) | LGPL-3.0 | https://github.com/OCA/vertical-hotel |
| Python dependencies (requests, qrcode, etc.) | Various (BSD/MIT/Apache) | See `requirements.txt` |

---

## Module Catalog

All 55 custom modules are documented in detail in [`addons/l10n_si_README.md`](./addons/l10n_si_README.md). Summary by tier:

### Tier 1 — Regulatory compliance (mandatory for SI production)

| Module | Purpose |
|--------|---------|
| `l10n_si_vat_validation` | MOD11 checksum + FURS VIES lookup for SI VAT numbers |
| `l10n_si_sequence` | Invoice numbering per poslovni prostor (BL1-KASA1-2025-00001) |
| `l10n_si_fiscal` | FURS davčno potrjevanje: ZOI, EOR, QR code, retry cron |
| `l10n_si_edi` | FURS e-Račun eSLOG 2.0 XML generation, signing, submission |
| `l10n_si_bank_parser` | NLB/NKBM/Sparkasse/Addiko/Raiffeisen CAMT.053 + MT940 import |
| `l10n_si_reports` | AJPES SRS, REK-1, M4 XML exports for eDavki |

### Tier 2 — Enterprise replacement

| Module | Replaces | Purpose |
|--------|----------|---------|
| `l10n_si_hr_payroll_community` | `l10n_si_hr_payroll` | Slovenian payroll: ZDoh-2, ZPrD, M4, olajšave |
| `l10n_si_sign` | `sign` | eIDAS digital signing (SI-TRUST/CA HALCOM) |
| `l10n_si_bank_sync` | `bank_sync` | Auto-fetch daily statements from 5 SI banks |
| `l10n_si_helpdesk_simple` | `helpdesk` | Customer ticket system with SLA + portal |
| `l10n_si_fleet` | `fleet` (extended) | SI-specific: tehnični pregled, zavarovanje, vozni listi |

### Tier 3 — Business operations (11 modules)

Approvals, knowledge base, customer statements, subscriptions, field service, maintenance, quality control, timesheet approval, OCR invoice, marketing automation, WhatsApp integration.

### Tier 4 — Tourism vertical (6 modules)

Hotel PMS, restaurant (KOT + 14 allergens), camping (seasonal pricing), farm tourism (EKO certs), tourist tax (12 SI municipalities), event venue (weddings/conferences).

### Tier 5 — Advanced tourism & operations (14 modules)

Event accommodation, equipment rental, vendor booking, contracts, wellness/spa, channel manager (Booking.com/Airbnb), POS advanced, AI concierge, housekeeping, maintenance requests, executive dashboard, loyalty program, group bookings, mobile PWA.

### Tier 6 — Finance & HR (6 modules)

Revenue management (yield), review aggregation (Booking.com/TripAdvisor), HR roster (ZDR-1 shifts), procurement, budget planning, SRS accounting + financial ratios.

### Tier 7 — Guest services & compliance (6 modules)

Website booking engine, payment gateway (7 providers), concierge services, transport (airport shuttle), sustainability (Green Key), GDPR compliance.

### Tier 8 — Accounting, audit & hotel operations (15 modules)

Fixed assets (SI depreciation), Intrastat (EU trade), VIES return, year-end close (SRS 990/999), audit trail, gift vouchers, minibar, laundry, partner portal, multi-company (hotel chains), weather integration (14-day forecast), competitor pricing, accessibility (disabled guests), kitchen display system (KDS), pet management.

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| **Python** | 3.10 | 3.12 |
| **PostgreSQL** | 14 | 15 or 16 |
| **RAM** | 4 GB | 8 GB+ |
| **Disk** | 20 GB | 50 GB+ (NVMe SSD) |
| **wkhtmltopdf** | 0.12.6 (patched Qt) | Same |
| **Node.js** | 18+ | 20+ |
| **Less.js** | 4.0 | Latest |

### Python dependencies

```bash
pip install -r requirements.txt
pip install qrcode requests pillow
# For OCR: apt install tesseract-ocr tesseract-ocr-slv
# For XML signing: apt install xmlsec1
```

---

## Installation

### Quick start (development)

```bash
# 1. Clone this repository
git clone --branch 19.0 https://github.com/markec12345678/odoo.git
cd odoo

# 2. Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip wheel
pip install -r requirements.txt
pip install qrcode requests pillow

# 4. Set up PostgreSQL
sudo -u postgres createuser --createdb --no-createrole --no-superuser --pwprompt odoo
sudo -u postgres createdb -O odoo odoo_test

# 5. Install all custom modules
./odoo-bin \
    --addons-path=addons,odoo/addons \
    -d odoo_test \
    -i base,l10n_si,l10n_si_vat_validation,l10n_si_sequence,l10n_si_fiscal,l10n_si_edi,l10n_si_bank_parser,l10n_si_reports \
    --db_user=odoo --db_password=your_password \
    --without-demo=True \
    --stop-after-init

# 6. Start the server
./odoo-bin \
    --addons-path=addons,odoo/addons \
    -d odoo_test \
    --db_user=odoo --db_password=your_password
```

Open `http://localhost:8069` and log in with `admin` / `admin`.

### Production installation

For production deployment on a VPS, see the deployment scripts in [`/home/z/my-project/download/odoo-si-deploy/`](./SETUP.md):

```bash
sudo bash setup.sh --domain=erp.your-domain.si --email=admin@your-domain.si
```

This installs: PostgreSQL, Odoo, Nginx (HTTPS via Let's Encrypt), systemd services, daily backup, and all Tier 1 modules.

---

## Configuration

### Configuration order

Install and configure modules in this order:

1. **Tier 1** — FURS certificate, eIDAS certificate, bank parsers, reports
2. **Tier 2** — Payroll constants, sign certificate, bank sync API keys
3. **Tier 3** — Approvals rules, knowledge articles, subscription plans
4. **Tier 4** — Hotel rooms, restaurant menus, camping parcels, tourist tax rates
5. **Tier 5** — Channel manager API keys, POS config, AI concierge backend
6. **Tier 6** — Revenue rate plans, HR shifts, procurement vendors, budget
7. **Tier 7** — Booking engine, payment gateway, GDPR consents

### Key configuration files

| File | Purpose |
|------|---------|
| `/etc/odoo/odoo.conf` | Main Odoo configuration |
| `/etc/systemd/system/odoo.service` | systemd unit for Odoo HTTP |
| `/etc/systemd/system/odoo-longpolling.service` | systemd unit for gevent |
| `/etc/nginx/sites-available/odoo` | Nginx reverse proxy with HTTPS |
| `/usr/local/bin/odoo-backup.sh` | Daily backup script |

### FURS registration

Before going live with FURS davčno potrjevanje (ZOI/EOR), you must:

1. Register at [eDavki](https://edavki.fu.gov.si)
2. Obtain a test FURS certificate (`.p12`)
3. Register each poslovni prostor (business premise)
4. Test in FURS test environment (`blagajne-test.fu.gov.si`)
5. Obtain production FURS certificate
6. Switch to production (`blagajne.fu.gov.si`)

See [`FURS_Checklist.md`](./FURS_Checklist.md) for the full 4-week registration process.

---

## Testing

```bash
# Run all tests for a specific module
./odoo-bin -d testdb -i l10n_si_fiscal \
    --test-enable --test-tags=/l10n_si_fiscal \
    --stop-after-init

# Run tests for all l10n_si modules
./odoo-bin -d testdb \
    -i l10n_si_vat_validation,l10n_si_sequence,l10n_si_fiscal \
    --test-enable --test-tags=standard,-slow \
    --stop-after-init

# Lint with ruff
pip install ruff==0.15.0
ruff check addons/l10n_si_*
ruff format --check addons/l10n_si_*
```

---

## Deployment

### Production architecture

```
Internet → Nginx (TLS 1.2/1.3) → Odoo (4 workers, port 8069)
                                   Odoo Longpolling (gevent, port 8072)
                                   PostgreSQL 15
                                   Hetzner Storage Box (offsite backup)
```

### Worker sizing formula

```
workers = (CPU_cores × 2) + 1
RAM_per_worker = 2.5 GB (limit_memory_hard)
total_RAM = workers × 2.5GB + 2GB (PostgreSQL) + 1GB (OS)
```

### Backup strategy

- **Daily**: `pg_dump -Fc` + `filestore` tarball (14-day retention)
- **Weekly**: Full backup to offsite (Hetzner Storage Box)
- **Quarterly**: Restore test on a clean server

---

## Contributing

We welcome contributions! Please read [`CONTRIBUTING.md`](./CONTRIBUTING.md) for guidelines.

### Quick rules

1. Branch from `19.0`: `git checkout -b feature/my-feature 19.0`
2. Follow [Odoo coding guidelines](https://www.odoo.com/documentation/19.0/developer/reference/coding_guidelines.html)
3. Run `ruff check` and `ruff format` on changed files
4. Add or update tests under `tests/`
5. Use conventional commit prefixes: `[IMP]`, `[FIX]`, `[REF]`, `[ADD]`, `[REM]`
6. Open a PR against `19.0`

---

## Security

### Supported versions

| Version | Supported |
|---------|-----------|
| 19.0 | Active development |
| 18.0 | Not supported in this fork |
| 17.0 | Not supported in this fork |

### Reporting a vulnerability

**Do NOT open public issues for security vulnerabilities.**

Contact: markec12345678 (via GitHub private vulnerability reporting)

Include:
- Detailed description of the vulnerability
- Steps to reproduce
- Proof-of-concept script
- Affected versions
- Suggested fix (if any)

We will respond within 48 hours and provide a fix timeline.

### Critical security reminders

- **Revoke any exposed GitHub tokens immediately** — classic `ghp_` tokens with `repo` scope grant full access.
- **Use fine-grained tokens** scoped to specific repositories with `Contents: Read/Write` only.
- **Never commit `.p12` certificates or API keys** to the repository.
- **Store secrets** in environment variables or Odoo's `ir.config_parameter` with restricted access.
- **Enable `list_db = False`** in production to hide the database manager.
- **Set `dbfilter = ^your_db$`** to prevent cross-database access.

---

## Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for the full changelog.

### Recent releases

| Version | Date | Description |
|---------|------|-------------|
| 19.0.8.0 | 2026-06-23 | Tier 8: assets, Intrastat, VIES, year-end close, audit trail, gift vouchers, minibar, laundry, portal, multi-company, weather, competitor, accessibility, KDS, pets |
| 19.0.7.0 | 2026-06-23 | Tier 7: website booking, payment gateway, concierge, transport, sustainability, GDPR |
| 19.0.6.0 | 2026-06-22 | Tier 6: revenue management, reviews, HR roster, procurement, budget, accounting |
| 19.0.5.0 | 2026-06-22 | Tier 5: housekeeping, maintenance, dashboard, loyalty, group bookings, mobile PWA |
| 19.0.4.0 | 2026-06-22 | Tier 4-5: event venue + 8 advanced tourism modules |
| 19.0.3.0 | 2026-06-21 | Tier 3: 11 enterprise replacement modules |
| 19.0.2.0 | 2026-06-21 | Tier 2: payroll, sign, bank sync, helpdesk, fleet |
| 19.0.1.0 | 2026-06-20 | Tier 1: FURS, eRačun, bank parser, reports, VAT, sequence |

---

## Legal References

### Slovenian legislation

| Law | Reference | Modules affected |
|-----|-----------|------------------|
| ZDavPR-1 (davčno potrjevanje računov) | UR. l. RS š. 89/16 | `l10n_si_fiscal`, `l10n_si_pos_advanced` |
| ZDavR-1 (davčna številka) | UR. l. RS | `l10n_si_vat_validation` |
| ZEfUP (e-fakturiranje javni sektor) | UR. l. RS | `l10n_si_edi` |
| ZDoh-2 (dohodnina) | UR. l. RS | `l10n_si_hr_payroll_community` |
| ZPrD (prispevki socialno varstvo) | UR. l. RS | `l10n_si_hr_payroll_community` |
| ZTur-1 (turizem) | UR. l. RS š. 8/17 | `l10n_si_tourist_tax` |
| ZDR-1 (delovna razmerja) | UR. l. RS | `l10n_si_hr_roster` |
| ZVPot (varstvo potrošnikov) | UR. l. RS | `l10n_si_helpdesk_simple` |
| ZInfZOh (olajšave) | ZDoh-2 109. člen | `l10n_si_hr_payroll_community` |
| GDPR (EU 2016/679) | EU Regulation | `l10n_si_data_protection` |
| EU 1169/2011 (alergeni) | EU Regulation | `l10n_si_restaurant` |
| eIDAS (EU 910/2014) | EU Regulation | `l10n_si_sign`, `l10n_si_event_contract` |

### FURS technical specifications

- [FURS davčno potrjevanje računov](https://www.fu.gov.si/seznam/6892)
- [FURS eDavki portal](https://edavki.fu.gov.si)
- [FURS test environment](https://blagajne-test.fu.gov.si:9002/v1/cash_registers/)

### AJPES

- [AJPES SRS pravilnik](https://www.ajpes.si)
- Standardni računovodski izkazi v3.0

---

## Support

| Channel | Use for |
|---------|---------|
| [GitHub Issues](https://github.com/markec12345678/odoo/issues) | Bug reports, feature requests |
| [GitHub Discussions](https://github.com/markec12345678/odoo/discussions) | Questions, community help |
| [Odoo Forum](https://www.odoo.com/forum/help-1) | General Odoo questions |
| [FURS ePodpora](mailto:epodpora@fu.gov.si) | FURS API technical issues |

### Commercial support

For paid implementation, customization, and support in Slovenia:

| Provider | Specialization |
|----------|----------------|
| MOReko d.o.o. | Odoo partner, FURS integrations |
| Adacta d.o.o. | Custom development, banks |
| Misoma d.o.o. | eDavki, AJPES |
| B.S. Informatika | Slovenian localization |

---

## Credits

### Authors

- **markec12345678** — All 55 custom `l10n_si_*` modules
- **Odoo S.A.** — Odoo Community framework (upstream)
- **Serpent Consulting Services** — Original hotel module basis (OCA/vertical-hotel)
- **Odoo Community Association (OCA)** — Community modules and guidelines

### Acknowledgments

- [OCA/vertical-hotel](https://github.com/OCA/vertical-hotel) — Hotel module inspiration (LGPL-3)
- [OCA/pos](https://github.com/OCA/pos) — POS module patterns (AGPL-3)
- [OCA/l10n-slovenia](https://github.com/OCA/l10n-slovenia) — SI localization reference
- [guohuadeng/app-odoo](https://github.com/guohuadeng/app-odoo) — UI enhancement patterns (LGPL-3)

### Disclaimer

This software is provided "as is" without warranty of any kind. The authors are not liable for any damages arising from the use of this software. Users are responsible for ensuring compliance with all applicable Slovenian and EU regulations. Always test in a FURS test environment before going to production.
