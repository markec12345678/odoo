# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    kpd_code_id = fields.Many2one(
        "l10n_hr.kpd.code",
        string="KPD (Klasus)",
        help="Croatian statistical product classification.",
    )
