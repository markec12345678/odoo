# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_approval_sla_days = fields.Integer(
        string='SLA odobritev (dnevi)',
        default=3,
        help='After N days, pending approvals are escalated to the next level.',
    )
    si_approval_auto_remind = fields.Boolean(
        string='Avtomatski opomniki',
        default=True,
        help='Send reminder email every day when approval is pending.',
    )
