# -*- coding: utf-8 -*-
"""Predloga pogodbe - HTML z placeholderji."""
from odoo import fields, models


class L10nSiEventContractTemplate(models.Model):
    _name = 'l10n_si.event.contract.template'
    _description = 'Slovenian Event Contract Template'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    active = fields.Boolean(default=True)
    contract_type = fields.Selection(
        selection=[('wedding', 'Poročna pogodba'),
                   ('conference', 'Konferenčna pogodba'),
                   ('hall_rental', 'Najem dvorane'),
                   ('sponsorship', 'Sponsorska pogodba'),
                   ('catering', 'Catering pogodba'),
                   ('other', 'Drugo')],
        default='hall_rental',
        required=True,
    )

    body = fields.Html(required=True,
                        help='Placeholders: {{event.name}}, {{event.date_start}}, '
                             '{{event.partner_id.name}}, {{event.venue_id.name}}, '
                             '{{event.total_amount}}, {{event.expected_guests}}, '
                             '{{company.name}}, {{company.street}}, {{company.vat}}')

    description = fields.Text()
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]
