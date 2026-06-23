# Changelog

All notable changes to the custom `l10n_si_*` modules are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [19.0.8.0] — 2026-06-23

### Added — Tier 8: Accounting, audit & hotel operations (15 modules)

- **l10n_si_assets** — Fixed assets with SI depreciation (linear/declining per ZDD-1), 4 pre-configured categories (IT/furniture/buildings/vehicles), monthly depreciation cron.
- **l10n_si_intrastat** — Monthly Intrastat report for EU trade (arrivals + dispatches), auto-compute from invoices, commodity codes, transport modes.
- **l10n_si_vies_return** — Monthly VIES (PP ODS) for EU B2B VAT, auto-compute from out_invoices to EU partners.
- **l10n_si_year_end_close** — Year-end closing per SRS (accounts 990, 999), compute net profit, create closing journal entry.
- **l10n_si_audit_trail** — Audit trail for sensitive field changes (prices, VAT, ZOI/EOR), automatic logging via base.write() override.
- **l10n_si_gift_voucher** — Gift vouchers: sell, redeem (full/partial), track balance, expiry dates.
- **l10n_si_minibar** — Hotel minibar: item catalog, consumption tracking, auto-charge to folio.
- **l10n_si_laundry** — Laundry service: guest + internal, express (1.5x), auto-charge to folio.
- **l10n_si_partner_portal** — Guest portal: view stays, loyalty points, submit maintenance requests.
- **l10n_si_multi_company** — Hotel chain management: central reservation, shared vendors, multi-company.
- **l10n_si_weather_integration** — 14-day weather forecast (open-meteo.com API), occupancy impact, rate adjustment recommendations.
- **l10n_si_competitor_pricing** — Competitor price tracking, position analysis (cheapest/most expensive), recommendations.
- **l10n_si_accessibility** — Accessibility features for disabled guests: wheelchair access, elevators, accessible bathrooms, visual alarms.
- **l10n_si_kitchen_display** — Kitchen Display System (KDS): digital screen replacing paper tickets, overdue alerts, prep time tracking.
- **l10n_si_pets** — Pet management: species, breed, vaccination records, pet fees, room type pet policies.

## [19.0.7.0] — 2026-06-23

### Added — Tier 7: Guest services & compliance (6 modules)

- **l10n_si_website_booking** — Direct booking engine on website (`/book`). Search by dates, dynamic rates from revenue management, promo codes (2 pre-configured: EARLYBIRD10, LASTMINUTE15), multi-step checkout, auto-creates partner + reservation.
- **l10n_si_payment_gateway** — 7 payment providers (Activa/Stripe/PayPal/UPN/TRR/cash/voucher), 3D Secure, refund workflow, payment links, webhook endpoints, auto-reconciliation with invoices.
- **l10n_si_concierge_services** — Concierge desk: 8 request types (excursions, tickets, restaurant, transport, spa, shopping, medical, business), auto-charge to hotel folio.
- **l10n_si_transport** — Hotel shuttle, airport transfers, excursions, taxi, car rental, limousine. Fleet integration, driver assignment, auto-charge to folio.
- **l10n_si_sustainability** — Green Key/EU Ecolabel/Travelife/EKO/ISO 14001 certificates. 9 metric types (electricity/gas/water/oil/waste/CO2/guests), per-guest normalization.
- **l10n_si_data_protection** — GDPR compliance: 7 consent types, data subject requests (access/erasure/portability/objection), 30-day deadline tracking, auto-anonymization on erasure.

## [19.0.6.0] — 2026-06-22

### Added — Tier 6: Finance & HR (6 modules)

