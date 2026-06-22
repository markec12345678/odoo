# Slovenian Localization Modules for Odoo 19.0

Fifty-five custom addons developed for the Slovenian market. All installed via the
standard `--addons-path` mechanism; each depends on the previous one(s) as
noted below.

## Modules

### Tier 1 — Core regulatory compliance (mandatory for production SI deployment)

| Module | Depends on | Purpose |
|--------|-----------|---------|
| `l10n_si_vat_validation` | `base_vat`, `l10n_si` | MOD11 checksum + FURS VIES lookup for SI VAT numbers |
| `l10n_si_sequence` | `account`, `l10n_si` | Invoice numbering per poslovni prostor (BL1-KASA1-2025-00001) |
| `l10n_si_fiscal` | `l10n_si_sequence`, `l10n_si_vat_validation` | FURS davčno potrjevanje: ZOI, EOR, QR code, retry cron |
| `l10n_si_edi` | `account_edi_ubl_cii`, `l10n_si_vat_validation` | FURS e-Račun (eSLOG 2.0) generation, signing, submission |
| `l10n_si_bank_parser` | `account_bank_statement_import` | NLB/NKBM/Sparkasse/Addiko/Raiffeisen CAMT.053 + MT940 import |
| `l10n_si_reports` | `account`, `l10n_si_vat_validation` | AJPES SRS, REK-1, M4 XML exports for eDavki |

### Tier 2 — Enterprise replacement (closes 80% of Odoo Enterprise feature gap)

| Module | Depends on | Replaces Enterprise | Purpose |
|--------|-----------|---------------------|---------|
| `l10n_si_hr_payroll_community` | `hr`, `hr_contract`, `l10n_si` | `l10n_si_hr_payroll` | Slovenske plače: ZDoh-2, ZPrD, M4, REK-SH, olajšave, letni obračun |
| `l10n_si_sign` | `mail`, `l10n_si` | `sign` | EIDAS digital signing (SI-TRUST/CA HALCOM), PAdES/XAdES, TSA timestamp |
| `l10n_si_bank_sync` | `account`, `l10n_si_bank_parser` | `bank_sync` | Auto-fetch daily statements from NLB/NKBM/Sparkasse/Addiko/Raiffeisen |
| `l10n_si_helpdesk_simple` | `mail`, `portal`, `rating` | `helpdesk` | Customer ticket system with SLA tracking + customer portal |
| `l10n_si_fleet` | `fleet`, `hr` | `fleet` (extended) | SI-specific: tehnični pregled, zavarovanje, registracija, vozni listi |

### Tier 3a — Critical for SI business operations

| Module | Depends on | Replaces Enterprise | Purpose |
|--------|-----------|---------------------|---------|
| `l10n_si_approvals` | `hr`, `hr_holidays`, `purchase`, `hr_expense` | `approvals` | Multi-step approval workflows (potni nalogi, dopusti, nakupi) |
| `l10n_si_knowledge` | `mail`, `portal` | `knowledge` | Internal wiki + document templates with version history |
| `l10n_si_customer_statements` | `account`, `mail` | `account_customer_statements` | Monthly customer statements with aging buckets |
| `l10n_si_subscription_advanced` | `account`, `sale_management` | `sale_subscription` | Recurring billing (SaaS, memberships, leases) with auto-invoicing |
| `l10n_si_field_service` | `hr`, `stock`, `account` | `fieldservice` | Work orders + dispatching + customer signature + photo evidence |

### Tier 3b — Important for specific business types

| Module | Depends on | Replaces Enterprise | Purpose |
|--------|-----------|---------------------|---------|
| `l10n_si_maintenance_advanced` | `maintenance`, `stock` | `maintenance` (extended) | Preventive schedules, MTBF/MTTR, spare parts, downtime analysis |
| `l10n_si_quality_control` | `stock`, `mrp` | `quality_control` | Inspection checklists, NCR, CAPA, ISO 9001 audit trail |
| `l10n_si_timesheet_approval` | `hr_timesheet` | `hr_timesheet_approval` | Weekly timesheet approval workflow with line locking |
| `l10n_si_ocr_invoice` | `account`, `mail` | `account_ocr` | OCR scan supplier invoices (Tesseract / Google DocAI / AWS Textract) |
| `l10n_si_marketing_automation` | `mail`, `mass_mailing` | `marketing_automation` | Multi-step email campaigns with branching + triggers |
| `l10n_si_whatsapp` | `mail`, `base` | `whatsapp` | WhatsApp Cloud API + Twilio integration, templates, GDPR opt-in |

### Tier 4 — Tourism vertical (hotels, restaurants, camps, farms, events)

