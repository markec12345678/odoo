# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 19.0.x  | ✅ Active development |
| < 19.0  | ❌ Not supported     |

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email: security@example.com (replace with real email)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Affected module(s)
   - Potential impact

We will respond within 48 hours and provide a fix timeline.

## Security Measures

### Certificates
- FURS (.p12), FINA (.pfx), and eIDAS certificates are **never committed** to the repository
- `.gitignore` blocks all certificate file types: `*.p12`, `*.pfx`, `*.pem`, `*.key`, `*.crt`
- Certificates are stored encrypted in the Odoo database (Binary fields)

### API Keys
- All API keys (ZAI, OpenAI, Anthropic, Booking.com, Airbnb) are stored as `Char` fields with `password="True"` widget
- Keys are never logged in plain text
- `copy=False` prevents accidental duplication

### Personal Data (GDPR / ZVOP-1)
- Guest personal data (AJPES eTurizem, eVisitor) is retained for 5 years per ZPPreb-1
- `l10n_si_data_protection` module manages GDPR consent and data subject requests
- `l10n_si_audit_trail` logs all changes to sensitive fields

### Network Security
- All API calls use HTTPS with certificate verification (`verify=True`)
- FURS uses mutual TLS (mTLS) with client certificate
- CISF uses FINA-issued .pfx with mTLS
- No plain HTTP endpoints are used

### Authentication
- SI-PASS credentials for AJPES eTurizem (per-establishment)
- FINA certificate for CISF Fiskalizacija
- eIDAS qualified certificate for e-Račun (eSLOG 2.0)
- OAuth2 Bearer token for Airbnb
- HTTP Basic Auth for Booking.com

## Compliance

| Regulation | Module(s) | Status |
|-----------|-----------|--------|
| ZDavPR-1 (FURS) | l10n_si_fiscal | ✅ ZOI/EOR + QR code |
| ZPPreb-1 (AJPES) | l10n_si_etourism | ✅ Guest registration |
| ZTur-1 (tourist tax) | l10n_si_tourist_tax | ✅ 212 municipalities |
| GDPR / ZVOP-1 | l10n_si_data_protection | ✅ Consent + DSR |
| Zakon o fiskalizaciji (HR) | l10n_hr_fiscal | ✅ ZKI/JIR + QR |
| Zakon o boravišnoj pristojbi | l10n_hr_evisitor | ✅ Guest registration |
| Zakon o PDV (HR) | l10n_hr_pdv | ✅ VAT reporting |