- **l10n_si_revenue_management** — Dynamic pricing (yield management): 6 pricing factor groups (seasonal/weekday/occupancy/last-minute/early-bird/LOS), 90-day rate calendar, occupancy forecast.
- **l10n_si_review_management** — Booking.com/TripAdvisor/Google/Airbnb review aggregation, AI sentiment analysis (5 levels), auto-categorization (7 categories), auto-response generation, webhook endpoints.
- **l10n_si_hr_roster** — Shift scheduling per ZDR-1: 4 default shifts, min 11h rest, max 40h/week, overtime detection, swap requests, night/weekend/holiday premiums.
- **l10n_si_procurement** — Hotel procurement: 12 item categories, vendor ratings (5-level), annual contracts with value tracking, reorder points, seasonal demand multipliers.
- **l10n_si_budget_planning** — Annual budget by 11 departments, 12-month breakdown, planned vs actual variance, approval workflow (draft → submitted → approved → active → closed).
- **l10n_si_accounting_advanced** — SRS reports (balance sheet, income statement, cash flow, capital changes, VAT return), 13 financial ratios (ROA/ROE/ROS/liquidity/debt/activity), AJPES submission workflow.

## [19.0.5.0] — 2026-06-22

### Added — Tier 5: Operations & mobile (6 modules)

- **l10n_si_housekeeping** — Daily cron at 6:00 generates cleaning tasks, Lost & Found (8 categories), materials usage tracking, housekeeper stats.
- **l10n_si_maintenance_request** — Guest portal for reporting issues (QR code in room → URL), SLA tracking (1h/4h/24h/7d), photo evidence, 8 categories.
- **l10n_si_dashboard_executive** — KPI dashboard: ADR, RevPAR, GopPAR, occupancy %, revenue by segment, YoY comparison.
- **l10n_si_loyalty_program** — 4 tiers (Bronze/Silver/Gold/Platinum), points accrual, 4 pre-configured rewards (free night/breakfast/massage/upgrade).
- **l10n_si_group_booking** — Group reservations for agencies/schools/teams, agency commission, rooming list, cut-off dates, free leader room every N guests.
- **l10n_si_mobile_app** — Progressive Web App (installable) for housekeeping, maintenance, reception staff. Calendar view, one-click check-in/out.

## [19.0.4.0] — 2026-06-22

### Added — Tier 4-5: Tourism vertical + advanced tourism (14 modules)

- **l10n_si_hotel** — Hotel PMS: rooms, reservations, folio, check-in/out, FURS ZOI/EOR. Ported from OCA/vertical-hotel 17.0.
- **l10n_si_restaurant** — Menus with 14 EU allergens (EU 1169/2011), tables, KOT (kitchen order tickets), FURS.
- **l10n_si_camping** — Campsite parcels (tent/RV/cabin/glamping), 5 seasonal pricing periods, long-stay discounts.
- **l10n_si_farm_tourism** — Sobe na kmetiji, domači izdelki (EKO/SMGT cert), 5 pre-configured kmečke aktivnosti.
- **l10n_si_tourist_tax** — Turistična taksa per ZTur-1, 12 SI municipalities pre-configured with real rates.
- **l10n_si_event_venue** — Venue/hall rental for weddings, conferences, birthdays. 5 pre-configured packages. Calendar view.
- **l10n_si_event_accommodation** — Block reservation of rooms for event guests, special event price, release date.
- **l10n_si_event_equipment_rental** — Equipment rental (projectors, AV, stages, tables), stock management, conflict detection, technician.
- **l10n_si_event_photographer** — External vendor booking (photographer, DJ, florist, decorator, MC), vendor bills.
- **l10n_si_event_contract** — PDF contract generation with placeholder substitution, eIDAS signing via l10n_si_sign.
- **l10n_si_wellness** — Spa: massages, saunas, pools, day passes, therapist booking, per-category pricing (adult/child/senior/student).
- **l10n_si_channel_manager** — Sync with Booking.com/Airbnb/Expedia, 15-minute cron, webhook endpoints, room type mapping.
- **l10n_si_pos_advanced** — POS extensions: FURS on POS, room charge to folio, tourist tax, X/Z reports.
- **l10n_si_ai_concierge** — AI guest assistant in Slovenian, 24/7, multi-channel (website/WhatsApp/email), knowledge base integration.

## [19.0.3.0] — 2026-06-21

### Added — Tier 3: Business operations (11 modules)

