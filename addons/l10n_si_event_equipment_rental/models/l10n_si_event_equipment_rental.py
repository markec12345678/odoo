# -*- coding: utf-8 -*-
"""Rental = najem opreme za en dogodek, z več postavkami."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiEventEquipmentRental(models.Model):
    _name = 'l10n_si.event.equipment.rental'
    _description = 'Slovenian Event Equipment Rental'
    _inherit = ['mail.thread']
    _order = 'date_from DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    event_id = fields.Many2one('l10n_si.event.event', required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='event_id.partner_id', store=True)
    company_id = fields.Many2one(related='event_id.company_id', store=True)

    # Čas najema
    date_from = fields.Datetime(required=True, string='Od')
    date_to = fields.Datetime(required=True, string='Do')
    duration_hours = fields.Float(compute='_compute_duration', store=True)

    # Postavke
    line_ids = fields.One2many('l10n_si.event.equipment.rental.line', 'rental_id', string='Oprema')
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Tehnična podpora
    needs_technician = fields.Boolean(string='Tehnik na kraju', default=False)
    technician_id = fields.Many2one('hr.employee', string='Tehnik')
    technician_hours = fields.Float(default=4.0)
    technician_hourly_rate = fields.Float(default=25.0)
    technician_cost = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjen'),
                   ('in_progress', 'V izvedbi'),
                   ('returned', 'Vrnjeno'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )

    notes = fields.Text()
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.event.equipment.rental') or '/'
        return super().create(vals_list)

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for r in self:
            if r.date_from and r.date_to:
                r.duration_hours = (r.date_to - r.date_from).total_seconds() / 3600.0
            else:
                r.duration_hours = 0.0

    @api.depends('line_ids.subtotal', 'needs_technician', 'technician_hours', 'technician_hourly_rate')
    def _compute_total(self):
        for r in self:
            r.total_amount = sum(r.line_ids.mapped('subtotal'))
            r.technician_cost = (r.technician_hours * r.technician_hourly_rate) if r.needs_technician else 0.0
            r.total_amount += r.technician_cost

    def action_confirm(self):
        for r in self:
            # Validate availability
            for line in r.line_ids:
                if not line.equipment_id.is_available(r.date_from, r.date_to, line.quantity, exclude_line_id=line.id):
                    raise ValidationError(_(
                        'Ni dovolj na zalogi: %(eq)s (potrebnih %(need)d, prostih manj)',
                        eq=line.equipment_id.name, need=line.quantity,
                    ))
            r.state = 'confirmed'

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_return(self):
        """Oprema vrnjena - izdaj račun."""
        for r in self:
            if not r.move_id:
                lines = []
                for line in r.line_ids:
                    lines.append((0, 0, {
                        'name': f'{line.equipment_id.name} - najem ({r.duration_hours:.1f}h)',
                        'quantity': line.quantity,
                        'price_unit': line.unit_price * r.duration_hours,
                    }))
                if r.needs_technician and r.technician_id:
                    lines.append((0, 0, {
                        'name': f'Tehnik: {r.technician_id.name}',
                        'quantity': r.technician_hours,
                        'price_unit': r.technician_hourly_rate,
                    }))
                if lines:
                    move = self.env['account.move'].create({
                        'move_type': 'out_invoice',
                        'partner_id': r.partner_id.id,
                        'invoice_date': fields.Date.today(),
                        'company_id': r.company_id.id,
                        'invoice_line_ids': lines,
                        'l10n_si_event_id': r.event_id.id,
                    })
                    move.action_post()  # FURS
                    r.move_id = move.id
            r.state = 'returned'

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class L10nSiEventEquipmentRentalLine(models.Model):
    _name = 'l10n_si.event.equipment.rental.line'
    _description = 'Slovenian Event Equipment Rental Line'

    rental_id = fields.Many2one('l10n_si.event.equipment.rental', required=True, ondelete='cascade')
    equipment_id = fields.Many2one('l10n_si.event.equipment', required=True, ondelete='restrict')
    quantity = fields.Integer(required=True, default=1)
    unit_price = fields.Float(required=True, default=lambda self: self.equipment_id.hourly_rate)
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='rental_id.currency_id', store=True)

    @api.depends('quantity', 'unit_price', 'rental_id.duration_hours')
    def _compute_subtotal(self):
        for line in self:
            hours = line.rental_id.duration_hours or 0
            line.subtotal = line.quantity * line.unit_price * hours

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        if self.equipment_id:
            self.unit_price = self.equipment_id.hourly_rate
