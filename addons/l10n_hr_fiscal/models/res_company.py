# -*- coding: utf-8 -*-
"""Croatian company extensions for Fiskalizacija configuration."""
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    hr_fiscal_enabled = fields.Boolean(string='Fiskalizacija omogućena', default=False)
    hr_fiscal_environment = fields.Selection(
        selection=[('demo', 'DEMO (cistest.apis-it.hr)'),
                   ('prod', 'PROD (cis.porezna-uprava.gov.hr)')],
        string='Okolina', default='demo', required=True,
    )
    hr_fiscal_certificate = fields.Binary(
        string='FINA certifikat (.pfx)', copy=False,
        help='FINA aplikativni certifikat za fiskalizaciju.',
    )
    hr_fiscal_certificate_password = fields.Char(string='Lozinka certifikata', copy=False)
    hr_fiscal_auto_submit = fields.Boolean(string='Automatsko slanje CISF-u', default=True)
    hr_fiscal_notify_on_error = fields.Boolean(string='Obavijest pri grešci', default=True)
    hr_fiscal_notify_user_ids = fields.Many2many('res.users', string='Primatelji obavijesti')
