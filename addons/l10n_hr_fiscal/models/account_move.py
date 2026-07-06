# -*- coding: utf-8 -*-
"""Account.move extension for Croatian Fiskalizacija.

ZKI = MD5(oib + datum_vrijeme_izdavanja + broj_racuna +
          oznaka_pp + oznaka_nu + ukupni_iznos + ukupni_porez)

Reference: Fiskalizacija — Tehnička specifikacija za korisnike v1.8, section 3.1
"""
import hashlib
import logging
import uuid
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

CISF_DEMO = 'https://cistest.apis-it.hr:8449/FiskalizacijaServiceTest'
CISF_PROD = 'https://cis.porezna-uprava.gov.hr:8449/FiskalizacijaService'


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_hr_zki = fields.Char(
        string='ZKI', copy=False, readonly=True,
        help='Zaštitni kod izdavatelja računa — MD5 hex (32 chars).',
    )
    l10n_hr_jir = fields.Char(
        string='JIR', copy=False, readonly=True,
        help='Jedinstveni identifikator računa — UUID od CISF.',
    )
    l10n_hr_fiscal_state = fields.Selection(
        selection=[('pending', 'Na čekanju'),
                   ('submitted', 'Poslano'),
                   ('error', 'Greška'),
                   ('storno', 'Storno')],
        string='Status fiskalizacije', copy=False, readonly=True,
    )
    l10n_hr_fiscal_submitted_at = fields.Datetime(copy=False, readonly=True)
    l10n_hr_fiscal_qr = fields.Binary(
        string='QR kod', copy=False, readonly=True,
        help='QR kod za provjeru računa na Poreznoj upravi.',
    )
    l10n_hr_business_premise_id = fields.Many2one(
        'l10n_hr.business.premise', string='Poslovni prostor',
    )
    l10n_hr_fiscal_log_ids = fields.One2many(
        'l10n_hr.fiscal.log', 'move_id', string='Dnevnik fiskalizacije', readonly=True,
    )

    def _hr_fiscal_compute_zki(self):
        """Generate ZKI per CISF technical specification v1.8."""
        self.ensure_one()
        company = self.company_id
        oib = (company.vat or '').strip()
        if not oib or not oib.isdigit() or len(oib) != 11:
            raise UserError(_(
                'Company %(name)s has an invalid OIB for ZKI (must be 11 digits).',
                name=company.name,
            ))
        issue_dt = self.invoice_date or fields.Date.today()
        issue_dt_str = issue_dt.strftime('%d.%m.%Y') + '00:00:00'
        invoice_number = self.name or ''
        if not invoice_number:
            raise UserError(_('Cannot compute ZKI without an invoice number.'))
        premise = self.l10n_hr_business_premise_id
        premise_code = premise.code if premise else ''
        device_code = '1'
        total_amount = f'{self.amount_total:.2f}'
        total_tax = 0.0
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.amount_tax_domain == 'vat' and tax.amount:
                    total_tax += line.price_subtotal * (tax.amount / 100.0)
        total_tax_str = f'{total_tax:.2f}'
        concatenated = oib + issue_dt_str + invoice_number + premise_code + device_code + total_amount + total_tax_str
        return hashlib.md5(concatenated.encode('utf-8')).hexdigest()

    def _hr_fiscal_submit_to_cisf(self):
        """Submit invoice to CISF via SOAP using FINA mTLS certificate."""
        import tempfile
        import base64
        from .cisf_client import (
            CISFClient, CISFAuthError, CISFValidationError,
            CISFConnectionError, CISFUnknownError,
            extract_pfx_to_pem, build_invoice_xml,
        )

        self.ensure_one()
        company = self.company_id
        if not company.hr_fiscal_enabled:
            return False
        if not company.hr_fiscal_certificate:
            raise UserError(_('FINA certificate not configured on %s') % company.name)
        if not self.l10n_hr_zki:
            self.l10n_hr_zki = self._hr_fiscal_compute_zki()
        if not self.l10n_hr_business_premise_id:
            raise UserError(_('Invoice %s has no business premise set.') % self.name)

        vat_breakdown = []
        total_tax = 0.0
        taxes_by_rate = {}
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.amount_tax_domain == 'vat' and tax.amount:
                    rate = float(tax.amount)
                    base = line.price_subtotal
                    tax_amount = base * (rate / 100.0)
                    if rate not in taxes_by_rate:
                        taxes_by_rate[rate] = 0.0
                    taxes_by_rate[rate] += base
                    total_tax += tax_amount
        for rate, base in sorted(taxes_by_rate.items()):
            tax_amount = base * (rate / 100.0)
            vat_breakdown.append((rate, base, tax_amount))

        invoice_serial = self.name.split('/')[-1] if self.name else '1'
        invoice_xml = build_invoice_xml(
            oib=(company.vat or '').strip(),
            invoice_number=invoice_serial,
            premise_code=self.l10n_hr_business_premise_id.code,
            device_code='1',
            issue_datetime=self.invoice_date or fields.Date.today(),
            zki=self.l10n_hr_zki,
            total_amount=self.amount_total,
            vat_total=total_tax,
            vat_breakdown=vat_breakdown,
            payment_method='G',
        )
        log_vals = {
            'move_id': self.id,
            'company_id': company.id,
            'request_type': 'invoice',
            'request_xml': invoice_xml,
            'zki': self.l10n_hr_zki,
            'state': 'draft',
        }

        pfx_temp = None
        try:
            pfx_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
            pfx_temp.write(base64.b64decode(company.hr_fiscal_certificate))
            pfx_temp.close()
            cert_pem, key_pem = extract_pfx_to_pem(
                pfx_temp.name, company.hr_fiscal_certificate_password or '',
            )
            client = CISFClient(
                cert_pem_path=cert_pem, key_pem_path=key_pem,
                environment=company.hr_fiscal_environment,
            )
            jir, raw_response = client.submit_invoice(invoice_xml)
            self.write({
                'l10n_hr_jir': jir,
                'l10n_hr_fiscal_state': 'submitted',
                'l10n_hr_fiscal_submitted_at': fields.Datetime.now(),
            })
            log_vals.update({
                'state': 'sent', 'jir': jir,
                'response_xml': raw_response, 'http_status': 200,
            })
            self.env['l10n_hr.fiscal.log'].create(log_vals)
            _logger.info('CISF invoice %s submitted (JIR=%s)', self.name, jir)
            return True
        except CISFAuthError as e:
            _logger.error('CISF auth failed for %s: %s', self.name, e)
            self.write({'l10n_hr_fiscal_state': 'error'})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_hr.fiscal.log'].create(log_vals)
            return False
        except CISFValidationError as e:
            _logger.warning('CISF validation failed for %s: %s', self.name, e)
            self.write({'l10n_hr_fiscal_state': 'error'})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_hr.fiscal.log'].create(log_vals)
            return False
        except CISFConnectionError as e:
            _logger.warning('CISF connection error for %s: %s', self.name, e)
            self.write({'l10n_hr_fiscal_state': 'pending'})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_hr.fiscal.log'].create(log_vals)
            return False
        except (CISFUnknownError, Exception) as e:
            _logger.exception('CISF unknown error for %s', self.name)
            self.write({'l10n_hr_fiscal_state': 'error'})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_hr.fiscal.log'].create(log_vals)
            return False
        finally:
            import os as _os
            if pfx_temp and _os.path.exists(pfx_temp.name):
                _os.unlink(pfx_temp.name)

    def _post(self, soft=True):
        """After posting, generate ZKI and (optionally) submit to CISF."""
        posted = super()._post(soft=soft)
        for move in posted:
            if (move.move_type in ('out_invoice', 'out_refund', 'out_receipt')
                    and move.company_id.country_id.code == 'HR'
                    and move.company_id.hr_fiscal_enabled):
                if not move.l10n_hr_zki:
                    move.l10n_hr_zki = move._hr_fiscal_compute_zki()
                    move.l10n_hr_fiscal_state = 'pending'
                if move.company_id.hr_fiscal_auto_submit:
                    move._hr_fiscal_submit_to_cisf()
        return posted

    def action_hr_resubmit_to_cisf(self):
        """Manual action: re-submit the failed/pending invoice."""
        for move in self:
            move._hr_fiscal_submit_to_cisf()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Submitted'),
                'message': _('Re-submission queued.'),
                'type': 'info',
            },
        }
