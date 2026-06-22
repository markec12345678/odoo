# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiSustainabilityCertificate(models.Model):
    _name = 'l10n_si.sustainability.certificate'
    _description = 'Slovenian Sustainability Certificate'
    _order = 'valid_from DESC'

    name = fields.Char(required=True, translate=True)
    cert_type = fields.Selection(
        selection=[('green_key', 'Green Key'),
                   ('eu_ecolabel', 'EU Ecolabel'),
                   ('travelife', 'Travelife'),
                   ('eko', 'EKO certifikat'),
                   ('iso_14001', 'ISO 14001'),
                   ('other', 'Drugo')],
        required=True, default='green_key')

    level = fields.Selection(
        selection=[('bronze', 'Bronze'), ('silver', 'Silver'),
                   ('gold', 'Gold'), ('platinum', 'Platinum'),
                   ('standard', 'Standard'), ('n/a', 'N/A')],
        default='standard')

    valid_from = fields.Date(required=True, default=fields.Date.today)
    valid_to = fields.Date(required=True)
    cert_number = fields.Char(string='Številka certifikata')
    issuing_body = fields.Char(string='Izdajatelj')

    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    active = fields.Boolean(default=True)
    notes = fields.Text()
    attachment_id = fields.Many2one('ir.attachment', string='Dokument')
