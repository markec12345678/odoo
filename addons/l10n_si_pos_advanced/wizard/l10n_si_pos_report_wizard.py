# -*- coding: utf-8 -*-
"""X-report and Z-report wizard for SI POS.

X-report: interim daily summary (does NOT close session)
Z-report: daily close (finalizes the day, prints totals)
"""
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nSiPosReportWizard(models.TransientModel):
    _name = 'l10n_si.pos.report.wizard'
    _description = 'SI POS X/Z Report Wizard'

    report_type = fields.Selection(
        selection=[('x_report', 'X-poročilo (meddnevno)'),
                   ('z_report', 'Z-poročilo (dnevni zaključek)')],
        required=True, default='x_report',
    )
    config_id = fields.Many2one('pos.config', string='POS blagajna')
    session_id = fields.Many2one('pos.session', string='POS seja')
    date_from = fields.Datetime(
        string='Od', required=True,
        default=lambda self: fields.Datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
    )
    date_to = fields.Datetime(string='Do', required=True, default=fields.Datetime.now)

    total_orders = fields.Integer(readonly=True)
    total_amount = fields.Monetary(readonly=True, currency_field='currency_id')
    total_vat = fields.Monetary(readonly=True, currency_field='currency_id')
    total_cash = fields.Monetary(readonly=True, currency_field='currency_id')
    total_card = fields.Monetary(readonly=True, currency_field='currency_id')
    total_other = fields.Monetary(readonly=True, currency_field='currency_id')
    total_tourist_tax = fields.Monetary(readonly=True, currency_field='currency_id')

    furs_pending_count = fields.Integer(readonly=True)
    furs_error_count = fields.Integer(readonly=True)
    furs_submitted_count = fields.Integer(readonly=True)
    vat_breakdown_html = fields.Html(readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)

    @api.onchange('session_id')
    def _onchange_session_id(self):
        if self.session_id:
            self.config_id = self.session_id.config_id
            self.date_from = self.session_id.start_at
            self.date_to = self.session_id.stop_at or fields.Datetime.now()

    def action_generate(self):
        self.ensure_one()
        domain = [('date_order', '>=', self.date_from), ('date_order', '<=', self.date_to)]
        if self.config_id:
            domain.append(('config_id', '=', self.config_id.id))
        if self.session_id:
            domain.append(('session_id', '=', self.session_id.id))

        orders = self.env['pos.order'].search(domain)
        total_amount = sum(orders.mapped('amount_total'))
        total_tourist_tax = sum(orders.mapped('l10n_si_tourist_tax_amount'))
        total_cash = total_card = total_other = 0.0

        vat_by_rate = defaultdict(lambda: {'base': 0.0, 'tax': 0.0})
        for order in orders:
            for line in order.lines:
                if hasattr(line, 'tax_ids') and line.tax_ids:
                    for tax in line.tax_ids:
                        if tax.amount_tax_domain == 'vat' and tax.amount:
                            rate = float(tax.amount)
                            base = line.price_subtotal
                            vat_by_rate[rate]['base'] += base
                            vat_by_rate[rate]['tax'] += base * (rate / 100.0)
            for payment in order.payment_ids:
                method = payment.payment_method_id
                name_lower = (method.name or '').lower() if method else ''
                if 'cash' in name_lower or 'gotov' in name_lower:
                    total_cash += payment.amount
                elif 'card' in name_lower or 'kart' in name_lower:
                    total_card += payment.amount
                else:
                    total_other += payment.amount

        total_vat = sum(v['tax'] for v in vat_by_rate.values())
        furs_pending = len(orders.filtered(lambda o: o.l10n_si_fiscal_state == 'pending'))
        furs_error = len(orders.filtered(lambda o: o.l10n_si_fiscal_state == 'error'))
        furs_submitted = len(orders.filtered(lambda o: o.l10n_si_fiscal_state == 'submitted'))

        vat_parts = ['<table class="table table-sm"><thead><tr><th>Stopa</th>'
                     '<th class="text-right">Osnovica</th><th class="text-right">DDV</th>'
                     '<th class="text-right">Skupaj</th></tr></thead><tbody>']
        for rate in sorted(vat_by_rate.keys()):
            v = vat_by_rate[rate]
            vat_parts.append(f'<tr><td>{rate:.1f}%</td><td class="text-right">{v["base"]:.2f}</td>'
                             f'<td class="text-right">{v["tax"]:.2f}</td>'
                             f'<td class="text-right">{v["base"] + v["tax"]:.2f}</td></tr>')
        vat_parts.append('</tbody></table>')

        currency = self.config_id.currency_id if self.config_id else self.env.company.currency_id
        self.write({
            'total_orders': len(orders), 'total_amount': total_amount, 'total_vat': total_vat,
            'total_cash': total_cash, 'total_card': total_card, 'total_other': total_other,
            'total_tourist_tax': total_tourist_tax,
            'furs_pending_count': furs_pending, 'furs_error_count': furs_error,
            'furs_submitted_count': furs_submitted, 'vat_breakdown_html': ''.join(vat_parts),
            'currency_id': currency.id if currency else False,
        })
        if self.report_type == 'z_report' and self.session_id:
            _logger.info('Z-report generated for session %s — %d orders, %.2f total',
                         self.session_id.name, len(orders), total_amount)
        return {
            'type': 'ir.actions.act_window',
            'name': _('X-poročilo') if self.report_type == 'x_report' else _('Z-poročilo'),
            'res_model': 'l10n_si.pos.report.wizard', 'res_id': self.id,
            'view_mode': 'form', 'target': 'new',
        }

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref('l10n_si_pos_advanced.action_report_pos_xz').report_action(self)

    def action_close_session(self):
        self.ensure_one()
        if self.report_type != 'z_report':
            raise UserError(_('Z-report is required to close a session.'))
        if not self.session_id:
            raise UserError(_('No session set.'))
        self.session_id.action_pos_session_closing_control()
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'title': _('Session closed'),
                           'message': _('Session %s has been closed.') % self.session_id.name,
                           'type': 'success'}}
