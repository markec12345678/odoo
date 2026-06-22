# -*- coding: utf-8 -*-
"""KOT (Kitchen Order Ticket) - naročilo mize, ki gre v kuhinjo."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class L10nSiRestaurantKot(models.Model):
    """Kitchen Order Ticket - naročilo, ki gre v kuhinjo.

    Lifecycle:
        draft → sent_to_kitchen → preparing → ready → served → invoiced
    """
    _name = 'l10n_si.restaurant.kot'
    _description = 'Slovenian Restaurant KOT'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    table_id = fields.Many2one('l10n_si.restaurant.table', required=True, ondelete='restrict')
    waiter_id = fields.Many2one('res.users', string='Natakar', default=lambda self: self.env.user, required=True)
    guests = fields.Integer(string='Gostje', default=2, required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    line_ids = fields.One2many('l10n_si.restaurant.kot.line', 'kot_id', string='Postavke')
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('sent', 'Poslano v kuhinjo'),
                   ('preparing', 'V pripravi'),
                   ('ready', 'Pripravljeno'),
                   ('served', 'Postreženo'),
                   ('invoiced', 'Zaračunano'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )

    # Accounting
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)
    amount_total = fields.Monetary(compute='_compute_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    notes = fields.Text(string='Opombe za kuhinjo')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.restaurant.kot') or '/'
        return super().create(vals_list)

    @api.depends('line_ids.subtotal')
    def _compute_amount(self):
        for kot in self:
            kot.amount_total = sum(kot.line_ids.mapped('subtotal'))

    def action_send_to_kitchen(self):
        """Pošlje naročilo v kuhinjo — tiskalna postaja vidi vse 'sent' KOT."""
        for kot in self:
            kot.state = 'sent'
            kot.table_id.state = 'occupied'
            kot.table_id.current_kot_id = kot.id

    def action_start_preparing(self):
        self.write({'state': 'preparing'})

    def action_mark_ready(self):
        """Kuhinja označi, da so jedi pripravljene za postrežbo."""
        self.write({'state': 'ready'})

    def action_served(self):
        """Natakar označi, da so jedi postrežene."""
        self.write({'state': 'served'})

    def action_create_invoice(self):
        """Generiraj račun iz KOT in sproži FURS davčno potrjevanje."""
        Invoice = self.env['account.move']
        for kot in self:
            if kot.move_id:
                continue
            if not kot.line_ids:
                raise UserError(_('KOT %s nima postavk.') % kot.name)

            lines = []
            for line in kot.line_ids:
                lines.append((0, 0, {
                    'product_id': line.menu_id.product_id.id,
                    'name': line.menu_id.name,
                    'quantity': line.quantity,
                    'price_unit': line.unit_price,
                }))

            move = Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': kot.partner_id.id if kot.partner_id else False,
                'invoice_date': fields.Date.today(),
                'company_id': kot.company_id.id,
                'invoice_line_ids': lines,
            })
            move.action_post()  # Triggers ZOI/EOR via l10n_si_fiscal
            kot.write({'move_id': move.id, 'state': 'invoiced'})
            kot.table_id.action_cleaning()

    # partner_id needed for invoice - add as field
    partner_id = fields.Many2one('res.partner', string='Gost (opcija)')


class L10nSiRestaurantKotLine(models.Model):
    _name = 'l10n_si.restaurant.kot.line'
    _description = 'Slovenian Restaurant KOT Line'

    kot_id = fields.Many2one('l10n_si.restaurant.kot', required=True, ondelete='cascade')
    menu_id = fields.Many2one('l10n_si.restaurant.menu', required=True, ondelete='restrict')
    quantity = fields.Float(default=1.0, required=True)
    unit_price = fields.Float(required=True)
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='kot_id.currency_id')
    notes = fields.Char(string='Opombe kuhinji', help='Npr. "brez čebule", "dobro pečeno"')
    state = fields.Selection(
        selection=[('ordered', 'Naročeno'),
                   ('preparing', 'V pripravi'),
                   ('ready', 'Pripravljeno'),
                   ('served', 'Postreženo'),
                   ('cancelled', 'Preklicano')],
        default='ordered',
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('menu_id')
    def _onchange_menu_id(self):
        if self.menu_id:
            self.unit_price = self.menu_id.price
