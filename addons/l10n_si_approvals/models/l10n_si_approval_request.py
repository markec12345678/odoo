# -*- coding: utf-8 -*-
"""Approval request — one document needing one or more approvals."""
from odoo import _, api, fields, models


class L10nSiApprovalRequest(models.Model):
    _name = 'l10n_si.approval.request'
    _description = 'Slovenian Approval Request'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(required=True, tracking=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    category = fields.Selection(
        selection=[('purchases', 'Nakupi'),
                   ('leaves', 'Dopusti'),
                   ('expenses', 'Stroški'),
                   ('travel', 'Potni nalogi'),
                   ('vehicle', 'Službena vozila'),
                   ('custom', 'Drugo')],
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    requester_employee_id = fields.Many2one(
        'hr.employee', string='Requester', required=True,
        default=lambda self: self.env.user.employee_id,
    )
    requester_user_id = fields.Many2one(
        'res.users', related='requester_employee_id.user_id', store=True,
    )

    # Linked document
    res_model = fields.Char(string='Document Model')
    res_id = fields.Integer(string='Document ID')
    amount = fields.Float(string='Znesek (€)', default=0.0)
    days = fields.Integer(string='Število dni', default=0)
    description = fields.Html(required=True)

    # Workflow
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('pending', 'V postopku'),
                   ('approved', 'Odobreno'),
                   ('rejected', 'Zavrnjeno'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )
    approver_ids = fields.One2many(
        'l10n_si.approval.step', 'request_id', string='Approval Steps',
    )
    current_approver_id = fields.Many2one(
        'hr.employee', compute='_compute_current_approver', store=True,
    )
    date_approved = fields.Datetime(readonly=True, copy=False)
    date_rejected = fields.Datetime(readonly=True, copy=False)

    # SLA
    sla_deadline = fields.Datetime(compute='_compute_sla', store=True)
    sla_breached = fields.Boolean(compute='_compute_sla', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.approval.request') or '/'
        return super().create(vals_list)

    @api.depends('create_date', 'company_id')
    def _compute_sla(self):
        from datetime import timedelta
        for req in self:
            if req.create_date and req.company_id.si_approval_sla_days:
                req.sla_deadline = req.create_date + timedelta(days=req.company_id.si_approval_sla_days)
                req.sla_breached = (
                    req.state == 'pending' and
                    fields.Datetime.now() > req.sla_deadline
                )
            else:
                req.sla_deadline = False
                req.sla_breached = False

    @api.depends('approver_ids.state', 'approver_ids.sequence')
    def _compute_current_approver(self):
        for req in self:
            pending = req.approver_ids.filtered(lambda s: s.state == 'pending')
            pending = pending.sorted('sequence')
            req.current_approver_id = pending[:1].approver_employee_id if pending else False

    def action_submit(self):
        """Find matching rule, create approval steps, send notifications."""
        for req in self:
            req._apply_rules()
            req.state = 'pending'
            req._notify_current_approver()

    def _apply_rules(self):
        """Find matching rule(s) and create approval steps."""
        self.ensure_one()
        # Find matching rule based on category + amount/days
        domain = [
            ('category', '=', self.category),
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
            ('min_amount', '<=', self.amount),
        ]
        rules = self.env['l10n_si.approval.rule'].search(domain)
        # Filter by max_amount (0 = unlimited)
        matching = rules.filtered(
            lambda r: r.max_amount == 0 or r.amount and self.amount <= r.max_amount
        )
        if not matching:
            # No rule → auto-approve
            self.env['l10n_si.approval.step'].create({
                'request_id': self.id,
                'sequence': 10,
                'approver_employee_id': self.env.user.employee_id.id,
                'state': 'approved',
                'role': 'manager',
                'decision_date': fields.Datetime.now(),
                'notes': 'Auto-approved (no matching rule).',
            })
            self.state = 'approved'
            self.date_approved = fields.Datetime.now()
            return

        rule = matching[0]
        sequence = 10
        for approver in rule.approver_ids:
            self.env['l10n_si.approval.step'].create({
                'request_id': self.id,
                'sequence': sequence,
                'approver_employee_id': approver.approver_employee_id.id,
                'role': approver.role,
                'state': 'pending',
            })
            sequence += 10

    def _notify_current_approver(self):
        for req in self:
            if req.current_approver_id and req.current_approver_id.user_id:
                req.message_post(
                    body=_('Prosim odobrite ali zavrnite zahtevek %s') % req.name,
                    partner_ids=[req.current_approver_id.user_id.partner_id.id],
                )

    def action_approve(self):
        """Current approver approves → advance to next step or complete."""
        for req in self:
            current_step = req.approver_ids.filtered(
                lambda s: s.state == 'pending' and s.approver_employee_id.user_id == self.env.user
            )
            if not current_step:
                return  # not authorized
            current_step.write({
                'state': 'approved',
                'decision_date': fields.Datetime.now(),
            })
            # Check if all approved
            pending = req.approver_ids.filtered(lambda s: s.state == 'pending')
            if not pending:
                req.write({
                    'state': 'approved',
                    'date_approved': fields.Datetime.now(),
                })

    def action_reject(self):
        for req in self:
            current_step = req.approver_ids.filtered(
                lambda s: s.state == 'pending' and s.approver_employee_id.user_id == self.env.user
            )
            if not current_step:
                return
            current_step.write({
                'state': 'rejected',
                'decision_date': fields.Datetime.now(),
            })
            req.write({
                'state': 'rejected',
                'date_rejected': fields.Datetime.now(),
            })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    @api.model
    def _cron_check_sla_breach(self):
        """Daily check: send reminders for pending approvals, escalate SLA breaches."""
        for req in self.search([('state', '=', 'pending')]):
            if req.sla_breached:
                # Escalate: notify company manager
                req.message_post(
                    body=_('⚠️ SLA presežen! Zahtevek %s čaka na odobritev od %s.') % (
                        req.name, req.current_approver_id.name,
                    ),
                    partner_ids=[self.env.user.partner_id.id],
                )
            elif req.company_id.si_approval_auto_remind:
                req._notify_current_approver()


class L10nSiApprovalStep(models.Model):
    _name = 'l10n_si.approval.step'
    _description = 'Slovenian Approval Step'
    _order = 'sequence, id'

    request_id = fields.Many2one('l10n_si.approval.request', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10, required=True)
    approver_employee_id = fields.Many2one('hr.employee', required=True)
    role = fields.Selection(
        selection=[('manager', 'Neposredni vodja'),
                   ('department', 'Vodja oddelka'),
                   ('director', 'Direktor'),
                   ('hr', 'HR'),
                   ('finance', 'Finančna'),
                   ('specific', 'Specifična oseba')],
        required=True,
    )
    state = fields.Selection(
        selection=[('pending', 'Čaka'),
                   ('approved', 'Odobreno'),
                   ('rejected', 'Zavrnjeno')],
        default='pending',
    )
    decision_date = fields.Datetime(readonly=True)
    notes = fields.Text()
