# -*- coding: utf-8 -*-
"""Review - posamezna ocena gosta."""
from odoo import api, fields, models


class L10nSiReview(models.Model):
    _name = 'l10n_si.review'
    _description = 'Slovenian Review'
    _inherit = ['mail.thread']
    _order = 'review_date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Source
    source_id = fields.Many2one('l10n_si.review.source', required=True, ondelete='restrict')
    source_platform = fields.Selection(related='source_id.platform', store=True)
    external_review_id = fields.Char(string='ID ocene na platformi', copy=False,
                                       help='ID review-a na zunanjem viru (prepreči duplikate)')

    # Gost
    partner_id = fields.Many2one('res.partner', string='Gost (če znan)')
    guest_name = fields.Char(string='Ime gosta')
    guest_country_id = fields.Many2one('res.country', string='Država gosta')

    # Vsebina
    title = fields.Char(string='Naslov')
    body = fields.Text(string='Vsebina ocene', required=True)
    rating = fields.Selection(
        selection=[('1', '1 - Zelo slabo'),
                   ('2', '2 - Slabo'),
                   ('3', '3 - Srednje'),
                   ('4', '4 - Dobro'),
                   ('5', '5 - Odlično'),
                   ('6', '6 - Zelo odlično'),
                   ('7', '7 - Izjemno'),
                   ('8', '8 - Odlično'),
                   ('9', '9 - Superb'),
                   ('10', '10 - Nepozabno')],
        required=True,
        tracking=True,
    )
    rating_normalized = fields.Float(compute='_compute_normalized', store=True,
                                       string='Normalizirana ocena (0-5)',
                                       help='Vsa merila normalizirana na 0-5 za primerjavo.')

    # Datum
    review_date = fields.Datetime(required=True, default=fields.Datetime.now)
    stay_date = fields.Date(string='Datum bivanja')
    visit_type = fields.Selection(
        selection=[('solo', 'Sam'),
                   ('couple', 'Par'),
                   ('family', 'Družina'),
                   ('friends', 'Prijatelji'),
                   ('business', 'Poslovno'),
                   ('group', 'Skupina')],
        string='Tip potovanja',
    )

    # AI analiza
    sentiment = fields.Selection(
        selection=[('very_positive', 'Zelo pozitivno'),
                   ('positive', 'Pozitivno'),
                   ('neutral', 'Nevtralno'),
                   ('negative', 'Negativno'),
                   ('very_negative', 'Zelo negativno'),
                   ('not_analyzed', 'Ni analizirano')],
        default='not_analyzed',
        tracking=True,
    )
    detected_categories = fields.Char(string='Zaznane kategorije',
                                        help='npr. čistoča, osebje, hrana, lokacija, cena, soba, wellness')
    ai_summary = fields.Text(string='AI povzetek')

    # Odgovor
    response_text = fields.Text(string='Naš odgovor')
    response_author_id = fields.Many2one('res.users', string='Avtor odgovora', readonly=True, copy=False)
    responded_on = fields.Datetime(readonly=True, copy=False)
    response_time_hours = fields.Float(compute='_compute_response_time', store=True)
    is_responded = fields.Boolean(compute='_compute_response_status', store=True)

    # Status
    state = fields.Selection(
        selection=[('new', 'Novo'),
                   ('analyzed', 'Analizirano'),
                   ('responded', 'Odgovorjeno'),
                   ('escalated', 'Preneseno na vodjo'),
                   ('archived', 'Arhivirano')],
        default='new',
        tracking=True,
    )

    # Slike
    image_ids = fields.One2many('l10n_si.review.image', 'review_id', string='Slike')
    image_count = fields.Integer(compute='_compute_image_count', store=False)

    # Povezave
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Povezani folio')
    hotel_reservation_id = fields.Many2one('l10n_si.hotel.reservation', string='Povezana rezervacija')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.review') or '/'
        return super().create(vals_list)

    @api.depends('guest_name', 'review_date', 'number')
    def _compute_name(self):
        for r in self:
            name = r.guest_name or 'Anonimni gost'
            date = r.review_date.strftime('%d.%m.%Y') if r.review_date else ''
            r.name = f'{r.number} - {name} ({date})'

    @api.depends('rating')
    def _compute_normalized(self):
        for r in self:
            try:
                rating = int(r.rating)
                # Booking-style 1-10 → 0-5
                r.rating_normalized = (rating - 1) * 5 / 9 if rating <= 10 else 0
            except (ValueError, TypeError):
                r.rating_normalized = 0

    @api.depends('review_date', 'responded_on')
    def _compute_response_time(self):
        for r in self:
            if r.review_date and r.responded_on:
                delta = r.responded_on - r.review_date
                r.response_time_hours = delta.total_seconds() / 3600.0
            else:
                r.response_time_hours = 0.0

    @api.depends('response_text')
    def _compute_response_status(self):
        for r in self:
            r.is_responded = bool(r.response_text)

    def _compute_image_count(self):
        for r in self:
            r.image_count = len(r.image_ids)

    def action_analyze_sentiment(self):
        """AI analiza sentiment-a in kategorij. V produkciji: pravi AI klic."""
        for review in self:
            body_lower = (review.body or '').lower()
            # Preprosta rule-based analiza
            positive_words = ['odlično', 'super', 'priporočam', 'lepo', 'čisto', 'prijazno',
                                'dobro', 'zadovoljen', 'vredu', 'hvala']
            negative_words = ['slabo', 'umazano', 'ne priporočam', 'nevljudno', 'drago',
                                'razočaran', 'težave', 'hladno', 'toga', 'pokvarjeno']

            pos_count = sum(1 for w in positive_words if w in body_lower)
            neg_count = sum(1 for w in negative_words if w in body_lower)

            if pos_count > neg_count + 1:
                review.sentiment = 'very_positive' if pos_count > 3 else 'positive'
            elif neg_count > pos_count + 1:
                review.sentiment = 'very_negative' if neg_count > 3 else 'negative'
            else:
                review.sentiment = 'neutral'

            # Kategorizacija
            categories = []
            cat_keywords = {
                'čistoča': ['čisto', 'umazano', 'higiena', 'prah'],
                'osebje': ['osebje', 'reception', 'natakar', 'hišnik', 'prijazen'],
                'hrana': ['hrana', 'zajtrk', 'večerja', 'restavracija', 'jed'],
                'lokacija': ['lokacija', 'center', 'plaža', 'blizu'],
                'cena': ['cena', 'drago', 'ceneje', 'vredno'],
                'soba': ['soba', 'postelja', 'kopalnica', 'velikost'],
                'wellness': ['wellness', 'bazen', 'sauna', 'masaža'],
            }
            for cat, keywords in cat_keywords.items():
                if any(kw in body_lower for kw in keywords):
                    categories.append(cat)

            review.detected_categories = ', '.join(categories)
            review.ai_summary = f'Sentiment: {review.sentiment}. Kategorije: {", ".join(categories) or "brez"}'
            review.state = 'analyzed'

    def action_respond(self):
        """Odgovori na oceno."""
        for review in self:
            if not review.response_text:
                continue
            review.write({
                'state': 'responded',
                'responded_on': fields.Datetime.now(),
                'response_author_id': self.env.user.id,
            })

    def action_escalate(self):
        self.write({'state': 'escalated'})

    def action_archive(self):
        self.write({'state': 'archived'})

    def action_generate_ai_response(self):
        """AI predlog odgovora. V produkciji: pravi AI klic."""
        for review in self:
            if review.sentiment == 'very_positive' or review.sentiment == 'positive':
                review.response_text = (
                    f' Spoštovani {review.guest_name or "gost"},\n\n'
                    f'Hvala za vašo pozitivno oceno! Veselimo se vašega naslednjega obiska.\n\n'
                    f'Lep pozdrav,\nEkipa'
                )
            elif review.sentiment == 'negative' or review.sentiment == 'very_negative':
                review.response_text = (
                    f'Spoštovani {review.guest_name or "gost"},\n\n'
                    f'Hvala za vaše povratne informacije. Žal nam je, da izkušnja '
                    f'ni bila v skladu z vašimi pričakovanji. Vaše pripombe bomo '
                    f'podrobno preučili in ukrepali.\n\n'
                    f'Lep pozdrav,\nVodja'
                )
            else:
                review.response_text = (
                    'Spoštovani,\n\n'
                    'Hvala za vaše mnenje. Cenimo vaše povratne informacije.\n\n'
                    'Lep pozdrav'
                )


class L10nSiReviewImage(models.Model):
    _name = 'l10n_si.review.image'
    _description = 'Slovenian Review Image'

    review_id = fields.Many2one('l10n_si.review', required=True, ondelete='cascade')
    image = fields.Binary(required=True)
    caption = fields.Char()
    source_url = fields.Char(string='URL slike (na platformi)')
