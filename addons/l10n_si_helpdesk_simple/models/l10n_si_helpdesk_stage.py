# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiHelpdeskStage(models.Model):
    _name = 'l10n_si.helpdesk.stage'
    _description = 'Slovenian Helpdesk Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    is_close = fields.Boolean(
        string='Closing Stage',
        help='Tickets in this stage are considered closed.',
    )
    is_default = fields.Boolean(
        string='Default Stage',
        help='New tickets start in this stage.',
    )
    fold = fields.Boolean(
        string='Folded in Kanban',
        help='Folded stages are collapsed in the kanban view.',
    )
    description = fields.Text()

    _sql_constraints = [
        ('only_one_default', 'unique(is_default) WHERE is_default = TRUE',
         'Only one stage can be the default.'),
    ]
