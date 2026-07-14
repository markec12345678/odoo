# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class NkdCode(models.Model):
    """NKD 2007. (Croatian NACE Rev. 2) activity classification code.
    """
    _name = "l10n_hr.nkd.code"
    _description = "NKD Activity Code (Croatian NACE)"
    _order = "code"
    _rec_name = "code"

    code = fields.Char(required=True, size=6)
    name = fields.Char(required=True, translate=True)
    name_hr = fields.Char(string="Name (HR)")
    section = fields.Char(size=1, help="NKD section letter (A–U).")
    section_name = fields.Char()
    division = fields.Char(size=2)
    level = fields.Integer(
        default=5,
        help="1=section, 2=division, 3=group, 4=class, 5=subclass",
    )
    parent_id = fields.Many2one(
        "l10n_hr.nkd.code",
        string="Parent",
        ondelete="cascade",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "NKD code must be unique."),
    ]
