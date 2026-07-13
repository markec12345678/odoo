# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class L10n_si_competitor (models.Model):
    _name = "l10n_si.competitor"
    _description = "Slovenian Competitor Pricing"
    _order = "create_date DESC"

    name = fields.Char(required=True, string="Naziv")
    number = fields.Char(copy=False, readonly=True, default="/")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda s: s.env.company, required=True)
    notes = fields.Text()
    ai_analysis = fields.Text(
        string='AI analiza konkurenčnih cen', copy=False,
        help='AI-generirana analiza konkurenčnih cen in priporočila',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number","/") == "/":
                vals["number"] = self.env["ir.sequence"].next_by_code("l10n_si.competitor") or "/"
        return super().create(vals_list)

    def action_generate_ai_analysis(self):
        """AI analiza konkurenčnih cen in priporočila za prilagoditev."""
        AiCore = self.env.get('l10n_si.ai.core.route')
        if not AiCore:
            _logger.info('Competitor AI: AI Core not installed — skipping')
            return True
        for comp in self:
            prompt = (
                f"Analiziraj konkurenco za hotel:\n"
                f"Ime konkurenta: {comp.name}\n"
                f"Opombe: {comp.notes or 'brez opomb'}\n\n"
                f"Predlagaj strategijo za konkurenčno prednost:\n"
                f"1. Katere cene naj spremljamo?\n"
                f"2. Kako se pozicionirati glede na konkurenco?\n"
                f"3. Katere storitve izpostaviti kot diferenciator?\n"
                f"4. Priporočila za pakete in akcije?\n"
                f"Odgovori v slovenščini, 3-5 stavkov."
            )
            try:
                result = AiCore.generate(
                    messages=[{'role': 'user', 'content': prompt}],
                    task_type='reasoning',
                    system_prompt='Si strokovnjak za konkurenčno analizo '
                                  'v hotelirstvu. Analiziraš konkurenco in '
                                  'daješ strateška priporočila, v slovenščini.',
                    source_module='competitor_pricing',
                )
                if result.get('success') and result.get('response'):
                    comp.ai_analysis = result['response']
                    _logger.info(
                        'Competitor AI: analysis for %s via %s/%s',
                        comp.name, result.get('provider'),
                        result.get('model'),
                    )
            except Exception as e:
                _logger.error('Competitor AI: error: %s', e)
        return True
