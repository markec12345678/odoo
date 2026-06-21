# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import json
import logging
import shutil
import uuid
from datetime import datetime, timezone

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_si_zoi = fields.Char(
        string='ZOI',
        copy=False,
        readonly=True,
        help='Zaščitna oznaka izdajatelja računa — MD5 hex (32 chars).',
    )
    l10n_si_eor = fields.Char(
        string='EOR',
        copy=False,
        readonly=True,
        help='Enkratna identifikacijska oznaka računa — UUID vrnjen s strani FURS.',
    )
    l10n_si_fiscal_state = fields.Selection(
        selection=[('pending', 'Pending'),
                   ('submitted', 'Submitted'),
                   ('error', 'Error'),
                   ('storno', 'Storno')],
        string='Fiscal State',
        copy=False,
        readonly=True,
    )
    l10n_si_fiscal_submitted_at = fields.Datetime(copy=False, readonly=True)
    l10n_si_fiscal_qr = fields.Binary(
        string='QR Code',
        copy=False,
        readonly=True,
        help='QR code containing ZOI + meta fields for printing on the invoice.',
    )
    l10n_si_fiscal_log_ids = fields.One2many(
        'l10n_si.fiscal.log', 'move_id', string='Fiscal Log', readonly=True,
    )

    # -------------------------------------------------------------------------
    # ZOI generation
    # -------------------------------------------------------------------------

    def _si_fiscal_compute_zoi(self):
        """Generate the ZOI per FURS spec v1.6.

        ZOI = MD5(tax_number + issue_datetime + invoice_number +
                  business_premise_id + electronic_device_id + invoice_serial)

        All concatenated as strings, no separators. issue_datetime in ISO 8601
        without timezone: 'YYYY-MM-DDTHH:MM:SS'.

        Returns:
            str: 32-char lowercase hex MD5.
        """
        self.ensure_one()
        company = self.company_id
        tax_no = (company.vat or '').upper().lstrip('SI').strip()
        if not tax_no.isdigit() or len(tax_no) != 8:
            raise UserError(_(
                'Company %(name)s has an invalid VAT number for ZOI computation.',
                name=company.name,
            ))

        issue_dt = self.invoice_date or fields.Date.today()
        # FURS expects local time; assume server timezone is Europe/Ljubljana
        issue_dt_str = datetime.combine(issue_dt, datetime.min.time()).strftime('%Y-%m-%dT%H:%M:%S')

        invoice_number = self.l10n_si_sequence_number or self.name or ''
        if not invoice_number:
            raise UserError(_('Cannot compute ZOI without an invoice number.'))

        premise = self.l10n_si_business_premise_id
        device = self.l10n_si_electronic_device_id
        if not premise or not device:
            raise UserError(_(
                'Invoice %(inv)s has no SI business premise or device set.',
                inv=invoice_number,
            ))

        # Invoice serial number: extract the trailing digits from the SI sequence.
        serial = self._si_fiscal_extract_serial(invoice_number)
        if not serial:
            raise UserError(_('Cannot extract invoice serial from %s') % invoice_number)

        concatenated = tax_no + issue_dt_str + invoice_number + premise.code + device.code + serial
        zoi = hashlib.md5(concatenated.encode('utf-8')).hexdigest()
        return zoi

    @staticmethod
    def _si_fiscal_extract_serial(invoice_number: str) -> str:
        """Extract the trailing numeric serial from a formatted SI invoice number.

        Example: 'BL1-KASA1-2025-00001' → '00001'
        """
        parts = invoice_number.split('-')
        for part in reversed(parts):
            if part.isdigit():
                return part
        return ''

    # -------------------------------------------------------------------------
    # FURS submission
    # -------------------------------------------------------------------------

    def _si_fiscal_build_invoice_payload(self):
        """Build the JSON payload for FURS invoice submission.

        Schema per FURS Technical specification v1.6, section 4.1.
        """
        self.ensure_one()
        company = self.company_id
        tax_no = (company.vat or '').upper().lstrip('SI').strip()
        issue_dt = self.invoice_date or fields.Date.today()
        issue_datetime = datetime.combine(issue_dt, datetime.min.time())

        # Tax totals per rate (22%, 9.5%, 5%, 0%, exempt)
        taxes_by_rate = {}
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.amount_tax_domain == 'vat' and tax.amount:
                    rate = float(tax.amount)
                    base = line.price_subtotal
                    tax_amount = base * (rate / 100.0)
                    if rate not in taxes_by_rate:
                        taxes_by_rate[rate] = {'base': 0.0, 'tax': 0.0}
                    taxes_by_rate[rate]['base'] += base
                    taxes_by_rate[rate]['tax'] += tax_amount

        taxes_payload = []
        for rate in sorted(taxes_by_rate):
            data = taxes_by_rate[rate]
            taxes_payload.append({
                'TaxRate': rate,
                'TaxableAmount': round(data['base'], 2),
                'TaxAmount': round(data['tax'], 2),
            })

        return {
            'TaxNumber': int(tax_no),
            'IssueDateTime': issue_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
            'InvoiceNumber': self.name or self.l10n_si_sequence_number,
            'BusinessPremiseID': self.l10n_si_business_premise_id.code,
            'ElectronicDeviceID': self.l10n_si_electronic_device_id.code,
            'InvoiceAmount': round(self.amount_total, 2),
            'PaymentAmount': round(self.amount_total, 2),
            'TaxesPerSeller': taxes_payload,
            'OperatorTaxNumber': int(tax_no),  # self-hosted: same as company
            'ProtectedID': self.l10n_si_zoi,
        }

    def _si_fiscal_submit_to_furs(self):
        """Submit one invoice to FURS. Idempotent — safe to retry."""
        self.ensure_one()
        company = self.company_id
        if not company.si_fiscal_enabled:
            return False
        if not company.si_fiscal_certificate:
            raise UserError(_('FURS certificate not configured on %s') % company.name)

        if not self.l10n_si_zoi:
            self.l10n_si_zoi = self._si_fiscal_compute_zoi()

        payload = self._si_fiscal_build_invoice_payload()
        url = company.si_fiscal_get_endpoint() + 'invoices'
        cert_path, key_path, temp_dir = company.si_fiscal_get_cert_paths()

        log_vals = {
            'move_id': self.id,
            'company_id': company.id,
            'request_type': 'invoice' if not self.reversed_entry_id else 'storno',
            'zoi': self.l10n_si_zoi,
            'furs_request': json.dumps(payload, indent=2),
            'state': 'draft',
        }

        try:
            response = requests.post(
                url,
                json=payload,
                cert=(cert_path, key_path),
                timeout=15,
                headers={'Content-Type': 'application/json'},
            )
            log_vals['furs_response_code'] = response.status_code
            log_vals['furs_message'] = response.text

            if response.status_code in (200, 201):
                data = response.json()
                eor = data.get('UniqueInvoiceID') or data.get('EOR')
                self.write({
                    'l10n_si_eor': eor,
                    'l10n_si_fiscal_state': 'submitted',
                    'l10n_si_fiscal_submitted_at': fields.Datetime.now(),
                })
                log_vals['eor'] = eor
                log_vals['state'] = 'sent'
                self._si_fiscal_generate_qr_code()
                return True
            # Error
            self.l10n_si_fiscal_state = 'error'
            log_vals['state'] = 'error'
            log_vals['error_message'] = response.text
            log_vals['next_retry'] = fields.Datetime.add(
                fields.Datetime.now(), minutes=5,
            )
            return False
        except requests.RequestException as e:
            _logger.warning('FURS submission failed for move %s: %s', self.id, e)
            self.l10n_si_fiscal_state = 'error'
            log_vals['state'] = 'error'
            log_vals['error_message'] = str(e)
            log_vals['next_retry'] = fields.Datetime.add(
                fields.Datetime.now(), minutes=5,
            )
            return False
        finally:
            self.env['l10n_si.fiscal.log'].create(log_vals)
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # QR code
    # -------------------------------------------------------------------------

    def _si_fiscal_generate_qr_code(self):
        """Generate the QR code for printing on the invoice.

        Per FURS spec, the QR content is the ZOI prefixed with control characters:
            ZOI:<zoi> | date:<YYYY-MM-DDTHH:MM:SS> | amount:<X.YZ>
        Encoded as a PNG and stored in l10n_si_fiscal_qr.
        """
        self.ensure_one()
        if not self.l10n_si_zoi:
            return

        qr_data = (
            f'ZOI:{self.l10n_si_zoi}'
            f'|date:{self.invoice_date.isoformat() if self.invoice_date else ""}'
            f'|amount:{self.amount_total:.2f}'
        )

        try:
            import io
            import qrcode
            qr = qrcode.QRCode(
                version=10,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=4,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            self.l10n_si_fiscal_qr = buffer.getvalue()
        except ImportError:
            _logger.warning('qrcode library not installed — skipping QR generation')

    # -------------------------------------------------------------------------
    # Account.move lifecycle hooks
    # -------------------------------------------------------------------------

    def _post(self, soft=True):
        """After posting, generate ZOI and (optionally) submit to FURS."""
        posted = super()._post(soft=soft)
        for move in posted:
            if (move.move_type in ('out_invoice', 'out_refund', 'out_receipt')
                    and move.company_id.country_id.code == 'SI'
                    and move.company_id.si_fiscal_enabled):
                # Generate ZOI immediately (cheap, local).
                if not move.l10n_si_zoi:
                    move.l10n_si_zoi = move._si_fiscal_compute_zoi()
                    move.l10n_si_fiscal_state = 'pending'
                # Submit if auto mode is on.
                if move.company_id.si_fiscal_auto_submit:
                    move._si_fiscal_submit_to_furs()
        return posted

    def action_si_resubmit_to_furs(self):
        """Manual action: re-submit the failed/pending invoice."""
        for move in self:
            move._si_fiscal_submit_to_furs()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Submitted'),
                'message': _('Re-submission complete. Check the Fiscal Log for details.'),
                'type': 'info',
            },
        }
