# -*- coding: utf-8 -*-
"""Approval rule — defines routing for a given category and amount."""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiApprovalRule(models.Model):
    """Rule that determines which approver(s) are needed for a request.

    Example rules:
        category='purchases', min_amount=0, max_amount=500  → direct manager
        category='purchases', min_amount=500, max_amount=5000 → department head
        category='purchases', min_amount=5000, max_amount=∞  → director
        category='leaves', days_min=1, days_max=3 → direct manager
        category='leaves', days_min=3, days_max=∞ → director + HR
    """
    _name = 'l10n_si.approval.rule'
    _description = 'Slovenian Approval Rule'
    _order = 'category, min_amount, days_min'

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    category = fields.Selection(
        selection=[('purchases', 'Nakupi'),
                   ('leaves', 'Dopusti'),
                   ('expenses', 'Stroški'),
                   ('travel', 'Potni nalogi'),
                   ('vehicle', 'Službena vozila'),
                   ('custom', 'Drugo')],
        required=True,
    )
    min_amount = fields.Float(string='Min. znesek (€)', default=0.0)
    max_amount = fields.Float(string='Max. znesek (€)', default=0.0,
                              help='0 means no upper limit.')
    days_min = fields.Integer(string='Min. dni', default=0)
    days_max = fields.Integer(string='Max. dni', default=0,
                              help='0 means no upper limit.')

    # Approver chain (sequential order)
    approver_ids = fields.One2many(
        'l10n_si.approval.rule.approver', 'rule_id', string='Approver Chain',
    )
    workflow_type = fields.Selection(
        selection=[('sequential', 'Zaporedno'),
                   ('parallel', 'Vzporedno (vsi hkrati)')],
        default='sequential',
        required=True,
    )

    @api.constrains('min_amount', 'max_amount')
    def _check_amounts(self):
        for rule in self:
            if rule.max_amount > 0 and rule.min_amount >= rule.max_amount:
                raise ValidationError(_(
                    'Min amount must be less than max amount (rule: %s).', rule.name,
                ))


class L10nSiApprovalRuleApprover(models.Model):
    """One approver in the chain for a rule."""
    _name = 'l10n_si.approval.rule.approver'
    _description = 'Slovenian Approval Rule Approver'
    _order = 'sequence, id'

    rule_id = fields.Many2one('l10n_si.approval.rule', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10, required=True)
    approver_employee_id = fields.Many2one('hr.employee', string='Approver', required=True)
    role = fields.Selection(
        selection=[('manager', 'Neposredni vodja'),
                   ('department', 'Vodja oddelka'),
                   ('director', 'Direktor'),
                   ('hr', 'HR'),
                   ('finance', 'Finančna'),
                   ('specific', 'Specifična oseba')],
        default='specific',
        required=True,
    )
