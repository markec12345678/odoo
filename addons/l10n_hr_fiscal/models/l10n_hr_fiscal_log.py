# -*- coding: utf-8 -*-
"""CISF audit log — every fiscalization API call is logged for 5 years."""
from odoo import fields, models


class L10nHrFiscalLog(models.Model):
    _name = 'l10n_hr.fiscal.log'
    _description = 'Croatian CISF Fiscal Log'
    _order = 'submitted_at DESC'

    move_id = fields.Many2one('account.move', string='Račun', ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    request_type = fields.Selection(
        selection=[('invoice', 'Slanje računa'),
                   ('premise', 'Registracija prostora'),
                   ('check', 'Provjera računa')],
        required=True,
    )
    submitted_at = fields.Datetime(default=fields.Datetime.now, required=True)
    duration_ms = fields.Integer()
    request_xml = fields.Text()
    response_xml = fields.Text()
    http_status = fields.Integer()
    state = fields.Selection(
        selection=[('draft', 'Nacrt'),
                   ('pending', 'U obradi'),
                   ('sent', 'Poslano'),
                   ('error', 'Greška')],
        default='draft',
    )
    error_message = fields.Text()
    zki = fields.Char(readonly=True)
    jir = fields.Char(readonly=True)
    next_retry = fields.Datetime()
