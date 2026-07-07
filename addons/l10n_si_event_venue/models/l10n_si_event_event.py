# -*- coding: utf-8 -*-
"""Event = konkreten dogodek (poroka, konferenca)."""
from odoo import _, api, fields, models


class L10nSiEventEvent(models.Model):
    """Dogodek = konkretna prireditev.

    Povezan je z eno ali več rezervacij dvoran (booking_ids).
    Ena rezervacija = ena dvorana v enem časovnem oknu.
    Za več dvoran ali več dni - več rezervacij vezanih na isti event.
    """
    _name = 'l10n_si.event.event'
    _description = 'Slovenian Event'
    _inherit = ['mail.thread']
    _order = 'date_start DESC'

    name = fields.Char(required=True, tracking=True, translate=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Vrsta dogodka
    event_type = fields.Selection(
        selection=[('wedding', 'Poroka'),
                   ('conference', 'Konferenca'),
                   ('business_meeting', 'Poslovni sestanek'),
                   ('birthday', 'Rojsni dan'),
                   ('anniversary', 'Obletnica'),
                   ('gala', 'Gala večer'),
                   ('cultural', 'Kulturni dogodek'),
                   ('sport', 'Športni dogodek'),
                   ('other', 'Drugo')],
        default='conference',
        required=True,
        tracking=True,
    )

    # Stranka
    partner_id = fields.Many2one(
        'res.partner', string='Stranka', required=True, tracking=True,
        help='Oseba/organizacija, ki naroča dogodek.',
    )
    contact_name = fields.Char(string='Oseba za kontakt')
    contact_phone = fields.Char()
    contact_email = fields.Char()

    # Lokacija
    venue_id = fields.Many2one('l10n_si.event.venue', required=True, tracking=True)
    hall_ids = fields.Many2many('l10n_si.event.hall', string='Dvorane')

    # Čas
    date_start = fields.Datetime(string='Začetek', required=True, default=fields.Datetime.now)
    date_end = fields.Datetime(string='Konec', required=True)
    setup_start = fields.Datetime(string='Začetek priprave',
                                    help='Kdaj začnemo pripravljati dvorano (pred dogodkom).')
    teardown_end = fields.Datetime(string='Konec razstavitve',
                                     help='Kdaj končamo razstavljanje (po dogodku).')

    # Gostje
    expected_guests = fields.Integer(string='Pričakovano gostov', default=50, required=True)
    confirmed_guests = fields.Integer(string='Potrjeno gostov', default=0)
    actual_guests = fields.Integer(string='Dejansko gostov', default=0)

    # Paket
    package_id = fields.Many2one('l10n_si.event.package', string='Paket')
    package_price = fields.Float(related='package_id.base_price', store=False)

    # Status
    state = fields.Selection(
        selection=[('inquiry', 'Povpraševanje'),
                   ('quoted', 'Ponudba poslana'),
                   ('confirmed', 'Potrjeno'),
                   ('deposit_paid', 'Avans plačan'),
                   ('in_progress', 'V izvedbi'),
                   ('completed_pending', 'Opravljeno - čaka račun'),
                   ('completed', 'Zaključeno'),
                   ('cancelled', 'Preklicano')],
        default='inquiry',
        tracking=True,
    )

    # Opis
    description = fields.Html()
    special_requests = fields.Text(string='Posebne želje stranke')
    internal_notes = fields.Text(string='Interne opombe')

    # Povezave
    booking_ids = fields.One2many('l10n_si.event.booking', 'event_id', string='Rezervacije dvoran')
    catering_line_ids = fields.One2many('l10n_si.event.catering.line', 'event_id', string='Catering')
    invoice_ids = fields.One2many('account.move', 'l10n_si_event_id', string='Računi')
    invoice_count = fields.Integer(compute='_compute_invoice_count', store=False)

    # Cene
    hall_total = fields.Monetary(compute='_compute_totals', store=True, currency_field='currency_id',
                                   string='Vrednost dvoran')
    catering_total = fields.Monetary(compute='_compute_totals', store=True, currency_field='currency_id',
                                      string='Vrednost cateringa')
    extras_total = fields.Monetary(compute='_compute_totals', store=True, currency_field='currency_id',
                                    string='Dodatne storitve')
    total_amount = fields.Monetary(compute='_compute_totals', store=True, currency_field='currency_id',
                                    string='Skupaj')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.event.event') or '/'
        return super().create(vals_list)

    @api.depends('booking_ids', 'catering_line_ids', 'package_id')
    def _compute_totals(self):
        for ev in self:
            ev.hall_total = sum(ev.booking_ids.mapped('total_amount'))
            ev.catering_total = sum(ev.catering_line_ids.mapped('subtotal'))
            # Extras: package extras + custom additions
            ev.extras_total = 0.0  # placeholder for additional services
            ev.total_amount = ev.hall_total + ev.catering_total + ev.extras_total
            if ev.package_id:
                ev.total_amount += ev.package_id.base_price

    def _compute_invoice_count(self):
        for ev in self:
            ev.invoice_count = len(ev.invoice_ids)

    # Workflow akcije
    def action_send_quote(self):
        """Pošlji ponudbo stranki."""
        self.write({'state': 'quoted'})

    def action_confirm(self):
        """Stranka je potrdila dogodek - rezerviraj dvorane."""
        for ev in self:
            ev.state = 'confirmed'
            for hall in ev.hall_ids:
                hall.state = 'booked'

    def action_register_deposit(self):
        """Zabeleži prejetje avansa."""
        self.write({'state': 'deposit_paid'})

    def action_start(self):
        """Dogodek se začne."""
        self.write({'state': 'in_progress'})

    def action_complete_pending(self):
        """Dogodek končan, čaka na končni račun."""
        self.write({'state': 'completed_pending'})
        for ev in self:
            for hall in ev.hall_ids:
                hall.state = 'available'

    def action_create_final_invoice(self):
        """Ustvari končni račun iz vseh postavk dogodka."""
        Invoice = self.env['account.move']
        for ev in self:
            lines = []
            # Paket
            if ev.package_id:
                lines.append((0, 0, {
                    'name': f'Paket: {ev.package_id.name}',
                    'quantity': 1,
                    'price_unit': ev.package_id.base_price,
                }))
            # Dvorane
            for booking in ev.booking_ids:
                lines.append((0, 0, {
                    'name': f'{booking.hall_id.name} - najem ({booking.duration_hours:.1f}h)',
                    'quantity': 1,
                    'price_unit': booking.total_amount,
                }))
            # Catering
            for cat in ev.catering_line_ids:
                lines.append((0, 0, {
                    'name': cat.menu_item_id.name,
                    'quantity': cat.quantity,
                    'price_unit': cat.unit_price,
                }))
            if not lines:
                continue
            invoice = Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': ev.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_date_due': fields.Date.today(),
                'company_id': ev.company_id.id,
                'invoice_line_ids': lines,
                'l10n_si_event_id': ev.id,
            })
            invoice.action_post()  # FURS ZOI/EOR via l10n_si_fiscal
        self.write({'state': 'completed'})

    def action_cancel(self):
        """Prekliči dogodek in sprosti dvorane."""
        for ev in self:
            ev.state = 'cancelled'
            for hall in ev.hall_ids:
                if hall.state == 'booked':
                    hall.state = 'available'

    def action_view_invoices(self):
        """Open the invoices view filtered by this event."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Računi'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('l10n_si_event_id', '=', self.id)],
            'context': {
                'default_l10n_si_event_id': self.id,
                'default_move_type': 'out_invoice',
            },
        }


# Add backref on account.move
class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_si_event_id = fields.Many2one(
        'l10n_si.event.event', string='Event', copy=False,
        help='Event that generated this invoice.',
    )
