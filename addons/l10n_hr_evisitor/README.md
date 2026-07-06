# Croatian eVisitor (Tourist Guest Registration) — l10n_hr_evisitor

**Odoo 19 module for Croatian tourist guest registration per Zakon o boravišnoj pristojbi**

## Status

**Phase 1 (data model + REST client + views): COMPLETE ✅**

## Legal requirement

Every Croatian accommodation provider MUST register each guest with eVisitor
within 24h of arrival. Penalty: 500–5.000 kn per unregistered guest.

## eVisitor API

- **Base URL (PROD):** `https://www.evisitor.hr/eVisitorRhetos_API/Rest/`
- **Base URL (TEST):** `https://www.evisitor.hr/eVisitorRhetos_API/Rest/_test/`
- **Auth:** HTTP Basic Auth (username/password from local TZ)

## Configuration

1. Register with local turistička zajednica
2. Receive eVisitor username + password
3. Configure each accommodation with HTZ ID
4. Check-in guest → auto-registration via REST API
5. Check-out guest → auto-deregistration

## Tourist tax (boravišna pristojba)

- Per accommodation: adult/youth/child rates
- Auto-calculated on check-out
- Reported to local TZ via eVisitor
