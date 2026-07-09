# -*- coding: utf-8 -*-
"""WhatsApp template model — predloge sporočil."""
from odoo import fields, models


class L10nSiWhatsAppTemplate(models.Model):
    _name = 'l10n_si.whatsapp.template'
    _description = 'WhatsApp Message Template'

    name = fields.Char(required=True, help='Ime predloge (npr. reservation_confirm)')
    language = fields.Selection([
        ('sl', 'Slovenščina'),
        ('hr', 'Hrvaščina'),
        ('en', 'English'),
    ], default='sl', required=True)
    body = fields.Text(string='Vsebina predloge', help='Besedilo z {{1}}, {{2}} za spremenljivke.')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
