# -*- coding: utf-8 -*-
"""eVisitor audit log — every API call is logged for statutory retention."""
from odoo import fields, models


class L10nHrEvisitorLog(models.Model):
    _name = 'l10n_hr.evisitor.log'
    _description = 'Croatian eVisitor API Audit Log'
    _order = 'submitted_at DESC'

    registration_id = fields.Many2one(
        'l10n_hr.evisitor.guest.registration',
        string='Prijava gosta', ondelete='restrict',
    )
    accommodation_id = fields.Many2one(
        'l10n_hr.evisitor.accommodation', string='Smještaj', ondelete='restrict',
    )
    company_id = fields.Many2one(
        'res.company', string='Tvrtka',
        default=lambda self: self.env.company, required=True,
    )
    request_type = fields.Selection(
        selection=[('check_in', 'Prijava gosta (CheckIn)'),
                   ('check_out', 'Odjava gosta (CheckOut)'),
                   ('tourist_tax', 'Obračun boravišne pristojbe'),
                   ('list_countries', 'Popis država'),
                   ('ping', 'Provjera povezanosti')],
        required=True,
    )
    submitted_at = fields.Datetime(
        string='Vrijeme slanja', default=fields.Datetime.now, required=True,
    )
    duration_ms = fields.Integer(string='Trajanje (ms)')
    request_payload = fields.Text(string='Zahtjev (JSON)')
    response_payload = fields.Text(string='Odgovor (JSON)')
    http_status = fields.Integer(string='HTTP status')
    state = fields.Selection(
        selection=[('draft', 'Nacrt'),
                   ('pending', 'U obradi'),
                   ('sent', 'Poslano'),
                   ('error', 'Greška')],
        string='Status', default='draft', required=True,
    )
    error_message = fields.Text(string='Poruka greške')
    evisitor_submission_id = fields.Char(
        string='eVisitor checkInId', readonly=True,
    )
    next_retry = fields.Datetime(string='Sljedeći pokušaj')
    retry_count = fields.Integer(string='Broj pokušaja', default=0)
