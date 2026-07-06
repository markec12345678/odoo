# Railway.com Deployment — SI/HR Odoo 19

**Najenostavnejši način za zagon Odoo v oblaku — brez bančne kartice, brez SSH, brez lokalnega Dockerja.**

## 📋 Prednosti Railway

| Feature | Railway | Oracle Cloud | Hugging Face |
|---------|---------|-------------|-------------|
| Brez kartice | ✅ | ❌ | ✅ |
| Vgrajen PostgreSQL | ✅ (1 klik) | ❌ (ročno) | ❌ |
| Auto-deploy iz GitHub | ✅ | ❌ | ✅ |
| Web URL | ✅ `app.railway.app` | ✅ (IP) | ✅ `.hf.space` |
| Brez auto-sleep | ✅ | ✅ | ❌ (48h) |
| FURS certifikati | ✅ | ✅ | ⚠️ |
| RAM | 512 MB–8 GB | 24 GB | 16 GB |
| Brezplačno | $5/mesec kredita | trajno | trajno |

## 🚀 Namestitev (5 minut)

### 1. Railway projekt je že ustvarjen ✅
Imaš: `https://railway.com/project/d4fff35a-43b3-46d8-b066-dab7ff2ef17d`

### 2. Dodaj PostgreSQL na Railway

1. Odpri svoj Railway projekt
2. Click **+ New → Database → PostgreSQL**
3. Railway samodejno ustvari `DATABASE_URL` spremenljivko
4. Kopiraj `DATABASE_URL` iz Variables tab

### 3. Dodaj Odoo kot Docker service

1. Click **+ New → GitHub Repository**
2. Izberi `markec12345678/odoo`
3. Railway samodejno zazna `Dockerfile.railway`
4. Pojdi na **Variables** tab za ta service in dodaj:
   ```
   DATABASE_URL = (prilepi iz PostgreSQL service)
   PORT = 8080
   MASTER_PWD = (izberi geslo)
   ```

### 4. Nastavi custom domain (opcijsko)

1. Settings → Networking → Generate Domain
2. Dobiš URL: `si-hr-odoo-production.up.railway.app`

### 5. Počakaj da se build-a

Railway bo:
1. Kloniral GitHub repo
2. Zagnal `Dockerfile.railway`
3. Povezal z PostgreSQL
4. Na koncu natisnil URL

### 6. Dostop

Odoo bo dosegliv na:
```
https://si-hr-odoo-production.up.railway.app
```

**Master password**: tisto kar si nastavil v `MASTER_PWD`

## 🔧 Namestitev modulov

Ko Odoo prvič zaženeš:

1. Odpri URL → ustvari bazo `si_odoo`
2. Pojdi na **Apps → Update Apps List**
3. Namesti module po vrsti:
   - `l10n_si` (osnova)
   - `l10n_si_fiscal` (FURS)
   - `l10n_si_hotel` (hotel)
   - `l10n_si_etourism` (AJPES)
   - `l10n_hr_fiscal` (CISF)

## 🔄 Auto-deploy

Railway samodejno deploy-a vsakič ko pushaš na `19.0` branch:
```bash
git push origin 19.0
→ Railway zazna push
→ Build Docker image
→ Restart service z novo kodo
```

## ⚠️ Omejitve Railway free tier

- **$5 kredita/mesec** — zadostuje za majhen Odoo (512 MB RAM)
- **PostgreSQL** — 1 GB brezplačno
- **Brez SSL za FURS** — Railway ima HTTPS, FURS certifikat moraš naložiti ročno v Odoo

## 💰 Priporočilo za ceno

| Načrt | RAM | Cena | Primerno za |
|-------|-----|------|-------------|
| Free | 512 MB | $5/mes | Demo, testiranje |
| Hobby | 8 GB | $5/mes | ✅ **Priporočeno** — 75 modulov, POS, hotel |
| Pro | 32 GB | $20/mes | Produkcija z več uporabniki |

## 🆘 Reševanje težav

### Odoo se ne zažene
```bash
# Preveri logs na Railway dashboard
# Settings → Logs
```

### PostgreSQL connection failed
```bash
# Preveri da je DATABASE_URL pravilno nastavljen
# Morajo biti: postgresql://user:pass@host:port/dbname
```

### Moduli se ne vidijo
```bash
# 1. Apps → Update Apps List
# 2. Odstrani filter "Apps" → prikaži vse
# 3. Išči "l10n_si" ali "l10n_hr"
```
