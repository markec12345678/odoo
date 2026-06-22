# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    si_gdpr_consent_ids = fields.One2many('l10n_si.gdpr.consent', 'partner_id', string='GDPR soglasja')
    si_gdpr_request_ids = fields.One2many('l10n_si.gdpr.request', 'partner_id', string='GDPR zahteve')
    si_gdpr_data_erased = fields.Boolean(default=False, string='Podatki izbrisani (GDPR člen 17)')
    si_data_retention_until = fields.Date(string='Hramba do', help='Datum, do katerega lahko hranimo podatke.')
