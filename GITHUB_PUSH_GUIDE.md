# GitHub Push Guide — SI/HR Odoo 19 Localization

## 📊 Trenutno stanje

| Metrika | GitHub (trenutno) | Lokalno (pripravljeno) |
|---------|-------------------|------------------------|
| Commit | `353168e9` | `51376498` |
| SI moduli | 70 | 70 |
| HR moduli | 0 | 5 |
| Skupaj moduli | 70 | **75** |
| Testi | 0 | **74** (52 unit + 22 E2E) |
| CI jobs | 5 | **8** (+unit, +e2e, +hr-count) |

## 🚀 Push navodila

Na vašem računalniku (kjer imate GitHub dostop):

### Opcija A: Če že imate klonirano

```bash
cd /path/to/your/odoo
git fetch origin
git pull origin 19.0
git log --oneline -3  # mora videti f926633c
```

### Opcija B: Klonirajte na novo

```bash
git clone git@github.com:markec12345678/odoo.git
cd odoo
git checkout 19.0
```

### Opcija C: Push iz tega okolja (če boste dodali SSH key)

```bash
cd /home/z/my-project/repos/odoo
git push origin 19.0
```

## 📝 Kaj je v 2 novih commitih

### Commit 1: `2c04087a`
- `l10n_hr_fiscal` — CISF Fiskalizacija (ZKI/JIR + FINA mTLS)
- `l10n_si_etourism` — AJPES eTurizem (prijava gostov)
- CI test runnerji (unit + E2E)
- README posodobitev (SI vs HR primerjava)

### Commit 2: `51376498`
- `l10n_hr_evisitor` — HTZ eVisitor REST API
- `l10n_hr_pdv` — PDV (VAT) reporting + ePorezna XML
- AI Concierge LLM klient (ZAI/OpenAI/Anthropic/Local)
- Channel Manager API klienti (Booking.com + Airbnb)
- POS X/Z report wizard
- Revenue Management cron jobs
- SRS konti (41 kontov) + Bilanca/Izid PDF
- eDavki XML generatorji (REK-1, M4)
- 13 test files (fiscal, hotel, restaurant, KDS, POS, revenue)
- Demo podatki (hotel, restaurant, camping)
- Docker setup (docker-compose.yml + odoo.conf)
- Backup/restore skripte
- Production checklist
- Priročnik za receptorico
- .gitignore za certifikate

## ✅ Po push-u preverite

1. **CI Actions**: https://github.com/markec12345678/odoo/actions
   - Vsi 8 job-i morajo biti zeleni
2. **Repo info**: Settings → Description = "Odoo 19 SI+HR localization for hospitality & tourism"
3. **Topics**: `odoo`, `slovenia`, `croatia`, `furs`, `ajpes`, `cisf`, `evisitor`, `hospitality`
4. **Branch protection**: Settings → Branches → 19.0 → Require status checks

## 🏷️ GitHub Release (opcijsko)

```bash
git tag -a v19.0.2.0 -m "SI+HR localization: 75 modules, 74 tests"
git push origin v19.0.2.0
```

Nato na GitHub: Releases → Draft new release → Tag: v19.0.2.0
