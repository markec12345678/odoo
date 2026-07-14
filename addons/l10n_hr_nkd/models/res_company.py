# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    nkd_code_id = fields.Many2one(
        "l10n_hr.nkd.code",
        string="NKD Activity",
        help="Company's registered activity (NKD 2007.).",
    )