- **l10n_si_approvals** — Multi-step approval workflows, rule-based routing, SLA escalation, delegation.
- **l10n_si_knowledge** — Internal wiki, document templates, version history, visibility levels.
- **l10n_si_customer_statements** — Monthly statements with aging buckets (0-30/31-60/61-90/90+).
- **l10n_si_subscription_advanced** — Recurring billing, trial periods, commitment, auto-invoicing.
- **l10n_si_field_service** — Work orders, dispatching, customer signature, photo evidence, auto-invoice.
- **l10n_si_maintenance_advanced** — Preventive schedules, MTBF/MTTR, spare parts, downtime analysis.
- **l10n_si_quality_control** — Inspection checklists, NCR (non-conformance), CAPA, ISO 9001 audit trail.
- **l10n_si_timesheet_approval** — Weekly approval workflow, line locking, auto-reminders.
- **l10n_si_ocr_invoice** — OCR scan supplier invoices (Tesseract/Google DocAI/AWS Textract), SI regex patterns.
- **l10n_si_marketing_automation** — Multi-step email campaigns, branching, triggers, A/B testing.
- **l10n_si_whatsapp** — WhatsApp Cloud API + Twilio, templates, GDPR opt-in/out, webhook for incoming.

## [19.0.2.0] — 2026-06-21

### Added — Tier 2: Enterprise replacement (5 modules)

- **l10n_si_hr_payroll_community** — Slovenian payroll: ZDoh-2, ZPrD, all olajšave, M4 auto-generation, payslip PDF.
- **l10n_si_sign** — eIDAS digital signing (SI-TRUST/CA HALCOM), PAdES/XAdES, RFC 3161 timestamp.
- **l10n_si_bank_sync** — Auto-fetch daily statements from NLB/NKBM/Sparkasse/Addiko/Raiffeisen.
- **l10n_si_helpdesk_simple** — Customer ticket system, 5-stage kanban, SLA tracking, customer portal, canned responses.
- **l10n_si_fleet** — SI-specific: tehnični pregled, zavarovanje, registracija, vozni listi, gorivo, servisi.

## [19.0.1.0] — 2026-06-20

### Added — Tier 1: Regulatory compliance (6 modules)

- **l10n_si_vat_validation** — MOD11 checksum validation for SI VAT numbers + optional FURS VIES lookup.
- **l10n_si_sequence** — Invoice numbering per poslovni prostor (BL1-KASA1-2025-00001), yearly auto-renewal cron.
- **l10n_si_fiscal** — FURS davčno potrjevanje: ZOI generation (MD5), EOR submission via REST API with mTLS, QR code on invoice PDF, retry cron for 48h compliance window (ZDavPR-1).
- **l10n_si_edi** — FURS e-Račun eSLOG 2.0 XML generation, eIDAS qualified signing, submission to eDavki portal, acceptance polling.
- **l10n_si_bank_parser** — ISO 20022 CAMT.053 + MT940 parser for NLB, NKBM, Sparkasse, Addiko, Raiffeisen, A1, Hypo. SI-specific quirks (PRILIV/ODLIV prefixes, double-space normalization).
- **l10n_si_reports** — AJPES SRS (annual), REK-1 (monthly B2B buyers), M4 (monthly payroll tax) XML exports for eDavki.

### Project infrastructure

- Comprehensive README.md with full module catalog
- Deployment scripts (setup.sh, odoo.conf, nginx.conf, backup.sh)
- FURS registration checklist (4-week process)
- OCA Slovenian modules guide

---

## Version History Summary

| Version | Date | Modules Added | Cumulative Total |
|---------|------|---------------|------------------|
| 19.0.1.0 | 2026-06-20 | 6 (Tier 1) | 6 |
| 19.0.2.0 | 2026-06-21 | 5 (Tier 2) | 11 |
| 19.0.3.0 | 2026-06-21 | 11 (Tier 3) | 22 |
| 19.0.4.0 | 2026-06-22 | 14 (Tier 4-5) | 36 |
| 19.0.5.0 | 2026-06-22 | 6 (Tier 5b) | 42 |
| 19.0.6.0 | 2026-06-22 | 6 (Tier 6) | 48 |
| 19.0.7.0 | 2026-06-23 | 6 (Tier 7) | 54 |
| 19.0.8.0 | 2026-06-23 | 15 (Tier 8) | 69 |
| + l10n_si | upstream | 1 (chart of accounts) | **70** |
