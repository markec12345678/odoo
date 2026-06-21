# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiWhatsappTemplate(models.Model):
    _name = 'l10n_si.whatsapp.template'
    _description = 'Slovenian WhatsApp Template'

    name = fields.Char(required=True, translate=True)
    body = fields.Text(required=True, translate=True,
                       help='Placeholders: {{partner.name}}, {{user.name}}, {{date}}')
    language = fields.Selection(
        selection=[('sl', 'Slovenščina'),
                   ('en', 'English'),
                   ('hr', 'Hrvaščina')],
        default='sl',
        required=True,
    )
    category = fields.Selection(
        selection=[('marketing', 'Marketing'),
                   ('utility', 'Utility'),
                   ('authentication', 'Authentication')],
        default='utility',
        required=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
