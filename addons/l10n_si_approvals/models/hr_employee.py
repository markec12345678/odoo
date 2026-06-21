# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    si_can_approve = fields.Boolean(string='Lahko odobrava', default=False)
    si_approval_limit = fields.Float(
        string='Odobritveni limit (€)',
        default=0.0,
        help='Maximum amount this employee can approve in one request.',
    )
    si_approver_for_categories = fields.Char(
        string='Odobrava kategorije',
        help='Comma-separated: leaves,purchases,expenses,travel,vehicle',
    )
    si_delegate_to_id = fields.Many2one(
        'hr.employee', string='Delegira na (med odsotnostjo)',
        help='When this employee is absent, all approvals are routed here.',
    )
