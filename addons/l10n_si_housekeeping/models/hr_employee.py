# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    si_is_housekeeper = fields.Boolean(string='Hišnik', default=False)
    si_housekeeping_zone = fields.Char(string='Cona hišništva', help='npr. 1. nadstropje, krilo A')
    si_cleanings_today = fields.Integer(compute='_compute_today', store=False)
    si_cleanings_completed_today = fields.Integer(compute='_compute_today', store=False)

    def _compute_today(self):
        Task = self.env['l10n_si.housekeeping.task']
        today = fields.Date.today()
        for emp in self:
            tasks = Task.search([
                ('housekeeper_id', '=', emp.id),
                ('scheduled_date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                ('scheduled_date', '<=', today.strftime('%Y-%m-%d 23:59:59')),
            ])
            emp.si_cleanings_today = len(tasks)
            emp.si_cleanings_completed_today = len(tasks.filtered(lambda t: t.state == 'done'))
