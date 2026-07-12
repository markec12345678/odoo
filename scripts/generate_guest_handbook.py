#!/usr/bin/env python3
"""Generate a bilingual (SI/EN) guest handbook PDF for the SI/HR Tourism Suite."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

FONT_DIR = '/usr/share/fonts'
# DejaVu fonts support full Slovenian/Croatian diacritics (č, š, ž, ć, đ)
# Register under 'NotoSerifSC' name so existing styles work without changes
pdfmetrics.registerFont(TTFont('NotoSerifSC', f'{FONT_DIR}/truetype/dejavu/DejaVuSerif.ttf'))
pdfmetrics.registerFont(TTFont('NotoSerifSC-Bold', f'{FONT_DIR}/truetype/dejavu/DejaVuSans-Bold.ttf'))
registerFontFamily('NotoSerifSC', normal='NotoSerifSC', bold='NotoSerifSC-Bold')

PRIMARY = HexColor('#1E3A5F')
ACCENT = HexColor('#C8A951')
WARM_BG = HexColor('#FDF8F0')
TEXT_DARK = HexColor('#2C2C2C')
TEXT_LIGHT = HexColor('#6B6B6B')
DIVIDER = HexColor('#D4C4A0')
WHITE = HexColor('#FFFFFF')

def create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CoverTitle', fontName='NotoSerifSC-Bold', fontSize=36, leading=42, textColor=WHITE, alignment=TA_CENTER, spaceAfter=8))
    styles.add(ParagraphStyle(name='CoverSubtitle', fontName='NotoSerifSC', fontSize=16, leading=22, textColor=ACCENT, alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name='CoverTagline', fontName='NotoSerifSC', fontSize=11, leading=16, textColor=HexColor('#B0B0B0'), alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='SectionHeading', fontName='NotoSerifSC-Bold', fontSize=18, leading=24, textColor=PRIMARY, spaceBefore=20, spaceAfter=6))
    styles.add(ParagraphStyle(name='SubHeading', fontName='NotoSerifSC-Bold', fontSize=13, leading=18, textColor=PRIMARY, spaceBefore=12, spaceAfter=4))
    styles.add(ParagraphStyle(name='BodySI', fontName='NotoSerifSC', fontSize=10.5, leading=16, textColor=TEXT_DARK, alignment=TA_JUSTIFY, spaceAfter=2))
    styles.add(ParagraphStyle(name='BodyEN', fontName='NotoSerifSC', fontSize=9.5, leading=14, textColor=TEXT_LIGHT, alignment=TA_JUSTIFY, spaceAfter=8))
    styles.add(ParagraphStyle(name='InfoBox', fontName='NotoSerifSC', fontSize=10, leading=14, textColor=TEXT_DARK, spaceAfter=4))
    styles.add(ParagraphStyle(name='InfoBoxHeading', fontName='NotoSerifSC-Bold', fontSize=11, leading=15, textColor=PRIMARY, spaceAfter=4))
    return styles

def bilingual_para(si_text, en_text, styles):
    return [Paragraph(si_text, styles['BodySI']), Paragraph(en_text, styles['BodyEN'])]

def info_box(title, lines, styles, bg_color=WARM_BG):
    content = [Paragraph(title, styles['InfoBoxHeading'])]
    for line in lines:
        content.append(Paragraph(f'• {line}', styles['InfoBox']))
    tbl = Table([[content]], colWidths=[170*mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ('BOX', (0, 0), (-1, -1), 0.5, DIVIDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return tbl

def section_divider():
    return HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=6, spaceAfter=10)

def cover_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1] - 8*mm, A4[0], 8*mm, fill=1, stroke=0)
    canvas.rect(0, 0, A4[0], 8*mm, fill=1, stroke=0)
    canvas.restoreState()

def body_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(1.5)
    canvas.line(20*mm, height - 15*mm, width - 20*mm, height - 15*mm)
    canvas.setFont('NotoSerifSC', 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(20*mm, height - 12*mm, 'Priročnik za gostje / Guest Handbook')
    canvas.drawRightString(width - 20*mm, height - 12*mm, 'SI/HR Tourism Suite')
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, 15*mm, width - 20*mm, 15*mm)
    canvas.setFont('NotoSerifSC', 8)
    canvas.setFillColor(TEXT_LIGHT)
    canvas.drawString(20*mm, 10*mm, 'Dobrodošli / Welcome')
    canvas.drawRightString(width - 20*mm, 10*mm, f'Stran / Page {doc.page}')
    canvas.restoreState()

def build_cover(styles):
    elements = []
    elements.append(Spacer(1, 80*mm))
    elements.append(Paragraph('Priročnik za gostje', styles['CoverTitle']))
    elements.append(Paragraph('Guest Handbook', styles['CoverSubtitle']))
    elements.append(Spacer(1, 20*mm))
    elements.append(Paragraph('SI/HR Tourism Suite', styles['CoverTagline']))
    elements.append(Paragraph('Odoo 19 — Slovenija &amp; Hrvaška', styles['CoverTagline']))
    elements.append(Spacer(1, 60*mm))
    elements.append(Paragraph('Dobrodošli v našem hotelu', styles['CoverSubtitle']))
    elements.append(Paragraph('Welcome to our hotel', styles['CoverTagline']))
    return elements

def build_content(styles):
    elements = []
    elements.append(Paragraph('1. Dobrodošli / Welcome', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Spoštovani gost, lepo vas pozdravljamo v našem hotelu. Veselimo se vašega boravka in storili bomo vse, da bo vaše bivanje prijetno in brezskrbno. Ta priročnik vsebuje vse pomembne informacije, ki jih potrebujete med bivanjem pri nas. Če imate kakršna koli vprašanja, smo vam vedno na voljo.',
        'Dear guest, welcome to our hotel. We are delighted to have you stay with us and will do everything to make your stay pleasant and carefree. This handbook contains all the important information you need during your stay. If you have any questions, we are always at your service.',
        styles
    ))
    elements.append(Paragraph('1.1 Prijava in odjava / Check-in &amp; Check-out', styles['SubHeading']))
    elements.extend(bilingual_para(
        'Prijava v sobo je mogoča od 14:00 ure naprej. Ob prijavi prosimo predstavite osebni dokument (potni list ali osebno izkaznico) za registracijo pri AJPES (slovenski sistem eTurizem). Odjava je do 11:00 ure. Če želite pozno odjavo, prosimo obvestite recepcijo vsaj 24 ur pred odhodom.',
        'Check-in is available from 14:00. Upon arrival, please present an ID document (passport or national ID) for registration with AJPES (Slovenian eTourism system). Check-out is by 11:00. If you require a late check-out, please inform the reception at least 24 hours before departure.',
        styles
    ))
    elements.append(info_box('Hitre informacije / Quick Info', [
        '<b>Prijava / Check-in:</b> 14:00',
        '<b>Odjava / Check-out:</b> 11:00',
        '<b>Recepcija / Reception:</b> 24/7',
        '<b>Zajtrk / Breakfast:</b> 7:00 — 10:00',
    ], styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('2. WiFi in internet / WiFi &amp; Internet', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Brezplačni WiFi je na voljo v celotnem hotelu, vključno s sobami, jedovalnico in wellness centrom. Omrežje je hitro in varno. Geslo najdete na tej strani ali na kartici v vaši sobi. Za težave s povezavo se obrnite na recepcijo.',
        'Free WiFi is available throughout the hotel, including rooms, dining area, and wellness center. The network is fast and secure. The password is listed on this page and on the card in your room. For connection issues, please contact the reception.',
        styles
    ))
    elements.append(info_box('WiFi dostop / WiFi Access', [
        '<b>Omrežje / Network:</b> Hotel_Guest_WiFi',
        '<b>Geslo / Password:</b> Gost2025',
        '<b>Hitrost / Speed:</b> do 100 Mbps',
        '<b>Pokritost / Coverage:</b> celoten hotel',
    ], styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('3. Zajtrk in prehrana / Breakfast &amp; Dining', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Bogati samopostrežni zajtrk je vključen v ceno vašega bivanja. Postrežen je v restavraciji v pritličju od 7:00 do 10:00 ure vsak dan. Ponujamo široko izbiro svežih peciv, sadja, sirev, mesnih izdelkov, toplih in hladnih jedi ter pijač. Za alergije ali posebne prehranske potrebe prosimo obvestite recepcijo ob prijavi.',
        'A rich buffet breakfast is included in your stay. It is served in the ground-floor restaurant from 7:00 to 10:00 every day. We offer a wide selection of fresh pastries, fruit, cheeses, cold cuts, hot and cold dishes, and beverages. For allergies or special dietary requirements, please inform the reception upon check-in.',
        styles
    ))
    elements.append(Paragraph('3.1 Restavracija / Restaurant', styles['SubHeading']))
    elements.extend(bilingual_para(
        'Naša restavracija ponuja tradicionalne slovenske in mednarodne jedi pripravljene iz lokalnih sestavin. Odprta je za kosilo od 12:00 do 15:00 in za večerjo od 18:00 do 22:00. Rezervacije miz sprejemamo na recepciji ali telefonsko na notranjo številko 100.',
        'Our restaurant offers traditional Slovenian and international dishes prepared with local ingredients. It is open for lunch from 12:00 to 15:00 and for dinner from 18:00 to 22:00. Table reservations can be made at the reception or by calling extension 100.',
        styles
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('4. Wellness in spa / Wellness &amp; Spa', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Wellness center je odprt vsak dan od 9:00 do 21:00. Dostop je brezplačen za vse goste. Vključuje notranji bazen, savno, parno kopel in fitnes. Masaže in tretmaji so na voljo po predhodni rezervaciji. Prosimo upoštevajte hišni red wellness centra: pred uporabo se stuširajte, v savni uporabljajte brisačo, v bazenu pa pokrivalo za glavo.',
        'The wellness center is open daily from 9:00 to 21:00. Access is free for all guests. It includes an indoor pool, sauna, steam bath, and fitness room. Massages and treatments are available by prior reservation. Please observe the wellness center rules: shower before use, use a towel in the sauna, and wear a swimming cap in the pool.',
        styles
    ))
    elements.append(info_box('Wellness urnik / Wellness Hours', [
        '<b>Bazen / Pool:</b> 9:00 — 21:00',
        '<b>Sauna:</b> 14:00 — 20:00',
        '<b>Fitnes / Gym:</b> 6:00 — 22:00',
        '<b>Masaže / Massages:</b> po dogovoru / by appointment',
    ], styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('5. AI Concierge — vaš digitalni asistent / your digital assistant', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Naš AI Concierge je na voljo 24 ur na dan preko spletnega klepeta na naši spletni strani ali preko WhatsAppa. AI asistent vam lahko pomaga pri vprašanjih o WiFi geslu, urah zajtrka, urniku wellnessa, priporočilih lokalnih atrakcij, restavracij in prevoza. Za kompleksnejše prošnje vas bo AI preusmeril na našo recepcijo.',
        'Our AI Concierge is available 24 hours a day via web chat on our website or via WhatsApp. The AI assistant can help you with questions about WiFi password, breakfast hours, wellness schedule, recommendations for local attractions, restaurants, and transport. For more complex requests, the AI will transfer you to our reception.',
        styles
    ))
    elements.append(Paragraph('5.1 Kako uporabljati AI Concierge / How to use AI Concierge', styles['SubHeading']))
    elements.extend(bilingual_para(
        'Preprosto odprite spletni klepet na naši spletni strani ali pošljite sporočilo na naš WhatsApp. AI bo prepoznal vaše vprašanje in odgovoril v slovenščini ali angleščini. Primeri vprašanj: "Kakšno je WiFi geslo?", "Kdaj je zajtrk?", "Priporočite restavracijo v bližini?", "Kako pridem do centra mesta?".',
        'Simply open the web chat on our website or send a message to our WhatsApp. The AI will recognize your question and respond in Slovenian or English. Example questions: "What is the WiFi password?", "When is breakfast?", "Can you recommend a nearby restaurant?", "How do I get to the city center?".',
        styles
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('6. Soba in storitve / Room &amp; Amenities', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Vaša soba je opremljena z vsem, kar potrebujete za prijetno bivanje. Mini bar je dopolnjen vsak dan, brisače se zamenjajo vsak drugi dan, posteljnina pa enkrat tedensko. Če potrebujete dodatne brisače, blazine ali druge pripomočke, pokličite recepcijo na notranjo številko 0.',
        'Your room is equipped with everything you need for a pleasant stay. The mini bar is restocked daily, towels are changed every other day, and bed linen once a week. If you need additional towels, pillows, or other amenities, call the reception at extension 0.',
        styles
    ))
    elements.append(info_box('Storitve v sobi / Room Services', [
        '<b>Mini bar:</b> dopolnjen dnevno / restocked daily',
        '<b>Brisače / Towels:</b> vsak drugi dan / every 2 days',
        '<b>Posteljnina / Linen:</b> tedensko / weekly',
        '<b>Sobna postrežba / Room service:</b> 7:00 — 23:00',
        '<b>Telefon / Phone:</b> notranja št. 0 / ext. 0',
    ], styles))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('7. Lokalne atrakcije / Local Attractions', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Naša lokacija je odlična izhodiščna točka za raziskovanje okolice. Recepcija vam lahko pomaga pri organizaciji izletov, rezervaciji vozovnic in priporočilih. Tukaj je nekaj bližnjih zanimivosti:',
        'Our location is an excellent starting point for exploring the surroundings. The reception can help you organize trips, book tickets, and provide recommendations. Here are some nearby attractions:',
        styles
    ))
    elements.append(Paragraph('7.1 Bled / Bled', styles['SubHeading']))
    elements.extend(bilingual_para(
        'Slikovito Blejsko jezero z otokom in cerkvico, Blejski grad na vrhu strme pečine in Vintgar soteska — vse znotraj 30 minut vožnje. Priporočamo ogled ob zori ali ob sončnem zahodu za najlepše fotografije.',
        'Picturesque Lake Bled with its island church, Bled Castle atop a steep cliff, and Vintgar Gorge — all within a 30-minute drive. We recommend visiting at dawn or sunset for the most beautiful photos.',
        styles
    ))
    elements.append(Paragraph('7.2 Ljubljana / Ljubljana', styles['SubHeading']))
    elements.extend(bilingual_para(
        'Prestolnica Slovenije ponuja čudovito staro mestno jedro, Ljubljanski grad, Tromostovje in živo kulinariko. Vozni čas: 25 minut. Priporočamo sprehod ob Ljubljanici in obisk centralne tržnice.',
        'The capital of Slovenia offers a beautiful old town, Ljubljana Castle, the Triple Bridge, and vibrant cuisine. Drive time: 25 minutes. We recommend a walk along the Ljubljanica river and a visit to the central market.',
        styles
    ))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('8. Nujne številke / Emergency Numbers', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'V primeru nuje pokličite 112 (splošna nujna številka v EU). Za specifične službe uporabite spodnje številke. Vse nujne številke so brezplačne in dostopne 24 ur na dan.',
        'In case of emergency, call 112 (general emergency number in the EU). For specific services, use the numbers below. All emergency numbers are free of charge and available 24 hours a day.',
        styles
    ))
    elements.append(info_box('Nujne številke / Emergency Numbers', [
        '<b>112</b> — Splošna nujna / General emergency (EU)',
        '<b>113</b> — Policija / Police',
        '<b>112 (medicinska)</b> — Reševalci / Ambulance',
        '<b>112 (gasilska)</b> — Gasilci / Fire brigade',
        '<b>Recepcija / Reception:</b> notranja št. 0 / ext. 0',
    ], styles, bg_color=HexColor('#FFF5F5')))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('9. Odjava / Check-out', styles['SectionHeading']))
    elements.append(section_divider())
    elements.extend(bilingual_para(
        'Ob odjavi prosimo predajte ključ na recepciji. Če želite račun poslati po e-pošti, prosimo obvestite recepcijo. Za pozno odjavo (po 11:00) se obračuna doplačilo v višini polovice dnevne cene sobe. Prtljago lahko pustite v shrambi na recepciji brezplačno do vašega odhoda.',
        'At check-out, please return your key at the reception. If you would like the invoice sent by email, please inform the reception. For late check-out (after 11:00), a surcharge of half the daily room rate applies. Luggage can be stored at the reception free of charge until your departure.',
        styles
    ))
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width='60%', thickness=1, color=ACCENT, spaceBefore=10, spaceAfter=10, hAlign='CENTER'))
    elements.append(Paragraph(
        '<para alignment="center"><b>Hvala, da ste izbrali naš hotel.</b><br/><i>Thank you for choosing our hotel.</i></para>',
        styles['BodySI']
    ))
    return elements

def main():
    output_path = '/home/z/my-project/download/Guest-Handbook-SI-EN.pdf'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=25*mm, bottomMargin=20*mm,
        title='Priročnik za gostje / Guest Handbook',
        author='SI/HR Tourism Suite',
        subject='Hotel guest handbook — bilingual SI/EN',
        creator='Odoo 19 SI/HR Tourism Suite',
    )
    styles = create_styles()
    story = []
    story.extend(build_cover(styles))
    story.append(PageBreak())
    story.extend(build_content(styles))
    def first_page(canvas, doc):
        cover_page(canvas, doc)
    def later_pages(canvas, doc):
        body_page(canvas, doc)
    doc.build(story, onFirstPage=first_page, onLaterPages=later_pages)
    size = os.path.getsize(output_path)
    print(f'PDF generated: {output_path}')
    print(f'Size: {size:,} bytes ({size/1024:.1f} KB)')

if __name__ == '__main__':
    main()
