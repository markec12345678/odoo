# -*- coding: utf-8 -*-
"""AI Core Provider — represents one LLM backend instance.

Each provider links to an l10n_si.ai.concierge.config record and has:
- priority (lower = tried first)
- task_type (what tasks this provider is best for)
- max_tokens_override (model-specific token limits)
"""
from odoo import api, fields, models


class L10nSiAiCoreProvider(models.Model):
    _name = 'l10n_si.ai.core.provider'
    _description = 'AI Core Provider'
    _order = 'priority, sequence'

    name = fields.Char(
        string='Name', required=True,
        compute='_compute_name', store=True,
    )
    config_id = fields.Many2one(
        'l10n_si.ai.concierge.config', string='AI Config',
        required=True, ondelete='cascade',
        help='The AI Concierge config with API key and backend settings',
    )
    backend = fields.Selection(
        related='config_id.ai_backend', string='Backend', store=True,
    )
    model_name = fields.Char(
        related='config_id.model_name', string='Model', store=True,
    )
    task_type = fields.Selection(
        selection=[
            ('general', 'Splošno (vse naloge)'),
            ('simple', 'Preprosto (hitri odgovori)'),
            ('reasoning', 'Kompleksno (razmišljanje, analize)'),
            ('creative', 'Kreativno (pisanje, marketing)'),
            ('multilingual', 'Večjezično (slovenščina, hrvaščina)'),
        ],
        default='general',
        required=True,
        help='Tip naloge, za katerega je ta ponudnik najboljši',
    )
    priority = fields.Integer(
        string='Prioriteta', default=10,
        help='Nižja številka = poskusimo prej (1 = primarni, 10 = zadnji fallback)',
    )
    active = fields.Boolean(string='Aktiven', default=True)
    max_tokens_override = fields.Integer(
        string='Max tokeni (override)',
        help='Če prazno, uporabi config.max_tokens. GLM 5.1 potrebuje 1000+',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('config_task_unique',
         'unique(config_id, task_type)',
         'Provider za ta config + task_type že obstaja!'),
    ]

    @api.depends('backend', 'model_name', 'task_type')
    def _compute_name(self):
        for p in self:
            p.name = f'{p.backend or "?"} / {p.model_name or "?"} ({p.task_type})'
