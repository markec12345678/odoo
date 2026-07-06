# Hugging Face Spaces Deployment

Namesto lokalnega Dockerja lahko Odoo zaženeš na Hugging Face Spaces — brezplačno, dostopno preko spleta.

## 📋 Prednosti vs. Docker lokalno

| Feature | Docker (lokalno) | HF Spaces |
|---------|-------------------|-----------|
| Dostop | samo localhost | ✅ spletni URL |
| Namestitev | `docker compose up` | avtomatsko (GitHub push) |
| PostgreSQL | vgrajen | zunanji (Supabase/Neon) |
| Cena | brezplačno | brezplačno (free tier) |
| RAM | neomejeno | 16 GB |
| Auto-sleep | ne | po 48h neaktivnosti |
| Produkcija | ✅ primerno | ⚠️ samo demo/preview |

## 🚀 Nastavitev (5 minut)

### 1. Ustvari zunanjo PostgreSQL bazo (brezplačno)

**Opcija A: Supabase** (priporočeno)
1. Pojdi na https://supabase.com → Sign up
2. Create new project
3. Settings → Database → Connection string
4. Kopiraj `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`

**Opcija B: Neon**
1. Pojdi na https://neon.tech → Sign up
2. Create project
3. Kopiraj connection string

### 2. Ustvari Hugging Face Space

1. Pojdi na https://huggingface.co/new-space
2. **Owner**: markec12345678
3. **Name**: si-hr-odoo
4. **SDK**: Docker
5. **Visibility**: Public (ali Private)
6. Click **Create Space**

### 3. Nastavi Secrets na HF Space

Pojdi na: `https://huggingface.co/spaces/markec12345678/si-hr-odoo/settings`

Add **Variables and secrets**:
```
DATABASE_URL = postgresql://postgres:YOUR_PASS@db.YOUR_PROJECT.supabase.co:5432/postgres
MASTER_PWD = your_admin_password
```

### 4. Nastavi GitHub Secret za avtomatski deploy

```bash
# Na GitHubu:
# Settings → Secrets and variables → Actions → New repository secret
# Name: HF_TOKEN
# Value: (your Hugging Face token from https://huggingface.co/settings/tokens)
```

⚠️ **Po nastavitvi razveljavi token na https://huggingface.co/settings/tokens** in ustvari novega.

### 5. Push na GitHub → avtomatski deploy

```bash
git push origin 19.0
```

GitHub Action bo:
1. Zagnal teste (unit + E2E)
2. Pripravil Dockerfile za HF
3. Pushal na Hugging Face Spaces
4. Space se bo samodejno zagnal

### 6. Dostop

Po ~5 minutah bo Odoo dosegliv na:
```
https://markec12345678-si-hr-odoo.hf.space
```

## ⚠️ Omejitve HF Spaces

1. **Auto-sleep**: Po 48h neaktivnosti Space gre v sleep. Prvi obisk ga zbudi (~30s).
2. **16 GB RAM**: Dovolj za Odoo z 2 workers, ne za velike instalacije.
3. **Persistent storage**: `/data` — omejeno na 20 GB (free tier).
4. **Brez SSL certifikata za FURS**: FURS/CISF certifikati so v `/data/certs/` — moraš ročno naložiti po vsakem restartu.
5. **Ni primerno za produkcijo**: Uporabi za demo/preview/testiranje.

## 🔄 Lokalni Docker (alternativa)

Če ženeš lokalno:
```bash
docker compose up -d
# Dostop: http://localhost:8069
```

## 📊 Priporočilo

| Namena | Priporočeno |
|--------|-------------|
| Demo/preview | ✅ HF Spaces |
| Razvoj | ✅ Lokalni Docker |
| Produkcija | ✅ VPS (Hetzner/DigitalOcean) + Docker |
| FURS/AJPES testi | ✅ Lokalni Docker (potreben certifikat) |