| Module | Depends on | Origin | Purpose |
|--------|-----------|--------|---------|
| `l10n_si_hotel` | `l10n_si_fiscal`, `l10n_si_sequence` | Ported from OCA/vertical-hotel 17.0 (SerpentCS) | Hotel PMS: rooms, reservations, folio, check-in/out with FURS ZOI/EOR |
| `l10n_si_restaurant` | `pos_restaurant`, `l10n_si_fiscal` | Custom | Menus with 14 allergens (EU 1169/2011), tables, KOT (kitchen order tickets), FURS |
| `l10n_si_camping` | `l10n_si_fiscal`, `l10n_si_sequence` | Custom | Campsite parcels (tent/RV/cabin/glamping), seasonal pricing, long-stay discounts |
| `l10n_si_farm_tourism` | `l10n_si_fiscal`, `l10n_si_sequence` | Custom | Sobe na kmetiji, domači izdelki (EKO/SMGT cert), kmečke aktivnosti, agroturizem |
| `l10n_si_tourist_tax` | `account`, `l10n_si` | Custom | Turistična taksa po občinah (ZTur-1), 12 SI municipalities preconfigured |
| `l10n_si_event_venue` | `l10n_si_fiscal`, `l10n_si_sequence` | Custom | Venue/hall rental for weddings, conferences, birthdays, galas; packages, catering, FURS |
| `l10n_si_event_accommodation` | `l10n_si_event_venue`, `l10n_si_hotel` | Custom | Block reservation of rooms for event guests (weddings, conferences) |
| `l10n_si_event_equipment_rental` | `l10n_si_event_venue` | Custom | Equipment rental (projectors, AV, stages, tables, chairs) with stock management |
| `l10n_si_event_photographer` | `l10n_si_event_venue` | Custom | External vendor booking (photographer, DJ, florist, decorator, MC) + vendor bills |
| `l10n_si_event_contract` | `l10n_si_event_venue`, `l10n_si_sign` | Custom | PDF contract generation with placeholder substitution + eIDAS signing |
| `l10n_si_wellness` | `l10n_si_fiscal`, `l10n_si_sequence` | Custom | Spa/wellness: massages, saunas, pools, day passes, therapist booking, FURS |
| `l10n_si_channel_manager` | `l10n_si_hotel`, `l10n_si_camping` | Custom | Sync with Booking.com/Airbnb/Expedia via API + webhook for reservations |
| `l10n_si_pos_advanced` | `point_of_sale`, `l10n_si_fiscal`, `l10n_si_hotel` | Custom | POS extensions: FURS on POS, room charge to folio, tourist tax, X/Z reports |
| `l10n_si_ai_concierge` | `l10n_si_knowledge`, `l10n_si_whatsapp` | Custom | AI guest assistant (Slovenian) for hotels: chat, WhatsApp, email, 24/7 |

### Tier 5 — Hotel operations, loyalty, executive, mobile

| Module | Depends on | Origin | Purpose |
|--------|-----------|--------|---------|
| `l10n_si_housekeeping` | `l10n_si_hotel`, `hr` | Custom | Housekeeping tasks, daily cron for room cleaning schedule, Lost & Found, materials usage |
| `l10n_si_maintenance_request` | `l10n_si_hotel`, `l10n_si_housekeeping`, `portal` | Custom | Guest portal for reporting issues (QR code in room → URL), SLA tracking, photo evidence |
| `l10n_si_dashboard_executive` | `l10n_si_hotel`, `l10n_si_restaurant`, `l10n_si_wellness` | Custom | Executive KPI dashboard: ADR, RevPAR, GopPAR, occupancy, YoY comparison |
| `l10n_si_loyalty_program` | `account`, `l10n_si_hotel` | Custom | Loyalty tiers (Bronze/Silver/Gold/Platinum), points accrual, rewards (4 pre-configured) |
| `l10n_si_group_booking` | `l10n_si_hotel`, `l10n_si_event_venue` | Custom | Group bookings for travel agencies/schools/teams, agency commission, rooming list, cut-off dates |
| `l10n_si_mobile_app` | `web`, `l10n_si_hotel`, `l10n_si_housekeeping`, `l10n_si_maintenance_request` | Custom | Progressive Web App (installable) for housekeeping, maintenance, reception staff |

### Tier 6 — Revenue, reviews, HR, procurement, budget, accounting

