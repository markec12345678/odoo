# -*- coding: utf-8 -*-
from odoo import fields, models


class PosSession(models.Model):
    _inherit = 'pos.session'

    si_x_report_generated = fields.Boolean(default=False, copy=False)
    si_z_report_generated = fields.Boolean(default=False, copy=False)
    si_x_report_date = fields.Datetime(readonly=True, copy=False)
    si_z_report_date = fields.Datetime(readonly=True, copy=False)

    si_fiscal_count = fields.Integer(
        compute='_compute_si_stats', store=False,
        string='FURS računi',
    )
    si_fiscal_errors = fields.Integer(
        compute='_compute_si_stats', store=False,
        string='FURS napake',
    )

    def _compute_si_stats(self):
        for s in self:
            orders = self.env['pos.order'].search([('session_id', '=', s.id)])
            s.si_fiscal_count = len(orders.filtered(lambda o: o.l10n_si_eor))
            s.si_fiscal_errors = len(orders.filtered(lambda o: o.l10n_si_fiscal_state == 'error'))

    def action_generate_x_report(self):
        """X-poročilo - vmesni pregled prometa brez zaključka."""
        for s in self:
            s.write({
                'si_x_report_generated': True,
                'si_x_report_date': fields.Datetime.now(),
            })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/report/pdf/point_of_sale.report_saledetails/{self.id}',
            'target': 'self',
        }

    def action_generate_z_report(self):
        """Z-poročilo - dnevni zaključek POS."""
        for s in self:
            s.write({
                'si_z_report_generated': True,
                'si_z_report_date': fields.Datetime.now(),
            })
