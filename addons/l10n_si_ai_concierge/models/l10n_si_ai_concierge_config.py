# -*- coding: utf-8 -*-
"""Konfiguracija AI asistenta."""
from odoo import fields, models


class L10nSiAiConciergeConfig(models.Model):
    _name = 'l10n_si.ai.concierge.config'
    _description = 'Slovenian AI Concierge Configuration'

    name = fields.Char(required=True, default='AI Concierge')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # AI Backend
    ai_backend = fields.Selection(
        selection=[('openai', 'OpenAI (GPT-4)'),
                   ('anthropic', 'Anthropic Claude'),
                   ('zai', 'ZAI (GLM)'),
                   ('zenmux', 'ZenMux (OpenAI-compatible gateway)'),
                   ('openai_compatible', 'OpenAI-Compatible (custom endpoint)'),
                   ('local', 'Lokalni LLM')],
        default='zai',
        required=True,
    )
    api_key = fields.Char(string='API ključ')
    model_name = fields.Char(
        string='Ime modela', default='glm-4-plus',
        help='npr. gpt-4, claude-3-opus, glm-4-plus, z-ai/glm-5.2 (ZenMux)',
    )
    endpoint_url = fields.Char(
        string='Endpoint URL',
        help='Za OpenAI-Compatible / ZenMux backend. npr. https://zenmux.ai/api/v1',
    )

    # Sistemski prompt
    system_prompt = fields.Text(
        default="""Si prijazen AI asistent v slovenskem hotelu.
Tvoj cilj je pomagati gostom pri vprašanjih o:
- sobah, storitvah, urah delovanja
- lokalnih atrakcijah, prevozu, restavracijah
- rezervacijah masaž, miz, aktivnosti
Odgovarjaj v slovenščini, bodi jedrnat in prijazen.
Če ne veš, reci da boš preveril/a pri recepciji.""",
    )

    # Znanje
    knowledge_article_ids = fields.Many2many(
        'l10n_si.knowledge.article', string='Baza znanja',
        help='AI bo uporabil te članke za odgovore.',
    )

    # Kanali
    enabled_website = fields.Boolean(string='Spletni chat', default=True)
    enabled_whatsapp = fields.Boolean(string='WhatsApp', default=False)
    enabled_email = fields.Boolean(string='E-pošta', default=False)

    # Omejitve
    max_tokens = fields.Integer(default=500, string='Max tokenov na odgovor')
    temperature = fields.Float(default=0.7, string='Kreativnost (0-1)')

    # Statistika
    conversation_count = fields.Integer(compute='_compute_stats', store=False)
    message_count = fields.Integer(compute='_compute_stats', store=False)

    def _compute_stats(self):
        Conversation = self.env['l10n_si.ai.concierge.conversation']
        for cfg in self:
            convs = Conversation.search([('config_id', '=', cfg.id)])
            cfg.conversation_count = len(convs)
            cfg.message_count = sum(len(c.message_ids) for c in convs)