| Module | Depends on | Origin | Purpose |
|--------|-----------|--------|---------|
| `l10n_si_revenue_management` | `l10n_si_hotel`, `l10n_si_camping` | Custom | Dynamic pricing (yield management): seasonal/weekday/occupancy/last-minute/early-bird/LOS factors, rate calendar, 90-day forecast |
| `l10n_si_review_management` | `mail`, `l10n_si_hotel` | Custom | Booking.com/TripAdvisor/Google/Airbnb review aggregation, AI sentiment analysis, auto-response, webhook endpoints |
| `l10n_si_hr_roster` | `hr`, `hr_holidays`, `hr_attendance` | Custom | Shift scheduling (morning/afternoon/night/full), ZDR-1 compliance (11h rest, 40h/week), overtime, swap requests, calendar view |
| `l10n_si_procurement` | `purchase`, `stock`, `account` | Custom | Hotel procurement: 12 item categories (cleaning/cosmetics/linen/food/beverages), vendor ratings, annual contracts, reorder points |
| `l10n_si_budget_planning` | `account`, `analytic` | Custom | Annual budget by department (11 depts), 12-month breakdown, planned vs actual variance tracking, approval workflow |
| `l10n_si_accounting_advanced` | `account`, `l10n_si` | Custom | SRS reports (balance sheet, income statement, cash flow), financial ratios (ROA/ROE/ROS/liquidity/debt/activity), AJPES submission |

### Tier 7 — Guest services, payments, sustainability, GDPR

| Module | Depends on | Origin | Purpose |
|--------|-----------|--------|---------|
| `l10n_si_website_booking` | `website`, `l10n_si_hotel`, `l10n_si_camping`, `l10n_si_revenue_management` | Custom | Direct booking engine on website (/book), promo codes, dynamic rates, multi-step checkout, no OTA commission |
| `l10n_si_payment_gateway` | `account`, `payment` | Custom | 7 payment providers (Activa/Stripe/PayPal/UPN/TRR/cash/voucher), 3DS, refunds, payment links, webhook endpoints |
| `l10n_si_concierge_services` | `l10n_si_hotel` | Custom | Concierge desk: excursions, tickets, restaurant bookings, transport, medical, business services, auto-charge to folio |
| `l10n_si_transport` | `l10n_si_hotel`, `fleet` | Custom | Hotel shuttle, airport transfers, excursions, taxi, car rental, limousine; fleet integration |
| `l10n_si_sustainability` | `base`, `mail` | Custom | Green Key/EU Ecolabel/Travelife/EKO/ISO 14001 certificates, energy/water/waste/CO2 metrics, per-guest normalization |
| `l10n_si_data_protection` | `base`, `mail` | Custom | GDPR compliance: consent management (7 types), data subject requests (access/erasure/portability), 30-day deadline, IPP complaint, partner anonymization |

## Installation

```bash
# Already in the addons folder; just install from the Odoo Apps menu:
# Apps → Update Apps List → search for "Slovenian"

# Or via CLI:
./odoo-bin -d mydb -i l10n_si,l10n_si_vat_validation,l10n_si_sequence,l10n_si_fiscal,l10n_si_edi,l10n_si_bank_parser,l10n_si_reports --stop-after-init
```

## Configuration order

1. **`l10n_si_vat_validation`** — Company → SI VAT Validation tab → upload FURS .p12
2. **`l10n_si_sequence`** — Accounting → Configuration → Slovenian → Business Premises → register premise + devices
3. **`l10n_si_fiscal`** — Company → SI Fiscal Verification tab → enable + upload FURS cert + set environment
4. **`l10n_si_edi`** — Company → SI e-Račun tab → upload eIDAS cert + set PEPPOL ID
5. **`l10n_si_bank_parser`** — Accounting → Journals → Bank → set SI Bank Format
6. **`l10n_si_reports`** — Accounting → Reports → Slovenian Reports → generate per period

## Dependencies

Each module needs these additional Python packages on the server:

```bash
pip install qrcode requests xmlsec1
# xmlsec1 is a system package:
apt install xmlsec1  # Debian/Ubuntu
```

## Tests

Each module includes a tests/ directory. Run with:

```bash
./odoo-bin -d testdb -i l10n_si_vat_validation --test-enable --test-tags=/l10n_si_vat_validation --stop-after-init
```

## Legal

* **ZOI/EOR (l10n_si_fiscal)**: ZDavPR-1, UR. l. RS š. 89/16
* **e-Račun (l10n_si_edi)**: ZEfUP + EU Directive 2014/55/EU + EN 16931
* **REK-1 (l10n_si_reports)**: ZDDV-1, 81. člen
* **M4 (l10n_si_reports)**: ZDoh-2, 28. člen
* **AJPES SRS**: Pravilnik o vsebini in obliki računovodskih izkazov, UR. l. RS š. 60/06

## License

LGPL-3.0 — same as Odoo Community.
