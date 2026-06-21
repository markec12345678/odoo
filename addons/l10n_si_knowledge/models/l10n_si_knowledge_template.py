# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiKnowledgeTemplate(models.Model):
    """Predefined document templates with mail-merge placeholders."""
    _name = 'l10n_si.knowledge.template'
    _description = 'Slovenian Knowledge Template'

    name = fields.Char(required=True, translate=True)
    template_type = fields.Selection(
        selection=[('email', 'E-pošta'),
                   ('contract', 'Pogodba'),
                   ('offer', 'Ponudba'),
                   ('letter', 'Pismo'),
                   ('other', 'Drugo')],
        default='email',
        required=True,
    )
    subject = fields.Char(help='For email templates only.')
    body = fields.Html(required=True)
    placeholders = fields.Text(
        help='Available placeholders: {{partner.name}}, {{partner.email}}, '
             '{{user.name}}, {{date}}, {{company.name}}',
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
