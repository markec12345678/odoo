# -*- coding: utf-8 -*-
"""Review source - konfiguracija povezav z zunanjimi platformami."""
from odoo import api, fields, models


class L10nSiReviewSource(models.Model):
    _name = 'l10n_si.review.source'
    _description = 'Slovenian Review Source'
    _order = 'sequence'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    platform = fields.Selection(
        selection=[('booking_com', 'Booking.com'),
                   ('tripadvisor', 'TripAdvisor'),
                   ('google', 'Google Reviews'),
                   ('airbnb', 'Airbnb'),
                   ('expedia', 'Expedia'),
                   ('internal', 'Interni obrazec')],
        required=True,
        default='internal',
    )

    # API credentials
    api_endpoint = fields.Char()
    api_key = fields.Char()
    api_username = fields.Char()
    api_password = fields.Char()
    hotel_id_on_platform = fields.Char(string='Hotel ID na platformi')

    # Sync settings
    sync_frequency_hours = fields.Integer(default=6, string='Sync vsakih (ur)')
    last_sync = fields.Datetime(readonly=True, copy=False)
    last_sync_status = fields.Selection(
        selection=[('success', 'Uspešno'),
                   ('error', 'Napaka'),
                   ('never', 'Nikoli')],
        default='never', readonly=True,
    )
    last_error = fields.Text(readonly=True)

    review_ids = fields.One2many('l10n_si.review', 'source_id', string='Ocene')
    review_count = fields.Integer(compute='_compute_count', store=False)
    average_rating = fields.Float(compute='_compute_count', store=False)

    def _compute_count(self):
        for s in self:
            s.review_count = len(s.review_ids)
            if s.review_ids:
                s.average_rating = sum(s.review_ids.mapped('rating')) / len(s.review_ids)
            else:
                s.average_rating = 0.0

    @api.model
    def _cron_sync_all_sources(self):
        """Cron: pull new reviews from all configured sources."""
        for source in self.search([('active', '=', True), ('platform', '!=', 'internal')]):
            try:
                source._pull_reviews()
                source.write({
                    'last_sync': fields.Datetime.now(),
                    'last_sync_status': 'success',
                    'last_error': False,
                })
            except Exception as e:
                source.write({
                    'last_sync_status': 'error',
                    'last_error': str(e),
                })

    def _pull_reviews(self):
        """Pull reviews from external platform. Override per-platform."""
        self.ensure_one()
        # V produkciji: implementirati za vsako platformo posebej
        pass
