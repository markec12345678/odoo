# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiHelpdeskCannedResponse(models.Model):
    """Predefined responses for quick reply."""
    _name = 'l10n_si.helpdesk.canned.response'
    _description = 'Slovenian Helpdesk Canned Response'

    name = fields.Char(required=True, translate=True)
    body = fields.Html(required=True, translate=True)
    team_ids = fields.Many2many('l10n_si.helpdesk.team', string='Teams')
    active = fields.Boolean(default=True)
