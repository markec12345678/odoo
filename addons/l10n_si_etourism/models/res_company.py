# -*- coding: utf-8 -*-
"""Company extensions for eTurizem settings."""
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_si_etourism_environment = fields.Selection(
        selection=[('test', 'TEST'), ('prod', 'PROD')], string='SI eTurizem okolje', default='test',
    )
    l10n_si_etourism_auto_register = fields.Boolean(string='Samodejna prijava gostov', default=True)
    l10n_si_etourism_auto_deregister = fields.Boolean(string='Samodejna odjava gostov', default=True)
    l10n_si_etourism_notify_on_error = fields.Boolean(string='Obvesti ob napaki', default=True)
    l10n_si_etourism_notify_user_ids = fields.Many2many('res.users', string='Prejemniki obvestil o napakah')
