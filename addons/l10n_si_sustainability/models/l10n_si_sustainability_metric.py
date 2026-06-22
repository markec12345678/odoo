# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiSustainabilityMetric(models.Model):
    _name = 'l10n_si.sustainability.metric'
    _description = 'Slovenian Sustainability Metric'
    _order = 'date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    date = fields.Date(required=True, default=fields.Date.today)
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    metric_type = fields.Selection(
        selection=[('electricity', 'Elektrika (kWh)'),
                   ('gas', 'Plin (m³)'),
                   ('water', 'Voda (m³)'),
                   ('heating_oil', 'Kurilno olje (l)'),
                   ('waste_organic', 'Biološki odpadki (kg)'),
                   ('waste_recyclable', 'Reciklirni odpadki (kg)'),
                   ('waste_mixed', 'Mešani odpadki (kg)'),
                   ('co2_emission', 'CO2 izpust (t)'),
                   ('guests', 'Število gostov')],
        required=True, default='electricity')

    quantity = fields.Float(required=True)
    unit = fields.Char(related='metric_type', store=False)  # simplified
    cost = fields.Float(default=0.0, string='Strošek (EUR)')

    # Per guest normalization
    guests_in_period = fields.Integer(default=0, string='Gostov v obdobju')
    per_guest = fields.Float(compute='_compute_per_guest', store=True, string='Na gosta')

    notes = fields.Text()

    @api.depends('metric_type', 'date')
    def _compute_name(self):
        labels = dict(self._fields['metric_type'].selection)
        for m in self:
            m.name = f'{labels.get(m.metric_type, m.metric_type)} - {m.date}'

    @api.depends('quantity', 'guests_in_period')
    def _compute_per_guest(self):
        for m in self:
            m.per_guest = m.quantity / m.guests_in_period if m.guests_in_period else 0.0
