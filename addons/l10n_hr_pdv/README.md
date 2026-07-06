# Croatia — PDV Reporting (ePorezna)

**Module:** `l10n_hr_pdv`
**Author:** markec12345678
**License:** LGPL-3
**Version:** 19.0.1.0.0
**Countries:** `hr`

Croatian VAT (PDV) periodic reporting module: monthly or quarterly PDV
report (PDV obrazac), Knjiga PDV-a (VAT ledger) and ePorezna XML export
ready for upload to the Porezna uprava ePorezna portal.

---

## Sadržaj / Table of Contents

- [Značajke / Features](#značajke--features)
- [Instalacija / Installation](#instalacija--installation)
- [Konfiguracija / Configuration](#konfiguracija--configuration)
- [Korištenje / Usage](#korištenje--usage)
- [PDV stope / VAT rates](#pdv-stope--vat-rates)
- [EU države / EU country codes](#eu-države--eu-country-codes)
- [ePorezna XML format](#eporezna-xml-format)
- [Rokovi predaje / Deadlines](#rolovi-predaje--deadlines)
- [Cron automatizacija / Cron automation](#cron-automatizacija--cron-automation)
- [Tehničke napomene / Technical notes](#tehničke-napomene--technical-notes)
- [Reference](#reference)

---

## Značajke / Features

* **PDV izvještaj** (`l10n_hr.pdv.report`) — mjesečno ili kvartalno
  izvješće po tvrtki, s razradom PDV-a po stopama (25% / 13% / 5%).
* **Knjiga PDV-a** — detaljne stavke po dokumentu
  (`l10n_hr.pdv.report.line`) i za izlazni i za ulazni PDV.
* **PDV obrazac** — PDF ispis (QWeb) koji prati službeni izgled Porezne
  uprave.
* **ePorezna XML** — generira `<PdvObrazac>` XML za upload na ePorezna
  web portal ili za CISF razmjenu.
* **Detekcija EU partnera** — automatski prepoznaje EU nabave
  (intra-Community acquisitions) i EU isporuke (intra-Community supplies)
  na temelju države partnera (bez HR).
* **Obrnuti porezni teret** — prepoznaje domaće reverse-charge
  transakcije (po nazivu poreza koji sadrži "obrnuti" ili "reverse").
* **Cron automatizacija** — automatski generira mjesečna izvješća 1. u
  mjesecu za prethodno razdoblje.

## Instalacija / Installation

Modul ovisi o: `account`, `l10n_hr`, `l10n_hr_fiscal`.

```bash
# Instalacija iz Odoo UI: Aplikacije → Ažuriraj listu aplikacija → potraži "HR PDV"
# Instalacija iz CLI:
./odoo-bin -c odoo.conf -d <database> -i l10n_hr_pdv --stop-after-init
```

## Konfiguracija / Configuration

1. **Tvrtka** mora imati postavljen OIB u polju `vat` (porezni
   identifikator). Ako OIB počinje s "HR", prefiks se automatski
   uklanja u XML-u.
2. **Država tvrtke** mora biti Hrvatska (`base.hr`).
3. **PDV stope** moraju biti definirane u računovodstvu tvrtke sa
   stopama 25, 13 i 5 (redovnim putevima `l10n_hr` lokalizacije).
4. **Cron** `cron_l10n_hr_pdv_generate_monthly` je noupdate — pokreće
   se dnevno i generira izvješća za prethodni mjesec ako ne postoje.

## Korištenje / Usage

1. **Ručno kreiranje izvješća:**
   - Idite na *HR PDV → PDV izvještaji*.
   - Kliknite *Novo*, odaberite tip razdoblja (mjesečno / kvartalno),
     godinu i broj razdoblja.
   - Kliknite *Izračunaj* — modul dohvaća sve knjižene `account.move`
     u razdoblju i generira stavke.
   - Kliknite *Generiraj XML* za ePorezna XML.
   - Kliknite *Preuzmi XML* za preuzimanje datoteke.
2. **Statusi:** `draft` → `computed` → `submitted` → `accepted`
   (ili `rejected`). Status *accepted*/*rejected* ručno postavlja
   korisnik nakon odgovora Porezne uprave.
3. **Ispisi:**
   - *Knjiga PDV-a (PDF)* — A4 landscape, popis svih stavki.
   - *PDV obrazac (PDF)* — A4 portrait, službeni obrazac.

## PDV stope / VAT rates

| Stopa | Naziv | Primjena |
|-------|-------|----------|
| 25%   | Opća stopa | Standardna stopa na većinu dobara i usluga |
| 13%   | Snižena stopa | Prehrambeni proizvodi, knjige, novine, voda, javni prijevoz |
| 5%    | Posebno snižena stopa | Lijekovi, medicinska pomagala, edukacija, stambeni najam |

Module-bucketing (prepoznavanje stope): `models/l10n_hr_pdv_report_line.py`
funkcija `_rate_bucket()`.

## EU države / EU country codes

Detekcija EU partnera koristi skup `EU_COUNTRY_CODES` u
`models/l10n_hr_pdv_report_line.py` (isključuje HR):

```
AT, BE, BG, CY, CZ, DE, DK, EE, ES, FI, FR,
GR, HU, IE, IT, LT, LU, LV, MT, NL, PL, PT,
RO, SE, SI, SK
```

* **EU nabave** (`is_eu_acquisition`): ulazni dokument (`in_invoice`
  / `in_refund`) s partnerom iz EU (ne HR).
* **EU isporuke** (`is_eu_supply`): izlazni dokument (`out_invoice`
  / `out_refund`) s partnerom iz EU (ne HR).

## ePorezna XML format

Generira se XML struktura `<PdvObrazac>` (vidi metodu
`_build_eporezna_xml()`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PdvObrazac xmlns="urn:eporezna.porezna-uprava.hr">
  <Razdoblje>
    <Tip>mjesec|kvartal</Tip>
    <Godina>2024</Godina>
    <Broj>1</Broj>
    <DatumOd>2024-01-01</DatumOd>
    <DatumDo>2024-01-31</DatumDo>
  </Razdoblje>
  <Obveznik>
    <OIB>12345678901</OIB>
    <Naziv>Company name</Naziv>
  </Obveznik>
  <IzlazniPdv>
    <Stopa25><Osnovica/><Porez/></Stopa25>
    <Stopa13><Osnovica/><Porez/></Stopa13>
    <Stopa5><Osnovica/><Porez/></Stopa5>
  </IzlazniPdv>
  <UlazniPdv>
    <Stopa25><Osnovica/><Porez/></Stopa25>
    <Stopa13><Osnovica/><Porez/></Stopa13>
    <Stopa5><Osnovica/><Porez/></Stopa5>
  </UlazniPdv>
  <ObrnutiPorezniTeret>0.00</ObrnutiPorezniTeret>
  <EUNabave>0.00</EUNabave>
  <EUIsporuke>0.00</EUIsporuke>
  <PdvZaUplatu>0.00</PdvZaUplatu>
  <PdvZaPovrat>0.00</PdvZaPovrat>
</PdvObrazac>
```

## Rokovi predaje / Deadlines

* **Mjesečno izvještavanje:** 20. u mjesecu za prethodni mjesec.
* **Kvartalno izvještavanje:** 20. u mjesecu nakon završetka kvartala.

Računa se automatski u metodi `_compute_dates()` i pohranjuje u polje
`deadline`.

## Cron automatizacija / Cron automation

Cron zadatak `cron_l10n_hr_pdv_generate_monthly` (dan u
`data/ir_cron_data.xml`) pokreće se **dnevno** i poziva
`_cron_generate_pdv_reports()`. Metoda:

1. Pregledava sve tvrtke s državom = HR.
2. Za svaku tvrtku provjerava postoji li mjesečno izvješće za
   prethodni mjesec; ako ne postoji, kreira ga i automatski
   izračunava (`action_compute()`).
3. Postojeća izvješća se ne prepisuju.

## Tehničke napomene / Technical notes

* Modul ne dodaje dodatne stupce u `account_move` — sva PDV
  obilježja (reverse charge, EU nabava, EU isporuka) se izračunavaju
  on-the-fly iz partnerove države i naziva poreza.
* `_compute_amounts()` je storen i ovisi o `line_ids` te njihovim
  poljima — rekomputacija se automatski događa pri promjeni stavki.
* Valuta izvješća = valuta tvrtke (`company_id.currency_id`).
* XML escaping koristi jednostavnu funkciju `_escape_xml()` (bez
  vanjskih ovisnosti).
* Modul prati konvencije postojećeg `l10n_hr_fiscal` modula (isti
  autor, ista licenca).

## Reference

* [Zakon o PDV-u (N.N. 73/13, ...)](https://www.zakon.hr/z/219/Zakon-o-porezu-na-dodanu-vrijednost)
* [Pravilnik o PDV obrascu — ePorezna](https://porezna.gov.hr/eporezna)
* [Porezna uprava RH](https://porezna.gov.hr)
* [ePorezna portal](https://eporezna.porezna-uprava.gov.hr)

---

## Datoteke / Files

```
l10n_hr_pdv/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── ir_cron_data.xml              # Daily cron: monthly reports
│   └── ir_sequence_data.xml          # PDV/%(year)s/ sequence
├── models/
│   ├── __init__.py
│   ├── l10n_hr_pdv_report.py         # l10n_hr.pdv.report + account.move extension
│   └── l10n_hr_pdv_report_line.py    # l10n_hr.pdv.report.line
├── reports/
│   ├── pdv_form_report.xml           # PDV obrazac PDF (QWeb)
│   └── pdv_ledger_report.xml         # Knjiga PDV-a PDF (QWeb)
├── security/
│   └── ir.model.access.csv           # User/manager access
├── views/
│   ├── account_move_views.xml        # account.move minor extension
│   ├── l10n_hr_pdv_menu.xml          # HR PDV menu
│   └── l10n_hr_pdv_report_views.xml  # tree + form + search views
└── README.md
```
