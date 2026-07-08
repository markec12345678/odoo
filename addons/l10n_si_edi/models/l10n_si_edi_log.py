# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import shutil

import requests

from odoo import api, _, fields, models

_logger = logging.getLogger(__name__)


class L10nSiEdiLog(models.Model):
    """Submission log for each eSLOG XML sent to FURS eDavki."""
    _name = 'l10n_si.edi.log'
    _description = 'Slovenian e-Račun Submission Log'
    _order = 'create_date DESC'
    _rec_name = 'create_date'

    move_id = fields.Many2one('account.move', string='Invoice', ondelete='restrict')
    company_id = fields.Many2one('res.company', string='Company', required=True)
    xml_attachment_id = fields.Many2one(
        'ir.attachment', string='XML File', ondelete='restrict',
        help='Signed eSLOG 2.0 XML stored as attachment (10-year retention).',
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('sent', 'Sent'),
                   ('accepted', 'Accepted'),
                   ('rejected', 'Rejected'),
                   ('error', 'Error')],
        default='draft',
        required=True,
    )
    furs_message_id = fields.Char(string='FURS Message ID', readonly=True)
    furs_response = fields.Text(string='FURS Response', readonly=True)
    furs_response_code = fields.Integer(string='HTTP Code', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)
    submitted_at = fields.Datetime(string='Submitted At', readonly=True)
    accepted_at = fields.Datetime(string='Accepted At', readonly=True)
    retry_count = fields.Integer(default=0)

    @api.model
    def _cron_poll_acceptance_status(self):
        """Poll FURS for acceptance status of recently-submitted (not yet accepted) logs."""
        pending = self.search([
            ('state', '=', 'sent'),
            ('submitted_at', '>=', fields.Datetime.subtract(fields.Datetime.now(), hours=24)),
        ])
        _logger.info('Polling FURS for %d pending eSLOG submissions', len(pending))
        for log in pending:
            company = log.company_id
            if not company.si_edi_certificate:
                continue
            cert_path, key_path, temp_dir = company.si_edi_get_cert_paths()
            url = company.si_edi_get_endpoint() + f'/{log.furs_message_id}'
            try:
                response = requests.get(
                    url,
                    cert=(cert_path, key_path),
                    timeout=15,
                    headers={'Accept': 'application/xml'},
                )
                if response.status_code == 200:
                    body = response.text
                    if 'accepted' in body.lower() or 'Acceptance' in body:
                        log.write({
                            'state': 'accepted',
                            'accepted_at': fields.Datetime.now(),
                            'furs_response': body[:10000],
                        })
                        if log.move_id:
                            log.move_id.l10n_si_edi_state = 'accepted'
                            log.move_id.message_post(
                                body=_('eSLOG XML accepted by FURS.'),
                            )
                    elif 'rejected' in body.lower() or 'Rejection' in body:
                        log.write({
                            'state': 'rejected',
                            'furs_response': body[:10000],
                        })
                        if log.move_id:
                            log.move_id.l10n_si_edi_state = 'rejected'
                            log.move_id.message_post(
                                body=_('eSLOG XML rejected by FURS. See log.'),
                            )
                elif response.status_code == 404:
                    # Not yet processed — keep polling
                    pass
            except requests.RequestException as e:
                _logger.warning('Poll failed for log %s: %s', log.id, e)
            finally:
                if temp_dir:
                    shutil.rmtree(temp_dir, ignore_errors=True)
