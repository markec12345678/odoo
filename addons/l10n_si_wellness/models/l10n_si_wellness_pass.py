# -*- coding: utf-8 -*-
"""Day pass za vstop v wellness (bazen, savne)."""
from odoo import api, fields, models


class L10nSiWellnessPass(models.Model):
    _name = 'l10n_si.wellness.pass'
    _description = 'Slovenian Wellness Day Pass'
    _inherit = ['mail.thread']
    _order = 'date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Gost (opcija)')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Tip karte
    pass_type = fields.Selection(
        selection=[('day', 'Dnevna karta'),
                   ('half_day', 'Pol dneh'),
                   ('morning', 'Jutranja (do 12h)'),
                   ('evening', 'Večerna (po 16h)'),
                   ('2h', '2-urna')],
        default='day',
        required=True,
    )

    # Datum veljavnosti
    date = fields.Date(required=True, default=fields.Date.today)
    valid_from = fields.Datetime()
    valid_to = fields.Datetime()

    # Gostje (koliko oseb)
    adults = fields.Integer(default=1, required=True)
    children_7_15 = fields.Integer(default=0, string='Otroci 7-15')
    children_0_6 = fields.Integer(default=0, string='Otroci 0-6 (brezplačno)')

    # Cena
    price_per_adult = fields.Float(default=25.0)
    price_per_child = fields.Float(default=12.5)
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('paid', 'Plačano'),
                   ('used', 'Uporabljeno'),
                   ('expired', 'Poteklo'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )

    # Povezave
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Povezani hotelski folio (opcija)')

    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.wellness.pass') or '/'
        return super().create(vals_list)

    @api.depends('adults', 'children_7_15', 'price_per_adult', 'price_per_child', 'pass_type')
    def _compute_total(self):
        multipliers = {'day': 1.0, 'half_day': 0.7, 'morning': 0.6, 'evening': 0.6, '2h': 0.4}
        for p in self:
            mult = multipliers.get(p.pass_type, 1.0)
            adult_total = p.adults * p.price_per_adult * mult
            child_total = p.children_7_15 * p.price_per_child * mult
            p.total_amount = adult_total + child_total

    def action_pay(self):
        """Ustvari in potrdi račun (FURS)."""
        for p in self:
            if not p.move_id:
                lines = [(0, 0, {
                    'name': f'Wellness {p.pass_type} - {p.date}',
                    'quantity': p.adults,
                    'price_unit': p.price_per_adult,
                })]
                if p.children_7_15 > 0:
                    lines.append((0, 0, {
                        'name': f'Wellness {p.pass_type} - otroci',
                        'quantity': p.children_7_15,
                        'price_unit': p.price_per_child,
                    }))
                move = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': p.partner_id.id if p.partner_id else False,
                    'invoice_date': fields.Date.today(),
                    'company_id': p.company_id.id,
                    'invoice_line_ids': lines,
                })
                move.action_post()  # FURS
                p.move_id = move.id
            p.state = 'paid'

    def action_mark_used(self):
        self.write({'state': 'used'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
