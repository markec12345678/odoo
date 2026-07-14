# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    nkd_code_id = fields.Many2one(
        "l10n_hr.nkd.code",
        string="NKD Activity",
        help="Croatian national activity classification (NKD 2007.).",
    )
