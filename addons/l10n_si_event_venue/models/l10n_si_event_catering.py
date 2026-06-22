# -*- coding: utf-8 -*-
"""Catering line - jed/pijača za dogodek z količino."""
from odoo import api, fields, models


class L10nSiEventCateringLine(models.Model):
    _name = 'l10n_si.event.catering.line'
    _description = 'Slovenian Event Catering Line'

    event_id = fields.Many2one('l10n_si.event.event', required=True, ondelete='cascade')
    menu_item_id = fields.Many2one('l10n_si.event.menu.item', required=True, ondelete='restrict')

    # Količina
    quantity = fields.Float(required=True, default=1.0,
                             help='Na osebo ali na enoto, odvisno od vrste.')
    quantity_type = fields.Selection(
        selection=[('per_person', 'Na osebo'),
                   ('per_unit', 'Na enoto (npr. torta, vino)')],
        default='per_person',
        required=True,
    )

    # Cena
    unit_price = fields.Float(required=True)
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='event_id.currency_id', store=True)

    # Diet
    notes = fields.Char(string='Opombe kuhinji (alergije, prilagoditve)')

    @api.depends('quantity', 'unit_price', 'quantity_type', 'event_id.expected_guests')
    def _compute_subtotal(self):
        for line in self:
            if line.quantity_type == 'per_person':
                # quantity = število oseb, ki jedo to jed
                line.subtotal = line.quantity * line.unit_price
            else:
                line.subtotal = line.quantity * line.unit_price

    @api.onchange('menu_item_id')
    def _onchange_menu_item_id(self):
        if self.menu_item_id:
            self.unit_price = self.menu_item_id.price_per_person or self.menu_item_id.price_per_unit
            # Default količina = število gostov na event-u
            if self.event_id and self.menu_item_id.price_per_person > 0:
                self.quantity = self.event_id.expected_guests
                self.quantity_type = 'per_person'
            else:
                self.quantity = 1
                self.quantity_type = 'per_unit'
