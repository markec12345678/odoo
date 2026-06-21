# -*- coding: utf-8 -*-
"""Non-conformance report (NCR) + Corrective and Preventive Action (CAPA)."""
from odoo import api, fields, models


class L10nSiQualityNonconformance(models.Model):
    _name = 'l10n_si.quality.nonconformance'
    _description = 'Slovenian Non-Conformance Report'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')

    # Origin
    check_id = fields.Many2one('l10n_si.quality.check', string='Quality Check')
    product_id = fields.Many2one('product.product', required=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serija')
    production_id = fields.Many2one('mrp.production', string='Proizvodni nalog')
    picking_id = fields.Many2one('stock.picking', string='Dobavnica')

    # Description
    description = fields.Html(required=True)
    severity = fields.Selection(
        selection=[('minor', 'Manjša'),
                   ('major', 'Večja'),
                   ('critical', 'Kritična')],
        default='minor',
        required=True,
        tracking=True,
    )
    category = fields.Selection(
        selection=[('dimension', 'Dimenzija'),
                   ('surface', 'Površina'),
                   ('function', 'Funkcija'),
                   ('documentation', 'Dokumentacija'),
                   ('packaging', 'Pakiranje'),
                   ('other', 'Drugo')],
        default='other',
    )

    # Workflow
    state = fields.Selection(
        selection=[('open', 'Odprta'),
                   ('investigation', 'V preiskavi'),
                   ('action', 'CAPA v teku'),
                   ('verified', 'Preverjeno'),
                   ('closed', 'Zaprto')],
        default='open',
        tracking=True,
    )

    # People
    detected_by = fields.Many2one('res.users', string='Zaznal', default=lambda self: self.env.user)
    detected_on = fields.Datetime(default=fields.Datetime.now)
    responsible_id = fields.Many2one('res.users', string='Odgovorni', tracking=True)

    # CAPA
    root_cause = fields.Text(string='Vzrok')
    corrective_action = fields.Text(string='Korektivni ukrep')
    preventive_action = fields.Text(string='Preventivni ukrep')
    action_deadline = fields.Date(string='Rok ukrepanja')
    verified_by = fields.Many2one('res.users', string='Preveril', readonly=True)
    verified_on = fields.Datetime(readonly=True)

    # Quantity
    quantity_rejected = fields.Float(string='Količina zavrnjena', default=0.0)
    disposition = fields.Selection(
        selection=[('rework', 'Predelava'),
                   ('scrap', 'Odpis'),
                   ('accept', 'Sprejmi z odstopanjem'),
                   ('return', 'Vrni dobavitelju')],
        default='rework',
    )

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.quality.nonconformance') or '/'
        return super().create(vals_list)

    @api.depends('number', 'product_id')
    def _compute_name(self):
        for ncr in self:
            ncr.name = f'{ncr.number} - {ncr.product_id.name or ""}'

    def action_investigate(self):
        self.write({'state': 'investigation'})

    def action_implement(self):
        self.write({'state': 'action'})

    def action_verify(self):
        for ncr in self:
            ncr.write({
                'state': 'verified',
                'verified_by': self.env.user.id,
                'verified_on': fields.Datetime.now(),
            })

    def action_close(self):
        self.write({'state': 'closed'})
