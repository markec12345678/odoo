# -*- coding: utf-8 -*-
"""Sync log - audit trail of all channel operations."""
from odoo import fields, models


class L10nSiChannelLog(models.Model):
    _name = 'l10n_si.channel.log'
    _description = 'Slovenian Channel Manager Log'
    _order = 'create_date DESC'

    channel_config_id = fields.Many2one('l10n_si.channel.config', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='channel_config_id.company_id', store=True)

    log_type = fields.Selection(
        selection=[('availability_push', 'Push razpoložljivosti'),
                   ('rate_push', 'Push cen'),
                   ('reservation_pull', 'Pull rezervacij'),
                   ('reservation_push', 'Push potrditve'),
                   ('cancellation_push', 'Push preklic'),
                   ('connection_test', 'Test povezave'),
                   ('error', 'Napaka')],
        required=True,
    )
    state = fields.Selection(
        selection=[('success', 'Uspešno'),
                   ('error', 'Napaka'),
                   ('partial', 'Delno')],
        required=True,
    )
    message = fields.Text()
    raw_payload = fields.Text(readonly=True, help='Raw API request/response for debugging.')
