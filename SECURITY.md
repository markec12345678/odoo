# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email: support@sihr-tourism.si
3. Include: description, steps to reproduce, potential impact
4. You will receive a response within 48 hours

## Security Measures

### Deployment Security
- Odoo runs as non-root user (`odoo`)
- PostgreSQL connection is internal (Railway private network)
- No direct database access from internet
- HTTPS enforced by Railway reverse proxy

### FURS/CISF Certificate Handling
- Certificates stored as encrypted binary fields in `res.company`
- Certificate passwords never logged
- Certificate passwords encrypted at rest
- Multi-tenant: each company has its own certificate

### User Authentication
- 2FA (TOTP) supported via `auth_totp`
- Password policy via `auth_password_policy`
- Session timeout via `auth_timeout`
- Passkey support via `auth_passkey`

### Data Protection (GDPR)
- `l10n_si_data_protection` module for GDPR compliance
- Personal data encryption at rest
- Data export functionality
- Right to be forgotten (data deletion)

### Backup Security
- Daily PostgreSQL dump (03:00 UTC)
- Optional S3-compatible offsite storage (Backblaze B2, R2)
- 30-day retention policy
- Backup encryption recommended

## Security Checklist for Production

- [ ] Change admin password (default: admin/admin)
- [ ] Enable 2FA for all admin users
- [ ] Configure offsite backup (S3/B2)
- [ ] Set custom domain with SSL
- [ ] Review and minimize user permissions
- [ ] Enable audit trail module
- [ ] Configure FURS PROD certificate
- [ ] Set up monitoring/alerting
- [ ] Regular security updates (Odoo core + modules)
- [ ] Review PostgreSQL access logs
