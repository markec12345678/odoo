# -*- coding: utf-8 -*-
"""Loyalty member - one per partner."""
from odoo import api, fields, models


class L10nSiLoyaltyMember(models.Model):
    _name = 'l10n_si.loyalty.member'
    _description = 'Slovenian Loyalty Member'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Status
    state = fields.Selection(
        selection=[('active', 'Aktiven'),
                   ('paused', 'Pavziran'),
                   ('expired', 'Potekel'),
                   ('cancelled', 'Preklican')],
        default='active',
        tracking=True,
    )

    # Tier
    tier = fields.Selection(
        selection=[('bronze', 'Bronze'),
                   ('silver', 'Silver'),
                   ('gold', 'Gold'),
                   ('platinum', 'Platinum')],
        default='bronze',
        compute='_compute_tier', store=True,
        tracking=True,
    )
    tier_achieved_on = fields.Datetime(readonly=True, copy=False)

    # Points
    points_balance = fields.Integer(default=0, string='Stanje točk')
    points_total_earned = fields.Integer(default=0, string='Skupno pridobljeno')
    points_total_redeemed = fields.Integer(default=0, string='Skupno porabljeno')

    # Memberships dates
    joined_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    expires_on = fields.Date(readonly=True, copy=False)
    last_activity = fields.Datetime(readonly=True, copy=False)

    # Personal info
    birth_date = fields.Date(string='Birth Date')
    preferred_room_type_id = fields.Many2one('l10n_si.hotel.room.type')
    dietary_preferences = fields.Char(string='Dieta (alergije)')
    notes = fields.Text()

    # History
    transaction_ids = fields.One2many('l10n_si.loyalty.transaction', 'member_id', string='Transakcije')
    transaction_count = fields.Integer(compute='_compute_count', store=False)
    stay_count = fields.Integer(compute='_compute_count', store=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.loyalty.member') or '/'
        return super().create(vals_list)

    @api.depends('partner_id.name', 'number')
    def _compute_name(self):
        for m in self:
            m.name = f'{m.partner_id.name or "Gost"} ({m.number})'

    @api.depends('points_balance')
    def _compute_tier(self):
        tiers = [
            (20000, 'platinum'),
            (5000, 'gold'),
            (1000, 'silver'),
            (0, 'bronze'),
        ]
        for m in self:
            for threshold, tier_name in tiers:
                if m.points_balance >= threshold:
                    if m.tier != tier_name and m.tier:
                        m.tier_achieved_on = fields.Datetime.now()
                    m.tier = tier_name
                    break

    def _compute_count(self):
        for m in self:
            m.transaction_count = len(m.transaction_ids)
            # Stay count = number of folios
            m.stay_count = self.env['l10n_si.hotel.folio'].search_count([
                ('partner_id', '=', m.partner_id.id),
                ('state', '=', 'invoiced'),
            ])

    def add_points(self, points, source='stay', reference=False):
        """Add points to member (positive number)."""
        for m in self:
            self.env['l10n_si.loyalty.transaction'].create({
                'member_id': m.id,
                'points': points,
                'transaction_type': 'earned',
                'source': source,
                'reference': reference,
            })
            m.write({
                'points_balance': m.points_balance + points,
                'points_total_earned': m.points_total_earned + points,
                'last_activity': fields.Datetime.now(),
            })

    def redeem_points(self, points, reward_id=False):
        """Redeem points (negative number)."""
        for m in self:
            if m.points_balance < points:
                return False
            self.env['l10n_si.loyalty.transaction'].create({
                'member_id': m.id,
                'points': -points,
                'transaction_type': 'redeemed',
                'reward_id': reward_id,
            })
            m.write({
                'points_balance': m.points_balance - points,
                'points_total_redeemed': m.points_total_redeemed + points,
                'last_activity': fields.Datetime.now(),
            })
            return True

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_activate(self):
        self.write({'state': 'active'})


class L10nSiLoyaltyTransaction(models.Model):
    _name = 'l10n_si.loyalty.transaction'
    _description = 'Slovenian Loyalty Transaction'
    _order = 'create_date DESC'

    member_id = fields.Many2one('l10n_si.loyalty.member', required=True, ondelete='cascade')
    points = fields.Integer(required=True, help='Pozitivno za pridobitev, negativno za porabo.')
    transaction_type = fields.Selection(
        selection=[('earned', 'Pridobljeno'),
                   ('redeemed', 'Porabljeno'),
                   ('adjusted', 'Popravek'),
                   ('expired', 'Poteklo')],
        required=True,
    )
    source = fields.Selection(
        selection=[('stay', 'Bivanje'),
                   ('dining', 'Prehrana'),
                   ('wellness', 'Wellness'),
                   ('event', 'Dogodek'),
                   ('referral', 'Priporočilo'),
                   ('bonus', 'Bonus'),
                   ('reward', 'Nagrada')],
        default='stay',
    )
    reference = fields.Char(string='Sklic (npr. folio št.)')
    reward_id = fields.Many2one('l10n_si.loyalty.reward', string='Nagrada')
    notes = fields.Text()
    create_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
