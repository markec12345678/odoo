# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    kpd_code_id = fields.Many2one(
        "l10n_hr.kpd.code",
        string="KPD (Klasus) Default",
        help="Default KPD code for products in this category.",
    )
