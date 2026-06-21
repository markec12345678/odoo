# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class L10nSiReportWizardMixin(models.AbstractModel):
    """Common fields for all SI report wizards (year/month/company)."""
    _name = 'l10n_si.report.wizard.mixin'
    _description = 'SI Report Wizard Mixin'

    company_id = fields.Many2one(
        'res.company', string='Company',
        required=True, default=lambda self: self.env.company,
    )
    year = fields.Integer(
        string='Year',
        required=True,
        default=lambda self: fields.Date.today().year,
    )
    month = fields.Integer(
        string='Month (1-12)',
        default=lambda self: fields.Date.today().month,
    )
