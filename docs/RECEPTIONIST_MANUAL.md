# Priročnik za receptorico — SI/HR Odoo 19

## 1. Dnevne naloge

### Zjutraj
1. Preveri današnje prihode — Hotel → Rezervacije → Filter: Danes = check-in
2. Preveri današnje odhode — Hotel → Rezervacije → Filter: Danes = check-out
3. Preveri AJPES status — SI eTurizem → Prijave gostov → Filter: Napake
4. Preveri FURS status — Računi → Filter: Fiscal state = Napaka

### Zvečer
1. Izpiši X-poročilo — POS → X-poročilo
2. Preveri, da so vsi računi fiskalizirani
3. Zaključi POS sejo — POS → Z-poročilo → Zaključi sejo

## 2. Prijava gosta (Check-in)
1. Hotel → Rezervacije → najdi rezervacijo
2. Preveri: ime, soba, datumi, število gostov
3. Preveri osebni dokument (potni list/osebna izkaznica)
4. Klikni **"Prijava"** — soba → zasedena, folio kreiran, AJPES prijava samodejno
5. Izroči ključ, razloži WiFi/zajtrk/check-out čas

**Zakonska obveznost**: Prijava gostov v 24h po ZPPreb-1. Kazen 500–4.000 EUR.

## 3. Odjava gosta (Check-out)
1. Hotel → Rezervacije → najdi (state = "Prijava")
2. Preveri folio (sobe + storitve + turistična taksa)
3. Klikni **"Odjava"** — soba → čiščenje, folio zaključen, AJPES odjava samodejno
4. Kreiraj račun → FURS ZOI/EOR samodejno
5. Prejmi plačilo, izroči račun

## 4. Rezervacije
- **Nova**: Hotel → Rezervacije → Kreiraj → izpolni → Potrdi
- **Booking.com/Airbnb**: samodejno (cron vsakih 15 min)
- **Preklic**: Odpri → Prekliči (soba se sprosti)
- **No-show**: Odpri → "Ni prišel"

## 5. FURS in AJPES
- **FURS**: vsak račun mora imeti ZOI/EOR. Če napaka → "Ponovno pošlji FURS"
- **AJPES**: prijavi vsakega gosta v 24h. Če napaka → preveri podatke gosta
- **Turistična taksa**: samodejno na folio (odvisno od občine)

## 6. POS blagajna
1. POS → Odpri POS UI
2. Izberi mizo → dodaj artikle → plačaj
3. Račun se samodejno fiskalizira (ZOI/EOR + QR koda)
4. **Plačilo na sobo**: izberi "Plačilo na sobo" → izberi folio gosta

### Z-poročilo (dnevni zaključek)
1. POS → Seje → Z-poročilo
2. Preveri: promet, DDV, plačila, FURS status
3. Natisni PDF → Zaključi sejo

## 7. Reševanje težav
| Težava | Rešitev |
|---------|---------|
| FURS napaka | Klikni "Ponovno pošlji FURS" |
| AJPES napaka | Preveri podatke gosta → "Pošlji prijavo" |
| Soba "zasedena" a gost odšel | Hotel → Sobe → "Prosta" |
| POS ne more zaključiti | Počakaj 5 min (FURS pending) ali "Ponovno pošlji" |

## Kontakti
- FURS: +386 1 478 3000
- AJPES: +386 1 587 51 00
