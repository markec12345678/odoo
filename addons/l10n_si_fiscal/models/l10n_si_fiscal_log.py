# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nSiFiscalLog(models.Model):
    """Audit log of every FURS API call (success or failure).

    Useful for:
    * Compliance audits (FURS may request proof of EOR within 10-year retention)
    * Debugging submission failures
    * Re-submission of failed invoices within 48h
    """
    _name = 'l10n_si.fiscal.log'
    _description = 'Slovenian Fiscal Verification Log'
    _order = 'create_date DESC'
    _rec_name = 'create_date'

    move_id = fields.Many2one('account.move', string='Invoice', ondelete='restrict')
    company_id = fields.Many2one('res.company', string='Company', required=True)
    request_type = fields.Selection(
        selection=[('echo', 'Echo test'),
                   ('register_premise', 'Premise registration'),
                   ('register_device', 'Device Registration'),
                   ('invoice', 'Invoice Submission'),
                   ('storno', 'Storno Submission')],
        string='Request Type',
        required=True,
    )
    zoi = fields.Char(string='ZOI', help='Zaščitna oznaka izdajatelja računa (MD5 hex).')
    eor = fields.Char(string='EOR', help='Enkratna identifikacijska oznaka računa (UUID).')
    furs_message = fields.Text(string='FURS Response', readonly=True)
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('sent', 'Sent'),
                   ('error', 'Error'),
                   ('storno', 'Storno')],
        default='draft',
        required=True,
    )
    furs_request = fields.Text(string='Request Payload', readonly=True)
    furs_response_code = fields.Integer(string='HTTP Code', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)
    retry_count = fields.Integer(default=0)
    next_retry = fields.Datetime()

    def action_retry(self):
        """Manual retry: re-submit the failed invoice to FURS."""
        for log in self:
            if log.move_id:
                log.move_id._si_fiscal_submit_to_furs()
        return True

    @api.model
    def _cron_retry_failed_submissions(self):
        """Cron: retry all submissions that failed and have not exceeded 48h."""
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), hours=48)
        pending = self.search([
            ('state', '=', 'error'),
            ('create_date', '>=', cutoff),
            ('next_retry', '<=', fields.Datetime.now()),
        ])
        _logger.info('Cron retry: %d pending FURS submissions', len(pending))
        for log in pending:
            try:
                if log.move_id:
                    log.move_id._si_fiscal_submit_to_furs()
            except Exception as e:  # noqa: BLE001
                _logger.warning('Retry failed for log %s: %s', log.id, e)
                log.retry_count += 1
                # Exponential backoff: 5min, 10min, 20min, 40min, 80min
                log.next_retry = fields.Datetime.add(
                    fields.Datetime.now(), minutes=5 * (2 ** log.retry_count),
                )
