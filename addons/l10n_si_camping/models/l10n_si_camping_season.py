# -*- coding: utf-8 -*-
"""Sezone - nizka/prelivna/visoka + prazniki."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiCampingSeason(models.Model):
    _name = 'l10n_si.camping.season'
    _description = 'Slovenian Camping Season'
    _order = 'date_from'

    name = fields.Char(required=True, translate=True)
    code = fields.Selection(
        selection=[('low', 'Nizka sezona'),
                   ('shoulder', 'Prelivna'),
                   ('high', 'Visoka sezona'),
                   ('peak', 'Vrhunec (prazniki)'),
                   ('winter', 'Zima (zaprto)')],
        required=True,
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    multiplier = fields.Float(
        string='Cenovni množitelj',
        default=1.0,
        help='Cena parcele × ta faktor. 1.0 = osnovna, 1.5 = visoka sezona.',
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for s in self:
            if s.date_from >= s.date_to:
                raise ValidationError(_('Date from must be before date to.'))

    @api.model
    def get_season_for_date(self, target_date):
        """Return the season record active on target_date, or None."""
        season = self.search([
            ('date_from', '<=', target_date),
            ('date_to', '>=', target_date),
            ('active', '=', True),
        ], limit=1, order='date_from')
        return season or False
