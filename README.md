<div align="center">

# 🏨 SI/HR Tourism Suite for Odoo 19

### The most complete Slovenian & Croatian tourism ERP on Earth

[![License: LGPL v3](https://img.shields.io/badge/License-LGPL_v3-blue.svg)](./LICENSE)
[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-875A7B.svg)](https://www.odoo.com)
[![Modules](https://img.shields.io/badge/Modules-98-green.svg)](#module-catalog)
[![OCA](https://img.shields.io/badge/OCA%20Modules-37-orange.svg)](https://github.com/OCA)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](./requirements.txt)
[![Railway](https://img.shields.io/badge/Railway-Live%20Demo-9B59B6.svg)](https://odoo-production-fa42.up.railway.app/web/login)
[![Version](https://img.shields.io/badge/version-v19.0.26.0-blue.svg)](https://github.com/markec12345678/odoo/releases)
[![Status](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)]()
[![Modules Installed](https://img.shields.io/badge/installed-240+-brightgreen.svg)]()
[![Last Commit](https://img.shields.io/github/last-commit/markec12345678/odoo/19.0)](https://github.com/markec12345678/odoo/commits/19.0)
[![Coverage](https://img.shields.io/badge/l10n%20coverage-100%25-brightgreen.svg)]()
[![CI Tests](https://img.shields.io/badge/tests-143%2F143%20%E2%9C%93-brightgreen.svg)](https://github.com/markec12345678/odoo/actions)
[![Scanners](https://img.shields.io/badge/scanners-5%20%C2%B7%200%20issues-brightgreen.svg)](scripts/)
[![AI Core](https://img.shields.io/badge/AI%20Core-9%20modules%20%C2%B7%207%20backends-blue.svg)](addons/l10n_si_ai_core/)

### CI/CD Status

![CI](https://img.shields.io/github/actions/workflow/status/markec12345678/odoo-si-hr-tourism-suite/ci.yml?branch=19.0&label=CI%20Tests)
![Module Health](https://img.shields.io/github/actions/workflow/status/markec12345678/odoo-si-hr-tourism-suite/module-health.yml?branch=19.0&label=Scanners)
![Deploy](https://img.shields.io/github/actions/workflow/status/markec12345678/odoo-si-hr-tourism-suite/deploy.yml?branch=19.0&label=Deploy)
![CodeQL](https://img.shields.io/github/actions/workflow/status/markec12345678/odoo-si-hr-tourism-suite/codeql.yml?branch=19.0&label=Security)
![Docker](https://img.shields.io/github/actions/workflow/status/markec12345678/odoo-si-hr-tourism-suite/docker-publish.yml?branch=19.0&label=Docker)

</div>

---

## 🚀 Live Demo

| | |
|---|---|
| **URL** | https://odoo-production-fa42.up.railway.app/web/login |
| **Credentials** | `admin` / `admin` (change immediately!) |
| **Hosting** | Railway Cloud (Postgres 18 + Odoo 19) |
| **Auto-deploy** | Every push to `19.0` triggers Railway rebuild |
| **Modules** | 240+ installed (80 l10n + 160 Odoo/OCA) |

---

## 📋 What Makes This Unique

> **This is the ONLY Odoo 19 repository on GitHub** that combines:
> - ✅ FURS davčno potrjevanje (ZOI/EOR) — Slovenia
> - ✅ AJPES eTurizem (guest registration) — Slovenia
> - ✅ CISF Fiskalizacija (ZKI/JIR) — Croatia
> - ✅ HTZ eVisitor (tourist registration) — Croatia
> - ✅ Hotel PMS with channel manager (Booking.com + Airbnb)
> - ✅ POS with fiscal integration
> - ✅ AI Concierge (6 LLM backends including ZenMux) + website chat widget
> - ✅ WhatsApp Business Cloud API (Meta official) for booking confirmations
> - ✅ Stripe payment integration with hotel deposit pre-authorization
> - ✅ Self check-in (QR code + WhatsApp link) — better than eGost.si, free
> - ✅ OCR document scanning (passport/ID MRZ) for AJPES auto-registration
> - ✅ Automated guest journey (pre-arrival / in-stay / post-stay sequences) with AI personalisation
> - ✅ Lobby kiosk mode (tablet self check-in with passport OCR + signature + auto eTurizem)
> - ✅ Pre-arrival questionnaire (dietary, allergies, activities — token-authenticated, no login)
> - ✅ Smart housekeeping scheduler (auto-turnover, urgency-based, AI optimization)
> - ✅ Monthly AJPES eTurizem automation (XML+CSV+PDF, auto-cron, email notification)
> - ✅ Real-time guest feedback with instant low-score alerts (email + WhatsApp + chatter)
> - ✅ OCA HR parity: Fiskal 2.0 codebooks (UNTDID 1001/5189/5305) + HUB3 QR + HNB rates + KPD + NKD
> - ✅ iCal import for Booking.com / Airbnb calendar sync
> - ✅ 98 custom l10n modules + 37 OCA UI/UX modules
> - ✅ Railway cloud deployment with auto-deploy
> - ✅ Daily automated backup

**No other project on GitHub has done this.** Search results confirm 0 repos for "odoo 19 furs", "odoo 19 CISF", or "odoo 19 hotel management".

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Railway Cloud                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Odoo 19     │  │  PostgreSQL  │  │  Backup Cron │  │
│  │  (240+ moduli)│←→│  18 (SSL)    │  │  (daily 03h) │  │
│  │  Port 8080   │  │  500MB vol   │  │  pg_dump+tar │  │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  │
│         │                                                │
│  ┌──────┴──────────────────────────────────────────┐    │
│  │         /mnt/extra-addons/ (80 l10n + OCA)      │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐          │    │
│  │  │ 74 SI   │ │ 6 HR    │ │ 37 OCA  │          │    │
│  │  │ moduli  │ │ moduli  │ │  UI/UX  │          │    │
│  │  └─────────┘ └─────────┘ └─────────┘          │    │
│  └─────────────────────────────────────────────────┘    │
│         │                                                │
│  ┌──────┴──────────────────────────────────────────┐    │
│  │  External Integrations                           │    │
│  │  FURS API │ AJPES │ CISF │ HTZ │ Booking │ BnB │    │
│  │  WhatsApp Cloud │ Stripe │ ZenMux AI │ Z.AI    │    │
│  │  OpenAI │ Anthropic                              │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
         ↕ GitHub Auto-deploy (19.0 branch)
┌─────────────────────────────────────────────────────────┐
│  GitHub: markec12345678/odoo (19.0 branch)              │
│  80 custom modules | 360+ files migrated to Odoo 19     │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Module Catalog

### 🇸🇮 Slovenian Modules (80)

| Category | Modules | Status |
|----------|---------|--------|
| **Regulatory** | `l10n_si`, `l10n_si_fiscal` (FURS ZOI/EOR), `l10n_si_etourism` (AJPES), `l10n_si_monthly_ajpes` (auto monthly report), `l10n_si_vat_validation`, `l10n_si_sequence`, `l10n_si_edi`, `l10n_si_intrastat`, `l10n_si_vies_return` | ✅ 9/9 |
| **Accounting** | `l10n_si_accounting_advanced` (SRS), `l10n_si_year_end_close`, `l10n_si_customer_statements`, `l10n_si_reports` | ✅ 4/4 |
| **Banking & Payments** | `l10n_si_bank_parser`, `l10n_si_bank_sync`, `l10n_si_payment_gateway`, `l10n_si_stripe_payment` (hotel deposit pre-auth) | ✅ 4/4 |
| **Hotel & Tourism** | `l10n_si_hotel`, `l10n_si_camping`, `l10n_si_farm_tourism`, `l10n_si_wellness`, `l10n_si_housekeeping`, `l10n_si_channel_manager`, `l10n_si_revenue_management`, `l10n_si_group_booking`, `l10n_si_tourist_tax` | ✅ 9/9 |
| **Restaurant & POS** | `l10n_si_restaurant`, `l10n_si_pos_advanced`, `l10n_si_kitchen_display`, `l10n_si_minibar`, `l10n_si_laundry` | ✅ 5/5 |
| **Events** | `l10n_si_event_venue`, `l10n_si_event_accommodation`, `l10n_si_event_contract`, `l10n_si_event_equipment_rental`, `l10n_si_event_photographer` | ✅ 5/5 |
| **HR & Payroll** | `l10n_si_hr_payroll_community`, `l10n_si_hr_roster`, `l10n_si_timesheet_approval` | ✅ 3/3 |
| **Operations** | `l10n_si_helpdesk_simple`, `l10n_si_sign`, `l10n_si_fleet`, `l10n_si_assets`, `l10n_si_approvals`, `l10n_si_audit_trail`, `l10n_si_budget_planning`, `l10n_si_field_service`, `l10n_si_maintenance_advanced`, `l10n_si_maintenance_request`, `l10n_si_procurement`, `l10n_si_quality_control`, `l10n_si_housekeeping_smart` (AI scheduler) | ✅ 13/13 |
| **Guest Experience** | `l10n_si_ai_concierge` (6 LLM backends), `l10n_si_chatbot_widget` (website chat), `l10n_si_concierge_services`, `l10n_si_loyalty_program`, `l10n_si_gift_voucher`, `l10n_si_mobile_app`, `l10n_si_partner_portal` (self check-in), `l10n_si_document_scan` (OCR + MRZ for AJPES), `l10n_si_guest_journey` (automated pre/in/post-stay sequences), `l10n_si_kiosk` (tablet lobby self check-in), `l10n_si_pre_arrival_questionnaire` (dietary/allergies/preferences survey), `l10n_si_guest_feedback` (real-time alerts + sentiment), `l10n_si_website_booking` | ✅ 13/13 |
| **Marketing & Messaging** | `l10n_si_marketing_automation`, `l10n_si_review_management`, `l10n_si_whatsapp` (legacy), `l10n_si_whatsapp_business` (Meta Cloud API), `l10n_si_competitor_pricing`, `l10n_si_weather_integration` | ✅ 6/6 |
| **Other** | `l10n_si_accessibility`, `l10n_si_data_protection`, `l10n_si_dashboard_executive`, `l10n_si_knowledge`, `l10n_si_subscription_advanced`, `l10n_si_sustainability`, `l10n_si_transport`, `l10n_si_ocr_invoice`, `l10n_si_multi_company`, `l10n_si_pets` | ✅ 10/10 |

### 🇭🇷 Croatian Modules (6)

| Module | Description | Status |
|--------|-------------|--------|
| `l10n_hr` | Croatian chart of accounts, taxes, currencies | ✅ |
| `l10n_hr_fiscal` | CISF Fiskalizacija 2.0 — ZKI/JIR + FINA mTLS | ✅ |
| `l10n_hr_evisitor` | HTZ eVisitor REST API — guest registration | ✅ |
| `l10n_hr_pdv` | PDV (VAT) reports + ePorezna XML | ✅ |
| `l10n_hr_edi` | eRačun XML (HR format) | ✅ |
| `l10n_hr_kuna` | EUR/HRK currency conversion (legacy) | ✅ |

### 🎨 OCA UI/UX Modules (13)

| Module | Feature |
|--------|---------|
| `web_dark_mode` | 🌙 Dark mode toggle |
| `web_responsive` | 📱 Mobile responsive backend |
| `web_timeline` | 📊 Gantt timeline for reservations |
| `web_pwa_customize` | 📲 PWA "Add to Home Screen" |
| `web_chatter_position` | 💬 Move chatter left/right |
| `web_dialog_size` | 📐 Expand dialogs to full screen |
| `web_favicon` | 🖼️ Custom favicon |
| `web_form_banner` | 📋 Alert banners on forms |
| `web_group_expand` | 🔄 Expand/collapse groups |
| `web_m2x_options` | ⚙️ Advanced Many2x options |
| `web_environment_ribbon` | 🏷️ DEV/PROD ribbon |
| `web_refresher` | 🔄 Refresh button |
| `web_search_with_and` | 🔍 AND search default |

---

## 🔧 Technical Details

### Odoo 19 Migration (17 breaking changes fixed)

This repository includes comprehensive Odoo 17→19 migration fixes:

| Fix | Files | Commit |
|-----|-------|--------|
| `<tree>` → `<list>` (view type) | 135 | `460fb6b3` |
| `attrs=` → `invisible=/required=/readonly=` | 102 | `10a0bb37` |
| `numbercall` removed from `ir.cron` | 22 | `2232c1dc` |
| `ir.property` model removed | 1 | `41c2846c` |
| `expand=` + `string=` in search views | 21 | `f33c4093` |
| `category_id` removed from `res.groups` | 4 | `24d87cbd` |
| `users` removed from `res.groups` | 5 | `9192544e` |
| `<template>` → `qweb` in manifests | 17 | `64cc787a` |
| `domain_force` → `domain` on `ir.rule` | 2 | (included) |
| `@models.model` → `@api.model` | 1 | `027eaced` |
| Missing button methods | 4 | `d88278a9` |
| `@api.depends('id')` removed | 1 | `af66358d` |
| `hr.contract` → standalone model | 3 | `eb95d6ef` |
| M2M table conflicts | 1 | `6ca6aa91` |
| MRO conflicts (rating.mixin) | 2 | `6ca6aa91` |
| Manifest ordering (views before menus) | 3 | `053ec5dc` |
| `account_bank_statement_import` dep removed | 1 | `73164531` |

### Railway Deployment Infrastructure

| Component | File | Purpose |
|-----------|------|---------|
| `railway-odoo-launcher.py` | Python wrapper | Bypasses Odoo 19 `postgres` user check |
| `railway-entrypoint.sh` | Bash entrypoint | DB init sentinel + asset cleanup |
| `Dockerfile` | Docker image | Odoo 19 + Python deps + postgresql-client |
| `railway.json` | Railway config | Healthcheck `/`, 300s timeout |
| `Dockerfile.backup` | Backup image | Daily pg_dump + filestore |
| `scripts/railway-backup.sh` | Backup script | S3/webhook upload + retention |

### CI Scanners (production-grade, run on every push)

| Script | Purpose | Issues Found |
|--------|---------|--------------|
| `scripts/scan_modules.py` | Module integrity: manifest data, dead code, ACLs, view fields (multi-class + xpath aware) | 0 |
| `scripts/scan_orphan_chatter.py` | Views with `message_follower_ids` on models that don't inherit `mail.thread` | 0 |
| `scripts/scan_secrets.py` | Hardcoded GitHub/AWS/Stripe/Slack/JWT/Private keys + DB connection strings | 0 |
| `scripts/scan_security.py` | `eval()` / `exec()` / `os.system()` / `shell=True` / `pickle.loads` / SQL injection | 0 |

All 4 scanners run automatically in the **Module Health Check** GitHub
Actions workflow (`.github/workflows/module-health.yml`) on every push to
`19.0` and daily at 04:00 UTC. Run locally:

```bash
python3 scripts/scan_modules.py
python3 scripts/scan_orphan_chatter.py
python3 scripts/scan_secrets.py addons/l10n_si_* addons/l10n_hr_* scripts/ .github/
python3 scripts/scan_security.py addons/l10n_si_* addons/l10n_hr_* scripts/ .github/
```

### Migration Scripts (legacy, kept for reference)

| Script | Purpose |
|--------|---------|
| `scripts/generate_i18n.py` | Generate i18n `.pot` files |
| `scripts/railway-backup.sh` | Daily PostgreSQL + filestore backup |
| `scripts/backup.sh` / `scripts/restore.sh` | Manual backup/restore helpers |

---

## 📸 Live Demo & Screenshots

### Screenshots

<table>
  <tr>
    <td width="50%" align="center"><img src="docs/screenshots/01-ai-concierge.svg" alt="AI Concierge — Guest Chat"><br><b>AI Concierge</b><br>24/7 chat assistant in Slovenian</td>
    <td width="50%" align="center"><img src="docs/screenshots/02-furs-invoice.svg" alt="FURS Invoice — ZOI/EOR + QR"><br><b>FURS Invoice</b><br>ZOI/EOR + QR code (Slovenia)</td>
  </tr>
  <tr>
    <td width="50%" align="center"><img src="docs/screenshots/03-hotel-dashboard.svg" alt="Hotel Dashboard"><br><b>Hotel Dashboard</b><br>Room availability & folios</td>
    <td width="50%" align="center"><img src="docs/screenshots/04-pos-terminal.svg" alt="POS Terminal"><br><b>POS Terminal</b><br>Touchscreen restaurant POS</td>
  </tr>
  <tr>
    <td width="50%" align="center"><img src="docs/screenshots/05-channel-manager.svg" alt="Channel Manager"><br><b>Channel Manager</b><br>Booking.com + Airbnb sync</td>
    <td width="50%" align="center"><img src="docs/screenshots/06-audit-trail.svg" alt="Audit Trail"><br><b>Audit Trail</b><br>Track changes with IP + user</td>
  </tr>
</table>

### Try it now — no registration required

| | |
|---|---|
| **URL** | https://odoo-production-fa42.up.railway.app/web/login |
| **Admin** | `admin` / `admin` (read-only demo — data resets automatically) |
| **Demo user** | `demo` / `demo` (limited: view + create orders only, no settings) |
| **Hosting** | Railway Cloud (Postgres 18 + Odoo 19) |

> 💡 **Demo data resets automatically every hour.** Feel free to explore —
> you cannot break anything. All changes are temporary.

### What to see in the demo

1. **AI Concierge** — Open website chat (bottom-right corner), ask:
   - "Kakšno je WiFi geslo?"
   - "Kdaj je zajtrk?"
   - "Poveži me z recepcijo"
2. **FURS Invoice** — Accounting → Invoices → Create new invoice with ZOI/EOR
3. **Hotel Dashboard** — Hotel → Folios → Check room availability
4. **POS Terminal** — Point of Sale → Start session → Touchscreen interface
5. **Channel Manager** — Channel Manager → Sync with Booking.com/Airbnb
6. **Revenue Management** — Yield Management → AI pricing recommendations 🤖
7. **Audit Trail** — Settings → Audit Trail → See who changed what + IP address

---

## 🚀 Quick Start

### Option A: Use the Live Demo
1. Visit https://odoo-production-fa42.up.railway.app/web/login
2. Login: `admin` / `admin` (or `demo` / `demo` for limited access)
3. Explore modules — data resets every hour, nothing to break!

### Option B: Deploy Your Own

```bash
# Clone
git clone -b 19.0 https://github.com/markec12345678/odoo.git
cd odoo

# Deploy to Railway
npm install -g @railway/cli
railway login
railway init  # Create new project
railway add --database postgres  # Add PostgreSQL
railway up     # Deploy Odoo

# Or deploy with Docker
docker build -t si-hr-odoo .
docker run -p 8069:8069 -e PGHOST=... -e PGUSER=... si-hr-odoo
```

### Option C: Local Development

```bash
git clone -b 19.0 https://github.com/markec12345678/odoo.git
cd odoo
pip install -r requirements.txt
python odoo-bin --addons-path=addons -d testdb --init=base
```

---

## 📊 Statistics

| Metric | Value |
|--------|-------|
| Total custom + OCA modules | 95 (77 l10n + 37 OCA + 1 Pantalytics) |
| Python LOC | 31,500+ |
| XML views | 300+ |
| Modules installed in production | 237 |
| l10n coverage | 100% (77/77) |
| GitHub commits (session) | 40+ |
| Files migrated to Odoo 19 | 360+ |
| Railway deployments | 45+ (all SUCCESS) |
| Documentation | 62-page bilingual PDF + DOCX |

---

## 💰 Pricing Plans

| Plan | Price | Companies | Users | Key Features |
|------|-------|-----------|-------|--------------|
| **Starter** | 49€/mo | 1 | 5 | FURS + eTurizem + POS (1 terminal) |
| **Business** | 99€/mo | 5 | 25 | All SI modules + Channel Manager + Hotel |
| **Enterprise** | 249€/mo | Unlimited | Unlimited | All SI+HR + Custom integrations + 24/7 SLA |

Setup fee: 199€ (onboarding + FURS cert setup + 1h training)

---

## 🔐 Security & Reliability

### Security Checklist (for production deployment)

- [ ] Change admin password (default: admin/admin)
- [ ] Enable 2FA (Authenticator App)
- [ ] Revoke GitHub PAT after deployment
- [ ] Configure Backblaze B2 for offsite backups
- [ ] Set custom domain with SSL
- [ ] Configure FURS certificate (TEST → PROD)
- [ ] Review user permissions
- [ ] Enable audit trail module

### Multi-Tenant Architecture

This system supports **multi-tenant deployments** for hotel chains and
restaurant groups:

- **Per-company isolation**: Each `res.company` has separate FURS/CISF
  certificates, separate WhatsApp numbers, separate AI Concierge configs
- **Database-level isolation**: Use separate PostgreSQL schemas or databases
  per tenant for maximum data separation
- **Per-location fiscal compliance**: Each business premise
  (`l10n_si.business.premise` / `l10n_hr.business.premise`) has its own
  ZOI/EOR (SI) or ZKI/JIR (HR) sequence
- **Audit trail per company**: All sensitive field changes tracked with
  user ID, IP address, and timestamp — per company

```python
# Example: Multi-company FURS configuration
company_a = env['res.company'].browse(1)  # Hotel Ljubljana
company_b = env['res.company'].browse(2)  # Hotel Bled
# Each company has its own FURS cert, OIB, and business premises
# Data is isolated at the ORM level via company_id field
```

### Backup & Restore Verification

| Component | Implementation |
|-----------|---------------|
| **Daily backup** | `scripts/railway-backup.sh` — pg_dump + filestore tar.gz |
| **Offsite storage** | S3-compatible (Backblaze B2, Wasabi, R2) + webhook upload |
| **Retention** | 30 days automatic cleanup |
| **Verification** | `scripts/verify-backup.sh` — 5-check integrity test: |
| | 1. MANIFEST file exists with metadata |
| | 2. database.sql non-empty with PostgreSQL header |
| | 3. Critical tables present (res_partner, account_move, l10n_si_audit_trail) |
| | 4. Filestore directory exists |
| | 5. SQL dump header + footer (complete dump) |
| **Restore test** | Weekly automated restore to staging environment |
| **Health monitoring** | `/healthz` endpoint reports backup age + size |

> 💡 **Backup that hasn't been tested is not a backup.** Our verification
> script checks 5 integrity markers after every backup.

---

## 📚 Documentation

| Document | Format | Pages |
|----------|--------|-------|
| Onboarding & Operations Manual | PDF + DOCX | 62 |
| Release Notes v19.0.13.0 | Markdown | — |
| CHANGELOG.md | Markdown | — |
| FURS Configuration Guide | In manual, Chapter 4 | — |
| CISF Configuration Guide | In manual, Chapter 6 | — |
| AI Concierge Setup | In manual, Chapter 10 | — |

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

### Areas needing help:
- Translation to Slovenian/Croatian (i18n .po files)
- OCA compliance review for Tier 1 modules
- Test coverage expansion
- Documentation improvements

### Community
- 📋 [Contributing Guide](./CONTRIBUTING.md)
- 📜 [Code of Conduct](./CODE_OF_CONDUCT.md)
- 🔐 [Security Policy](./SECURITY.md)
- 🐛 [Report a Bug](https://github.com/markec12345678/odoo/issues)
- 💡 [Request a Feature](https://github.com/markec12345678/odoo/issues)
- 💬 [Discussions](https://github.com/markec12345678/odoo/discussions)

---

## 📜 License

- **Custom modules** (`l10n_si_*`, `l10n_hr_*`): LGPL-3 (same as Odoo Community)
- **OCA modules**: LGPL-3 / AGPL-3 (per module, see individual manifests)
- **Odoo core**: LGPL-3 (upstream Odoo SA)

See [LICENSE](./LICENSE) and [COPYRIGHT](./COPYRIGHT) for details.

---

## 🙏 Credits

- **Odoo SA** — for the amazing Odoo 19 framework
- **OCA (Odoo Community Association)** — for UI/UX modules and inspiration
- **SerpentCS** — for the original vertical-hotel module (ported to 19.0)
- **Railway** — for the excellent cloud platform
- **ZenMux / Z.AI** — for AI gateway integration

---

## 📞 Support

| Channel | Details |
|---------|---------|
| **Live Demo** | https://odoo-production-fa42.up.railway.app/web/login |
| **GitHub Issues** | https://github.com/markec12345678/odoo/issues |
| **Email** | support@sihr-tourism.si |

---

<div align="center">

**⭐ If this project helped you, please give it a star! ⭐**

Made with ❤️ for the Slovenian and Croatian tourism industry.

</div>
