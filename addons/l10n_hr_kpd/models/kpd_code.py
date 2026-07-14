# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class KpdCode(models.Model):
    """Klasus (KPD) classification code — Croatian statistical product
    classification by activity.
    """
    _name = "l10n_hr.kpd.code"
    _description = "KPD (Klasus) Classification Code"
    _order = "code"
    _rec_name = "code"

    code = fields.Char(required=True, size=10)
    name = fields.Char(required=True, translate=True)
    name_hr = fields.Char(string="Name (HR)")
    description = fields.Text(translate=True)
    parent_id = fields.Many2one(
        "l10n_hr.kpd.code",
        string="Parent",
        ondelete="cascade",
    )
    child_ids = fields.One2many(
        "l10n_hr.kpd.code",
        "parent_id",
        string="Sub-categories",
    )
    level = fields.Integer(
        default=1,
        help="1=section, 2=division, 3=group, 4=class, 5=subclass",
    )
    active = fields.Boolean(default=True)
    is_service = fields.Boolean(
        default=False,
        help="True if this is a service (vs goods).",
    )

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "KPD code must be unique."),
    ]
