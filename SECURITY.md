# Security Policy

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| 19.0 | Active development | Custom `l10n_si_*` modules |
| 18.0 | Not supported in this fork | Upgrade to 19.0 |
| 17.0 | Not supported in this fork | Upgrade to 19.0 |
| <= 16.0 | Not supported | Not supported by upstream Odoo either |

## Reporting a Vulnerability

**Do NOT open public GitHub issues for security vulnerabilities.**

### How to report

1. Go to: https://github.com/markec12345678/odoo/security/advisories/new
2. Click **"Report a vulnerability"**
3. Include:
   - Detailed description of the vulnerability
   - Steps to reproduce
   - Proof-of-concept script (preferred over screenshots)
   - Affected module(s) and version(s)
   - Suggested fix (if any)
   - Your contact information (for follow-up)

### Response timeline

| Step | Timeline |
|------|----------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 5 business days |
| Fix or mitigation | Within 30 days (critical: 7 days) |
| Public disclosure | After fix is released (90 days max) |

### What qualifies

| Report | Accepted |
|--------|----------|
| SQL injection in custom modules | Yes |
| XSS in custom views/templates | Yes |
| FURS API credential exposure | Yes |
| Missing ACL on custom models | Yes |
| GDPR violation in data handling | Yes |
| Upstream Odoo bugs | No — report to Odoo S.A. |
| Configuration errors | No — see documentation |
| Missing HTTPS | No — deployment responsibility |

## Security Best Practices

### For developers

1. **Never commit secrets** — API keys, passwords, `.p12` certificates, tokens
2. **Use `ir.config_parameter`** for runtime secrets with restricted access
3. **Always add `ir.model.access.csv`** — no model without explicit ACLs
4. **Use `groups=` on sensitive fields** — restrict visibility
5. **Validate all user input** — use `@api.constrains` for field validation
6. **Escape XML** — use `&amp;` `&lt;` `&gt;` in XML attributes
7. **Use parameterized queries** — never string-concat SQL
8. **Audit FURS submissions** — log every API call with request/response

### For administrators

1. **Set `admin_passwd`** to a strong random string (32+ chars)
2. **Set `list_db = False`** in `odoo.conf` to hide database manager
3. **Set `dbfilter = ^your_db$`** to prevent cross-database access
4. **Use Nginx** with HTTPS (Let's Encrypt) — never expose port 8069 directly
5. **Run as non-root user** — `odoo:odoo` system user
6. **Enable `proxy_mode = True`** so Odoo trusts X-Forwarded headers
7. **Restrict PostgreSQL** to `127.0.0.1` or private network
8. **Daily backups** with offsite copy (test restore quarterly)
9. **Revoke exposed tokens** immediately — classic `ghp_` tokens are dangerous
10. **Use fine-grained GitHub tokens** with `Contents: Write` only, 7-day expiry

### For FURS compliance

- **ZOI/EOR must be obtained within 48 hours** of issuing a cash invoice (ZDavPR-1)
- **FURS certificate (.p12)** must be stored securely — not in the repository
- **FURS test environment** must be used before production go-live
- **All FURS API calls** must be logged for audit (10-year retention)
- **Penalty for non-compliance**: 200 € – 125,000 € (ZDavPR-1, 35. člen)

### For GDPR compliance

- **Consent must be obtained** before processing personal data for marketing
- **Data subject requests** (access/erasure/portability) must be answered within 30 days
- **Data retention** must follow legal minimums (10 years for accounting, 5 years for HR)
- **Right to erasure** does not override accounting retention requirements
- **Cross-border transfers** must comply with GDPR Chapter V

## Security Audit Checklist

- [ ] `admin_passwd` set to strong random string
- [ ] `list_db = False` in `odoo.conf`
- [ ] `dbfilter` set to specific database
- [ ] Nginx HTTPS with TLS 1.2+ configured
- [ ] Odoo runs as non-root user
- [ ] PostgreSQL restricted to localhost
- [ ] Daily backup running (verify restore)
- [ ] FURS certificate stored securely (not in repo)
- [ ] eIDAS certificate stored securely (not in repo)
- [ ] Bank API credentials stored securely (not in repo)
- [ ] All `ir.model.access.csv` files reviewed
- [ ] No hardcoded passwords in any `.py` file
- [ ] No API keys in any committed file
- [ ] GitHub token revoked if ever exposed
- [ ] `ir.config_parameter` used for runtime secrets
- [ ] GDPR consent management configured
- [ ] FURS test environment validated before production
