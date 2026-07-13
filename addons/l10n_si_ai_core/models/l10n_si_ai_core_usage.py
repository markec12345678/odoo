# -*- coding: utf-8 -*-
"""AI Core Usage — tracks token usage and API call statistics."""
from odoo import api, fields, models


class L10nSiAiCoreUsage(models.Model):
    _name = 'l10n_si.ai.core.usage'
    _description = 'AI Core Usage Statistics'
    _order = 'create_date DESC'

    source_module = fields.Char(
        string='Klicni modul', required=True, readonly=True,
        help='Modul, ki je sprožil AI klic (npr. ai_concierge, whatsapp)',
    )
    task_type = fields.Char(
        string='Tip naloge', required=True, readonly=True,
        help='simple, reasoning, creative, multilingual, general',
    )
    provider = fields.Char(
        string='Ponudnik', required=True, readonly=True,
        help='zai, puter, openai, anthropic, local, zenmux, openai_compatible',
    )
    model = fields.Char(string='Model', readonly=True)
    success = fields.Boolean(string='Uspeh', default=False, readonly=True)
    error_message = fields.Text(string='Napaka', readonly=True)
    create_date = fields.Datetime(default=fields.Datetime.now, readonly=True, index=True)
    user_id = fields.Many2one(
        'res.users', string='Uporabnik',
        default=lambda s: s.env.user, readonly=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda s: s.env.company, required=True, readonly=True,
    )

    @api.model
    def log_usage(self, source_module, task_type, provider, model,
                  success, error=None):
        """Log a single AI API call."""
        self.sudo().create({
            'source_module': source_module,
            'task_type': task_type,
            'provider': provider,
            'model': model or '',
            'success': success,
            'error_message': error or '',
        })

    @api.model
    def get_stats(self, days=7):
        """Get usage statistics for the last N days."""
        from datetime import timedelta
        cutoff = fields.Datetime.to_string(
            fields.Datetime.now() - timedelta(days=days)
        )
        records = self.search([('create_date', '>=', cutoff)])

        stats = {
            'total_calls': len(records),
            'successful': sum(1 for r in records if r.success),
            'failed': sum(1 for r in records if not r.success),
            'by_provider': {},
            'by_module': {},
            'by_task': {},
        }

        for r in records:
            stats['by_provider'][r.provider] = \
                stats['by_provider'].get(r.provider, 0) + 1
            stats['by_module'][r.source_module] = \
                stats['by_module'].get(r.source_module, 0) + 1
            stats['by_task'][r.task_type] = \
                stats['by_task'].get(r.task_type, 0) + 1

        return stats
