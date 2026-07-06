# Slovenian eTurizem (AJPES Guest Registration) — l10n_si_etourism

**Odoo 19 module for mandatory AJPES guest registration per ZPPreb-1**

## Status

**Phase 1+2 (data model + SOAP client + hotel/camping hooks): COMPLETE ✅**

## Legal requirement

Every Slovenian accommodation provider MUST register each guest with AJPES
eTurizem within 24h of check-in per ZPPreb-1 (UR. l. RS š. 81/16).

Penalty: 500–4.000 EUR per unregistered guest.

## AJPES SOAP API

- **Endpoint:** `https://www.ajpes.si/wsrno/eTurizem/wsETurizemPorocanje.asmx`
- **Operation:** `oddajPorocilo(uName, pwd, data, format)`
- **Auth:** SI-PASS username/password (issued by AJPES after RNO registration)

## ZOI vs ZKI comparison

| Aspect | SI (FURS) | HR (CISF) |
|--------|-----------|-----------|
| Signature | ZOI (MD5) | ZKI (MD5) |
| Tax ID | VAT (8 digits) | OIB (11 digits) |
| Date format | ISO 8601 | dd.MM.yyyyHH:mm:ss |

## Configuration

1. Register accommodation in RNO (AJPES)
2. Receive MID + SIFNAS
3. Get SI-PASS credentials
4. Odoo → SI eTurizem → Nastanitveni obrati → Create with MID/SIFNAS
5. Hotel/camping check-in → auto-registration

## Integration

- `l10n_si_hotel.reservation.action_check_in` → auto-register
- `l10n_si_hotel.reservation.action_check_out` → auto-deregister
- `l10n_si_camping.reservation.action_check_in` → auto-register
- `l10n_si_camping.reservation.action_check_out` → auto-deregister
- Cron retry every 15 minutes for pending/failed submissions
