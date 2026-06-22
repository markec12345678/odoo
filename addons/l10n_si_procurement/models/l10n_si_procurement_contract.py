# -*- coding: utf-8 -*-
"""Procurement contract - letna okvirna pogodba z dobaviteljem."""
from odoo import api, fields, models


class L10nSiProcurementContract(models.Model):
    _name = 'l10n_si.procurement.contract'
    _description = 'Slovenian Procurement Contract'
    _inherit = ['mail.thread']
    _order = 'date_from DESC'

    name = fields.Char(required=True, tracking=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    vendor_id = fields.Many2one('l10n_si.procurement.vendor', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Čas
    date_from = fields.Date(required=True, default=fields.Date.today)
    date_to = fields.Date(required=True)
    is_active = fields.Boolean(compute='_compute_active', store=False)

    # Vrednost
    contract_value = fields.Monetary(required=True, default=10000.0,
                                       string='Vrednost pogodbe (EUR)')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    used_value = fields.Monetary(compute='_compute_used', store=False,
                                   string='Porabljena vrednost (EUR)')
    remaining_value = fields.Monetary(compute='_compute_used', store=False,
                                        string='Preostala vrednost (EUR)')

    # Pogoji
    payment_terms_days = fields.Integer(default=30, string='Plačilo v (dneh)')
    discount_percent = fields.Float(default=10.0, string='Popust (%)')
    free_delivery = fields.Boolean(default=True, string='Brezplačna dostava')
    delivery_time_days = fields.Integer(default=2, string='Doba dobave')

    # Opis
    description = fields.Text()
    pdf_attachment_id = fields.Many2one('ir.attachment', string='Pogodba (PDF)')

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('active', 'Aktivna'),
                   ('expired', 'Potekla'),
                   ('terminated', 'Prekinjena')],
        default='draft',
        tracking=True,
    )

    # Povezani naročila
    purchase_order_ids = fields.One2many('purchase.order', 'l10n_si_contract_id', string='Naročila')
    po_count = fields.Integer(compute='_compute_used', store=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.procurement.contract') or '/'
        return super().create(vals_list)

    def _compute_active(self):
        today = fields.Date.today()
        for c in self:
            c.is_active = c.date_from <= today <= c.date_to and c.state == 'active'

    def _compute_used(self):
        for c in self:
            pos = c.purchase_order_ids.filtered(lambda p: p.state in ['purchase', 'done'])
            c.used_value = sum(pos.mapped('amount_total'))
            c.remaining_value = c.contract_value - c.used_value
            c.po_count = len(c.purchase_order_ids)

    def action_activate(self):
        self.write({'state': 'active'})

    def action_terminate(self):
        self.write({'state': 'terminated'})


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    l10n_si_contract_id = fields.Many2one('l10n_si.procurement.contract', string='Pogodba (SI Procurement)')
