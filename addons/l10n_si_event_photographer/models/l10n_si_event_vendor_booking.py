# -*- coding: utf-8 -*-
"""Vendor booking - naročilo zunanjega izvajalca za konkreten dogodek."""
from odoo import api, fields, models


class L10nSiEventVendorBooking(models.Model):
    _name = 'l10n_si.event.vendor.booking'
    _description = 'Slovenian Event Vendor Booking'
    _inherit = ['mail.thread']
    _order = 'date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    event_id = fields.Many2one('l10n_si.event.event', required=True, ondelete='cascade')
    vendor_id = fields.Many2one('l10n_si.event.vendor', required=True, ondelete='restrict')
    company_id = fields.Many2one(related='event_id.company_id', store=True)

    # Kadar
    date = fields.Datetime(required=True, related='event_id.date_start', store=True)
    duration_hours = fields.Float(default=4.0, required=True)

    # Opis
    description = fields.Text(required=True, string='Kaj naj naredi')

    # Cena
    pricing_type = fields.Selection(
        selection=[('fixed', 'Fiksna cena'),
                   ('hourly', 'Urno'),
                   ('package', 'Paket')],
        default='fixed',
        required=True,
    )
    agreed_price = fields.Float(required=True, default=500.0)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Status
    state = fields.Selection(
        selection=[('inquiry', 'Povpraševanje'),
                   ('quoted', 'Ponudba prejeta'),
                   ('confirmed', 'Potrjeno'),
                   ('completed', 'Opravljeno'),
                   ('cancelled', 'Preklicano')],
        default='inquiry',
        tracking=True,
    )

    # Povezava z dobaviteljskim računom
    move_id = fields.Many2one('account.move', string='Račun dobavitelja', readonly=True, copy=False)

    # Notranje
    internal_notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.event.vendor.booking') or '/'
        return super().create(vals_list)

    @api.depends('pricing_type', 'agreed_price', 'duration_hours')
    def _compute_total(self):
        for b in self:
            if b.pricing_type == 'hourly':
                b.total_amount = b.agreed_price * b.duration_hours
            else:
                b.total_amount = b.agreed_price

    def action_send_inquiry(self):
        """Pošlji povpraševanje izvajalcu po e-pošti."""
        self.write({'state': 'quoted'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_complete(self):
        """Opravljeno - čakaj na račun dobavitelja."""
        self.write({'state': 'completed'})

    def action_create_vendor_bill(self):
        """Ustvari račun dobavitelja (vendor bill)."""
        Bill = self.env['account.move']
        for booking in self:
            if booking.move_id:
                continue
            move = Bill.create({
                'move_type': 'in_invoice',
                'partner_id': booking.vendor_id.partner_id.id,
                'invoice_date': fields.Date.today(),
                'company_id': booking.company_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': f'{booking.vendor_id.name} - {booking.event_id.name}',
                    'quantity': booking.duration_hours if booking.pricing_type == 'hourly' else 1,
                    'price_unit': booking.agreed_price,
                })],
            })
            booking.move_id = move.id

    def action_cancel(self):
        self.write({'state': 'cancelled'})
