# Production Deployment Checklist — SI/HR Odoo

## 🔒 Security
- [ ] Change `MASTER_PWD` in `odoo.conf`
- [ ] Change PostgreSQL password
- [ ] Set `db_filter = ^si_odoo$`
- [ ] Set `proxy_mode = True`
- [ ] Put behind nginx with HTTPS
- [ ] Enable HSTS in nginx
- [ ] Restrict `/web/database/*` endpoints
- [ ] 2FA enabled for admin user

## 🇸🇮 Slovenian compliance
### FURS
- [ ] Production FURS certificate obtained
- [ ] Certificate uploaded to company → Fiscal (SI) tab
- [ ] Environment set to PROD
- [ ] Business premises registered
- [ ] Electronic devices registered
- [ ] Test invoice posted — ZOI/EOR appear
- [ ] QR code visible on invoice PDF

### AJPES eTurizem
- [ ] Accommodation registered in RNO
- [ ] MID + SIFNAS received from AJPES
- [ ] SI-PASS credentials configured
- [ ] Test guest check-in → registration submitted
- [ ] Switch to PROD

### eDavki reports
- [ ] REK-1 generated for previous month
- [ ] M4 generated for previous month
- [ ] All 212 tourist tax rates verified

## 🇭🇷 Croatian compliance
### CISF (Fiskalizacija)
- [ ] FINA production certificate obtained (.pfx)
- [ ] Certificate uploaded to company → HR Fiskalizacija tab
- [ ] Business premises registered via CISF
- [ ] Test invoice posted → ZKI/JIR appear

### eVisitor
- [ ] Local turistička zajednica registration
- [ ] eVisitor credentials obtained
- [ ] HTZ ID assigned to each accommodation
- [ ] Test guest check-in

### PDV
- [ ] VAT rates configured (25%, 13%, 5%)
- [ ] First PDV report generated
- [ ] XML export verified

## 🗃️ Database & backups
- [ ] Daily backup cron configured
- [ ] Backup script tested
- [ ] 30-day retention set
- [ ] Off-site backup configured
- [ ] Test restore verified

## ⚡ Performance
- [ ] `workers = 4` minimum
- [ ] `limit_memory_soft = 1342177280`
- [ ] PostgreSQL `shared_buffers = 256MB`
- [ ] Nginx gzip enabled

## 📧 Email
- [ ] SMTP server configured
- [ ] Test email sent

## 👥 Users & access
- [ ] Admin password changed
- [ ] Receptionist group configured
- [ ] Multi-company rules active
- [ ] Audit trail enabled

## 📞 Support contacts
- FURS: +386 1 478 3000
- AJPES: +386 1 587 51 00
- Porezna uprava HR: +385 1 62 12 999
- FINA cert: +385 1 6165 444
- HTZ eVisitor: +385 1 48 96 333
