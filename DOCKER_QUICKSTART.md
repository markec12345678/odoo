# Quick start — Slovenian/Croatian Odoo 19 with Docker

## Prerequisites
- Docker Engine 24+, Docker Compose v2+
- 4 GB RAM minimum (8 GB recommended)

## Steps

### 1. Start the stack
```bash
docker compose up -d
```

### 2. Create the database
Open http://localhost:8069
- **Master password:** `admin`
- **Database name:** `si_odoo`
- **Language:** Slovenian / Slovenia
- **Country:** Slovenia

### 3. Install modules
Go to **Apps → Update Apps List**, then install:
1. `l10n_si` — Slovenian chart of accounts
2. `l10n_si_fiscal` — FURS ZOI/EOR
3. `l10n_si_hotel` — Hotel PMS
4. `l10n_si_restaurant` — Restaurant management
5. `l10n_si_etourism` — AJPES guest registration
6. `l10n_hr_fiscal` — Croatian CISF (if needed)

### 4. Configure FURS
1. Get a free FURS test cert from https://blagajne-test.fu.gov.si/
2. Save as `certs/furs_test.p12`
3. Settings → Companies → [company] → Fiscal (SI) tab → Upload .p12
4. Set environment: TEST

### 5. Test a FURS invoice
1. Create a business premise (BL1) + electronic device (RECEP1)
2. Create a test partner → invoice → Post → verify ZOI/EOR

## Common commands
```bash
docker compose logs -f odoo
docker compose restart odoo
docker compose down
docker compose exec odoo odoo --database=si_odoo --update=l10n_si_hotel --stop-after-init
```

## Backups
```bash
docker compose exec db pg_dump -U odoo si_odoo > backup.sql
```
