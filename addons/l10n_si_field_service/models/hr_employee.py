# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    si_is_technician = fields.Boolean(string='Tehnik (terenski)', default=False)
    si_skills = fields.Char(string='Veščine (CSV)', help='npr. klima, vodovodne, elektrika')
    si_default_zone = fields.Char(string='Privzeta cona')
    si_active_work_orders = fields.Integer(
        compute='_compute_active_orders', store=False,
    )

    def _compute_active_orders(self):
        Order = self.env['l10n_si.field.service.order']
        for emp in self:
            emp.si_active_work_orders = Order.search_count([
                ('technician_id', '=', emp.id),
                ('state', 'in', ['assigned', 'in_progress']),
            ])
