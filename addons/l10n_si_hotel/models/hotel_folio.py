# -*- coding: utf-8 -*-
"""Hotel folio - main bill for a guest's stay."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HotelFolio(models.Model):
    """Folio - master bill that aggregates all charges for a stay.

    Lifecycle:
        draft → open → closed → invoiced
    """
    _name = 'l10n_si.hotel.folio'
    _description = 'Slovenian Hotel Folio'
    _inherit = ['mail.thread']
    _order = 'date_open DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Gost', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Dates
    date_open = fields.Datetime(default=fields.Datetime.now, readonly=True)
    date_close = fields.Datetime(readonly=True, copy=False)

    # Stay details
    check_in = fields.Datetime(required=True, default=fields.Datetime.now)
    check_out = fields.Datetime(required=True)
    adults = fields.Integer(default=2)
    children = fields.Integer(default=0)

    # Rooms assigned
    room_ids = fields.Many2many('l10n_si.hotel.room', string='Sobe')
    reservation_ids = fields.One2many('l10n_si.hotel.reservation', 'folio_id', string='Rezervacije')

    # Service charges
    service_line_ids = fields.One2many('l10n_si.hotel.folio.line', 'folio_id', string='Storitve')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('open', 'Odprt'),
                   ('closed', 'Zaključen'),
                   ('invoiced', 'Zaračunan'),
                   ('cancelled', 'Preklican')],
        default='draft',
        tracking=True,
    )

    # Accounting
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)
    amount_total = fields.Monetary(compute='_compute_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True, readonly=True,
    )

    # Notes
    notes = fields.Text()
    vip = fields.Boolean(default=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.hotel.folio') or '/'
        return super().create(vals_list)

    @api.depends('service_line_ids.subtotal', 'room_ids')
    def _compute_amount(self):
        for folio in self:
            total = sum(folio.service_line_ids.mapped('subtotal'))
            # Add room charges from linked reservations
            for res in folio.reservation_ids:
                total += res.total_amount
            folio.amount_total = total

    def action_open(self):
        """Open the folio - mark rooms as occupied."""
        for folio in self:
            folio.state = 'open'
            for room in folio.room_ids:
                room.write({
                    'state': 'occupied',
                    'current_folio_id': folio.id,
                })

    def action_close(self):
        """Close the folio on check-out. Rooms go to cleaning."""
        for folio in self:
            folio.write({
                'state': 'closed',
                'date_close': fields.Datetime.now(),
            })
            for room in folio.room_ids:
                room.write({
                    'state': 'cleaning',
                    'current_folio_id': False,
                })

    def action_create_invoice(self):
        """Generate invoice from folio and trigger FURS ZOI/EOR submission.

        Uses `l10n_si_fiscal` for davčno potrjevanje.
        """
        Invoice = self.env['account.move']
        for folio in self:
            if folio.move_id:
                continue
            if not folio.partner_id:
                raise UserError(_('Cannot invoice folio without a guest.'))

            lines = []
            # Room charges
            for res in folio.reservation_ids:
                lines.append((0, 0, {
                    'name': f'Soba {res.room_id.number} ({res.room_id.room_type_id.name}) - {res.nights} nočitev',
                    'quantity': res.nights,
                    'price_unit': res.daily_rate,
                    'tax_ids': [(6, 0, self._get_default_vat_tax_ids())],
                }))
            # Service charges
            for line in folio.service_line_ids:
                lines.append((0, 0, {
                    'name': line.service_id.name,
                    'quantity': line.quantity,
                    'price_unit': line.unit_price,
                    'tax_ids': [(6, 0, self._get_default_vat_tax_ids())],
                }))

            if not lines:
                raise UserError(_('Folio %s has no charges to invoice.') % folio.name)

            move = Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': folio.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_date_due': fields.Date.today(),
                'company_id': folio.company_id.id,
                'invoice_line_ids': lines,
                # SI sequence + fiscal premise come from l10n_si_sequence + l10n_si_fiscal
                # via overrides on account.move._post()
            })
            move.action_post()  # This triggers ZOI/EOR via l10n_si_fiscal
            folio.write({
                'move_id': move.id,
                'state': 'invoiced',
            })

    def _get_default_vat_tax_ids(self):
        """Return default 22% VAT tax for hotel services (room, minibar, etc.)."""
        Tax = self.env['account.tax']
        tax = Tax.search([
            ('amount', '=', 22.0),
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        return [tax.id] if tax else []

    def action_add_service(self):
        """Open wizard to add a service line to the folio."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Service'),
            'res_model': 'l10n_si.hotel.folio.service.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_folio_id': self.id},
        }


class HotelFolioLine(models.Model):
    _name = 'l10n_si.hotel.folio.line'
    _description = 'Slovenian Hotel Folio Line'

    folio_id = fields.Many2one('l10n_si.hotel.folio', required=True, ondelete='cascade')
    service_id = fields.Many2one('l10n_si.hotel.service', required=True, ondelete='restrict')
    description = fields.Char()
    quantity = fields.Float(default=1.0, required=True)
    unit_price = fields.Float(required=True, default=lambda self: self.service_id.default_price)
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='folio_id.currency_id')
    date = fields.Datetime(default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Sprejel', default=lambda self: self.env.user)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.unit_price = self.service_id.default_price
            self.description = self.service_id.name
