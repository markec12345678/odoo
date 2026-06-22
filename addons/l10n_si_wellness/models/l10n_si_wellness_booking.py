# -*- coding: utf-8 -*-
"""Booking - rezervacija termina za storitev."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nSiWellnessBooking(models.Model):
    _name = 'l10n_si.wellness.booking'
    _description = 'Slovenian Wellness Booking'
    _inherit = ['mail.thread']
    _order = 'date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    service_id = fields.Many2one('l10n_si.wellness.service', required=True, ondelete='restrict')
    partner_id = fields.Many2one('res.partner', string='Gost', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Termin
    date = fields.Datetime(required=True, default=fields.Datetime.now)
    duration_minutes = fields.Integer(related='service_id.duration_minutes', store=True)
    end_date = fields.Datetime(compute='_compute_end', store=True)

    # Cena
    guest_category = fields.Selection(
        selection=[('adult', 'Odrasli'),
                   ('child', 'Otroci 7-15'),
                   ('child_free', 'Otroci 0-6 (brezplačno)'),
                   ('senior', 'Seniorji 65+'),
                   ('student', 'Študenti')],
        default='adult',
        required=True,
    )
    price = fields.Float(required=True, default=40.0)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Terapevt (resource)
    therapist_employee_id = fields.Many2one('hr.employee', string='Terapevt')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjena'),
                   ('in_progress', 'V izvedbi'),
                   ('completed', 'Opravljena'),
                   ('cancelled', 'Preklicana'),
                   ('no_show', 'Ni prišel')],
        default='draft',
        tracking=True,
    )

    # Račun
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)

    # Povezava z dogodkom/hotelsko rezervacijo (optional)
    notes = fields.Text(string='Opombe (alergije, poškodbe)')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.wellness.booking') or '/'
        return super().create(vals_list)

    @api.depends('date', 'duration_minutes')
    def _compute_end(self):
        from datetime import timedelta
        for b in self:
            if b.date and b.duration_minutes:
                b.end_date = b.date + timedelta(minutes=b.duration_minutes)
            else:
                b.end_date = False

    @api.depends('price', 'guest_category', 'service_id')
    def _compute_total(self):
        for b in self:
            if b.guest_category == 'child_free':
                b.total_amount = 0.0
            else:
                b.total_amount = b.price

    @api.onchange('service_id', 'guest_category')
    def _onchange_service_or_category(self):
        if self.service_id:
            if self.guest_category == 'adult':
                self.price = self.service_id.price_adult
            elif self.guest_category == 'child':
                self.price = self.service_id.price_child
            elif self.guest_category == 'senior':
                self.price = self.service_id.price_senior
            elif self.guest_category == 'student':
                self.price = self.service_id.price_student
            else:
                self.price = 0.0

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        """Opravljeno - izdaj račun."""
        for b in self:
            if not b.move_id:
                move = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': b.partner_id.id,
                    'invoice_date': fields.Date.today(),
                    'company_id': b.company_id.id,
                    'invoice_line_ids': [(0, 0, {
                        'name': f'{b.service_id.name} ({b.duration_minutes}min) - {b.date}',
                        'quantity': 1,
                        'price_unit': b.price,
                    })],
                })
                move.action_post()  # FURS
                b.move_id = move.id
            b.state = 'completed'

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_no_show(self):
        self.write({'state': 'no_show'})
