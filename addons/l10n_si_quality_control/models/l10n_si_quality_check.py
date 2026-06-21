# -*- coding: utf-8 -*-
"""Quality check — one inspection of one product/operation."""
from odoo import api, fields, models


class L10nSiQualityCheck(models.Model):
    _name = 'l10n_si.quality.check'
    _description = 'Slovenian Quality Check'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(required=True, tracking=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    check_type = fields.Selection(
        selection=[('incoming', 'Sprejem (dobava)'),
                   ('in_process', 'Med proizvodnjo'),
                   ('final', 'Končni izdelek'),
                   ('audit', 'Revizijski pregled')],
        required=True,
        default='incoming',
    )

    # Linked document
    product_id = fields.Many2one('product.product', required=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serija')
    production_id = fields.Many2one('mrp.production', string='Proizvodni nalog')
    picking_id = fields.Many2one('stock.picking', string='Dobavnica')

    # Lines
    line_ids = fields.One2many('l10n_si.quality.check.line', 'check_id', string='Check Points')
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('in_progress', 'V postopku'),
                   ('pass', 'Sprejeto'),
                   ('fail', 'Zavrnjeno'),
                   ('partial', 'Delno sprejeto')],
        default='draft',
        tracking=True,
    )
    inspector_id = fields.Many2one('res.users', string='Inšpektor', default=lambda self: self.env.user)
    inspection_date = fields.Datetime(default=fields.Datetime.now)
    notes = fields.Text()

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.quality.check') or '/'
        return super().create(vals_list)

    def action_complete(self):
        """Mark check complete based on line results."""
        for check in self:
            if not check.line_ids:
                check.state = 'pass'
                continue
            all_pass = all(line.result == 'pass' for line in check.line_ids)
            any_fail = any(line.result == 'fail' for line in check.line_ids)
            if all_pass:
                check.state = 'pass'
            elif any_fail:
                check.state = 'fail'
                # Auto-create non-conformance
                check._create_nonconformance()
            else:
                check.state = 'partial'

    def _create_nonconformance(self):
        self.ensure_one()
        NCR = self.env['l10n_si.quality.nonconformance']
        failed_lines = self.line_ids.filtered(lambda l: l.result == 'fail')
        for line in failed_lines:
            NCR.create({
                'check_id': self.id,
                'product_id': self.product_id.id,
                'lot_id': self.lot_id.id if self.lot_id else False,
                'description': f'Neustreznost pri preverjanju: {line.name}',
                'severity': 'major' if line.critical else 'minor',
                'detected_by': self.env.user.id,
            })


class L10nSiQualityCheckLine(models.Model):
    _name = 'l10n_si.quality.check.line'
    _description = 'Slovenian Quality Check Line'

    check_id = fields.Many2one('l10n_si.quality.check', required=True, ondelete='cascade')
    name = fields.Char(required=True, string='Točka preverjanja')
    check_kind = fields.Selection(
        selection=[('pass_fail', 'Ustrezen/Neustrezen'),
                   ('numeric', 'Numerična vrednost'),
                   ('boolean', 'Da/Ne'),
                   ('text', 'Besedilo')],
        required=True,
        default='pass_fail',
    )

    # Numeric tolerance
    min_value = fields.Float(string='Min')
    max_value = fields.Float(string='Max')
    target_value = fields.Float(string='Cilj')

    # Result
    measured_value = fields.Float(string='Izmerjeno')
    measured_text = fields.Char(string='Izmerjeno (besedilo)')
    result = fields.Selection(
        selection=[('pass', 'Ustrezen'),
                   ('fail', 'Neustrezen'),
                   ('na', 'N/A')],
        default='na',
        required=True,
    )

    critical = fields.Boolean(
        string='Kritično',
        help='If critical and fails, NCR is auto-created.',
        default=False,
    )
    notes = fields.Text()
