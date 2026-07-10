# -*- coding: utf-8 -*-
"""Marketing campaign + steps + participant records."""
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval


class L10nSiMarketingCampaign(models.Model):
    _name = 'l10n_si.marketing.campaign'
    _description = 'Slovenian Marketing Campaign'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Trigger
    trigger = fields.Selection(
        selection=[('manual', 'Ročno'),
                   ('signup', 'Ob registraciji'),
                   ('abandoned_cart', 'Opuščen voziček'),
                   ('birthday', 'Rojstni dan'),
                   ('no_purchase_30', 'Brez nakupa 30 dni'),
                   ('no_purchase_90', 'Brez nakupa 90 dni'),
                   ('custom', 'Custom event')],
        default='manual',
        required=True,
    )

    # Audience
    domain = fields.Char(
        string='Filter partners',
        default='[]',
        help='Domain filter for which partners this campaign applies.',
    )

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('running', 'V teku'),
                   ('paused', 'Pavzirana'),
                   ('completed', 'Zaključena')],
        default='draft',
        tracking=True,
    )

    # Stats
    participant_count = fields.Integer(compute='_compute_stats', store=False)
    sent_count = fields.Integer(compute='_compute_stats', store=False)
    open_count = fields.Integer(compute='_compute_stats', store=False)
    click_count = fields.Integer(compute='_compute_stats', store=False)

    step_ids = fields.One2many(
        'l10n_si.marketing.campaign.step', 'campaign_id', string='Steps',
    )
    participant_ids = fields.One2many(
        'l10n_si.marketing.campaign.participant', 'campaign_id', string='Participants',
    )

    def _compute_stats(self):
        for camp in self:
            camp.participant_count = len(camp.participant_ids)
            camp.sent_count = sum(camp.participant_ids.mapped('email_sent_count'))
            camp.open_count = sum(camp.participant_ids.mapped('email_open_count'))
            camp.click_count = sum(camp.participant_ids.mapped('email_click_count'))

    def action_start(self):
        self.write({'state': 'running'})

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_add_participants(self):
        """Add partners matching the campaign domain."""
        for camp in self:
            domain = safe_eval(camp.domain or '[]')
            partners = self.env['res.partner'].search(domain)
            for partner in partners:
                if not partner.email:
                    continue
                existing = self.env['l10n_si.marketing.campaign.participant'].search([
                    ('campaign_id', '=', camp.id),
                    ('partner_id', '=', partner.id),
                ])
                if not existing:
                    self.env['l10n_si.marketing.campaign.participant'].create({
                        'campaign_id': camp.id,
                        'partner_id': partner.id,
                    })

    @api.model
    def _cron_process_campaigns(self):
        """Daily: advance each participant to the next step."""
        for camp in self.search([('state', '=', 'running')]):
            for participant in camp.participant_ids.filtered(lambda p: p.state == 'active'):
                participant._advance_to_next_step()


class L10nSiMarketingCampaignStep(models.Model):
    _name = 'l10n_si.marketing.campaign.step'
    _description = 'Slovenian Marketing Campaign Step'
    _order = 'sequence, id'

    campaign_id = fields.Many2one('l10n_si.marketing.campaign', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10, required=True)
    name = fields.Char(required=True)

    action_type = fields.Selection(
        selection=[('email', 'Pošlji email'),
                   ('wait', 'Čakaj'),
                   ('condition', 'Pogoj'),
                   ('tag', 'Dodaj tag'),
                   ('end', 'Konec')],
        required=True,
        default='email',
    )

    # Email action
    template_id = fields.Many2one('mail.template', string='Email template')

    # Wait action
    wait_days = fields.Integer(default=1)

    # Condition action
    condition_field = fields.Selection(
        selection=[('country_id', 'Država'),
                   ('total_spent', 'Skupna poraba'),
                   ('last_purchase_date', 'Zadnji nakup'),
                   ('tag_ids', 'Tags')],
        string='Pogoj polje',
    )
    condition_op = fields.Selection(
        selection=[('=', '='),
                   ('!=', '!='),
                   ('>', '>'),
                   ('<', '<'),
                   ('in', 'vsebuje'),
                   ('not_in', 'ne vsebuje')],
        string='Operator',
    )
    condition_value = fields.Char(string='Vrednost')

    # Branch
    next_step_if_true = fields.Many2one('l10n_si.marketing.campaign.step', string='Naslednji (true)')
    next_step_if_false = fields.Many2one('l10n_si.marketing.campaign.step', string='Naslednji (false)')


class L10nSiMarketingCampaignParticipant(models.Model):
    _name = 'l10n_si.marketing.campaign.participant'
    _description = 'Slovenian Marketing Campaign Participant'

    campaign_id = fields.Many2one('l10n_si.marketing.campaign', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')

    state = fields.Selection(
        selection=[('active', 'Aktiven'),
                   ('completed', 'Zaključen'),
                   ('unsubscribed', 'Odjavljen'),
                   ('bounced', 'Bounce')],
        default='active',
    )
    current_step_id = fields.Many2one('l10n_si.marketing.campaign.step')
    next_action_date = fields.Datetime(default=fields.Datetime.now)

    email_sent_count = fields.Integer(default=0)
    email_open_count = fields.Integer(default=0)
    email_click_count = fields.Integer(default=0)

    added_on = fields.Datetime(default=fields.Datetime.now)
    completed_on = fields.Datetime(readonly=True)

    def _advance_to_next_step(self):
        """Process the current step for this participant."""
        for p in self:
            if p.state != 'active':
                continue
            if fields.Datetime.now() < p.next_action_date:
                continue

            step = p.current_step_id or p.campaign_id.step_ids[:1]
            if not step:
                p.write({'state': 'completed', 'completed_on': fields.Datetime.now()})
                continue

            if step.action_type == 'email':
                if step.template_id and p.partner_id.email:
                    step.template_id.send_mail(p.partner_id.id, force_send=False)
                    p.email_sent_count += 1
                p._next_step(step)

            elif step.action_type == 'wait':
                p.next_action_date = fields.Datetime.now() + timedelta(days=step.wait_days)
                p.current_step_id = step.id  # Will be advanced next time

            elif step.action_type == 'condition':
                # Evaluate condition — simplified
                next_step = step.next_step_if_true if p._evaluate_condition(step) else step.next_step_if_false
                p.current_step_id = next_step.id if next_step else False

            elif step.action_type == 'tag':
                # Add tag to partner (placeholder)
                p._next_step(step)

            elif step.action_type == 'end':
                p.write({'state': 'completed', 'completed_on': fields.Datetime.now()})

    def _next_step(self, current_step):
        """Move to the next step in sequence."""
        self.ensure_one()
        next_step = self.env['l10n_si.marketing.campaign.step'].search([
            ('campaign_id', '=', self.campaign_id.id),
            ('sequence', '>', current_step.sequence),
        ], limit=1)
        self.current_step_id = next_step.id if next_step else False
        if not next_step:
            self.write({'state': 'completed', 'completed_on': fields.Datetime.now()})

    def _evaluate_condition(self, step):
        """Evaluate the condition for branching. Simplified for demo."""
        self.ensure_one()
        if not step.condition_field:
            return True
        value = getattr(self.partner_id, step.condition_field, None)
        if step.condition_op == '=':
            return str(value) == step.condition_value
        elif step.condition_op == '!=':
            return str(value) != step.condition_value
        return True
