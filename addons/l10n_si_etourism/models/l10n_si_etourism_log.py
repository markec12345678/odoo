# -*- coding: utf-8 -*-
"""Dnevnik AJPES klicev — audit trail."""
from odoo import fields, models


class L10nSiEtourismLog(models.Model):
    _name = 'l10n_si.etourism.log'
    _description = 'Slovenian eTurizem Audit Log'
    _order = 'submitted_at DESC'

    registration_id = fields.Many2one('l10n_si.etourism.guest.registration', string='Registracija', ondelete='restrict')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    request_type = fields.Selection(
        selection=[('registration', 'Prijava gosta'), ('deregistration', 'Odjava gosta'),
                   ('monthly_report', 'Mesečno poročilo'), ('ping', 'Test povezave')], required=True,
    )
    submitted_at = fields.Datetime(default=fields.Datetime.now, required=True)
    duration_ms = fields.Integer()
    request_xml = fields.Text()
    response_xml = fields.Text()
    http_status = fields.Integer()
    state = fields.Selection(
        selection=[('draft', 'Osnutek'), ('pending', 'V obdelavi'), ('sent', 'Poslano'), ('error', 'Napaka')], default='draft',
    )
    error_message = fields.Text()
