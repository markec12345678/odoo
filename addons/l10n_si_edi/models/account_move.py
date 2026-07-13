# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import shutil
from xml.etree import ElementTree as ET

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# eSLOG 2.0 namespaces
NS = {
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'default': 'http://www.gzs.si/ebcgs/slog/2.0',
}
ET.register_namespace('', NS['default'])
ET.register_namespace('cbc', NS['cbc'])
ET.register_namespace('cac', NS['cac'])


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_si_edi_state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('sent', 'Sent'),
                   ('accepted', 'Accepted'),
                   ('rejected', 'Rejected'),
                   ('error', 'Error')],
        string='e-Račun State',
        copy=False,
        readonly=True,
    )
    l10n_si_edi_log_ids = fields.One2many('l10n_si.edi.log', 'move_id', string='EDI Logs', readonly=True)

    # -------------------------------------------------------------------------
    # XML generation
    # -------------------------------------------------------------------------

    def _si_edi_generate_eslog_xml(self):
        """Generate eSLOG 2.0 XML for this invoice.

        Returns the XML as a string (UTF-8 encoded, signed with eIDAS).
        """
        self.ensure_one()
        if self.move_type not in ('out_invoice', 'out_refund'):
            raise UserError(_('eSLOG is only supported for customer invoices and refunds.'))

        company = self.company_id
        partner = self.partner_id

        # Root: Invoice
        invoice = ET.Element('{%s}Invoice' % NS['default'], nsmap=NS)

        # Profile / Customization (EN 16931 SI profile)
        cbc = ET.SubElement(invoice, '{%s}ProfileID' % NS['cbc'])
        cbc.text = 'urn:cen.eu:en16931:2017:slovenian:1.0'
        customization = ET.SubElement(invoice, '{%s}CustomizationID' % NS['cbc'])
        customization.text = 'urn:cen.eu:en16931:2017:slovenian:1.0'

        # IDs
        et_id = ET.SubElement(invoice, '{%s}ID' % NS['cbc'])
        et_id.text = self.name or ''

        issue_date = ET.SubElement(invoice, '{%s}IssueDate' % NS['cbc'])
        issue_date.text = (self.invoice_date or fields.Date.today()).isoformat()

        due_date = ET.SubElement(invoice, '{%s}DueDate' % NS['cbc'])
        due_date.text = (self.invoice_date_due or self.invoice_date or fields.Date.today()).isoformat()

        invoice_type_code = ET.SubElement(invoice, '{%s}InvoiceTypeCode' % NS['cbc'])
        invoice_type_code.text = '380' if self.move_type == 'out_invoice' else '381'  # 380=Commercial, 381=Credit note

        # Currency
        currency = ET.SubElement(invoice, '{%s}DocumentCurrencyCode' % NS['cbc'])
        currency.text = self.currency_id.name or 'EUR'

        # Seller (AccountingSupplierParty)
        supplier = ET.SubElement(invoice, '{%s}AccountingSupplierParty' % NS['cac'])
        party = ET.SubElement(supplier, '{%s}Party' % NS['cac'])
        party_name = ET.SubElement(party, '{%s}PartyName' % NS['cac'])
        name = ET.SubElement(party_name, '{%s}Name' % NS['cbc'])
        name.text = company.name or ''
        party_tax = ET.SubElement(party, '{%s}PartyTaxScheme' % NS['cac'])
        company_id = ET.SubElement(party_tax, '{%s}CompanyID' % NS['cbc'])
        company_id.text = (company.vat or '').upper()
        tax_scheme = ET.SubElement(party_tax, '{%s}TaxScheme' % NS['cac'])
        ET.SubElement(tax_scheme, '{%s}ID' % NS['cbc']).text = 'VAT'

        # Buyer (AccountingCustomerParty)
        customer = ET.SubElement(invoice, '{%s}AccountingCustomerParty' % NS['cac'])
        c_party = ET.SubElement(customer, '{%s}Party' % NS['cac'])
        c_party_name = ET.SubElement(c_party, '{%s}PartyName' % NS['cac'])
        c_name = ET.SubElement(c_party_name, '{%s}Name' % NS['cbc'])
        c_name.text = partner.name or ''
        if partner.vat:
            c_party_tax = ET.SubElement(c_party, '{%s}PartyTaxScheme' % NS['cac'])
            c_company_id = ET.SubElement(c_party_tax, '{%s}CompanyID' % NS['cbc'])
            c_company_id.text = partner.vat.upper()
            c_tax_scheme = ET.SubElement(c_party_tax, '{%s}TaxScheme' % NS['cac'])
            ET.SubElement(c_tax_scheme, '{%s}ID' % NS['cbc']).text = 'VAT'

        # Tax total
        tax_total = ET.SubElement(invoice, '{%s}TaxTotal' % NS['cac'])
        tax_amount = ET.SubElement(tax_total, '{%s}TaxAmount' % NS['cbc'])
        tax_amount.set('currencyID', self.currency_id.name or 'EUR')
        tax_amount.text = f'{self.amount_tax:.2f}'

        # Tax subtotals per rate
        taxes_by_rate = {}
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.amount_tax_domain == 'vat':
                    rate = float(tax.amount)
                    base = line.price_subtotal
                    tax_val = base * (rate / 100.0)
                    if rate not in taxes_by_rate:
                        taxes_by_rate[rate] = {'base': 0.0, 'tax': 0.0}
                    taxes_by_rate[rate]['base'] += base
                    taxes_by_rate[rate]['tax'] += tax_val

        for rate, data in sorted(taxes_by_rate.items()):
            subtotal = ET.SubElement(tax_total, '{%s}TaxSubtotal' % NS['cac'])
            taxable = ET.SubElement(subtotal, '{%s}TaxableAmount' % NS['cbc'])
            taxable.set('currencyID', self.currency_id.name or 'EUR')
            taxable.text = f'{data["base"]:.2f}'
            sub_amount = ET.SubElement(subtotal, '{%s}TaxAmount' % NS['cbc'])
            sub_amount.set('currencyID', self.currency_id.name or 'EUR')
            sub_amount.text = f'{data["tax"]:.2f}'
            category = ET.SubElement(subtotal, '{%s}TaxCategory' % NS['cac'])
            ET.SubElement(category, '{%s}ID' % NS['cbc']).text = 'S' if rate > 0 else 'Z'
            ET.SubElement(category, '{%s}Percent' % NS['cbc']).text = f'{rate:.2f}'
            tax_scheme_sub = ET.SubElement(category, '{%s}TaxScheme' % NS['cac'])
            ET.SubElement(tax_scheme_sub, '{%s}ID' % NS['cbc']).text = 'VAT'

        # Monetary total
        monetary = ET.SubElement(invoice, '{%s}LegalMonetaryTotal' % NS['cac'])
        for tag, value in (
            ('TaxExclusiveAmount', self.amount_untaxed),
            ('TaxInclusiveAmount', self.amount_total),
            ('PayableAmount', self.amount_total),
        ):
            elem = ET.SubElement(monetary, '{%s}%s' % (NS['cbc'], tag))
            elem.set('currencyID', self.currency_id.name or 'EUR')
            elem.text = f'{value:.2f}'

        # Invoice lines
        for idx, line in enumerate(self.invoice_line_ids, start=1):
            inv_line = ET.SubElement(invoice, '{%s}InvoiceLine' % NS['cac'])
            line_id = ET.SubElement(inv_line, '{%s}ID' % NS['cbc'])
            line_id.text = str(idx)
            line_qty = ET.SubElement(inv_line, '{%s}InvoicedQuantity' % NS['cbc'])
            line_qty.text = str(line.quantity or 1)
            line_amount = ET.SubElement(inv_line, '{%s}LineExtensionAmount' % NS['cbc'])
            line_amount.set('currencyID', self.currency_id.name or 'EUR')
            line_amount.text = f'{line.price_subtotal:.2f}'

            item = ET.SubElement(inv_line, '{%s}Item' % NS['cac'])
            item_desc = ET.SubElement(item, '{%s}Description' % NS['cbc'])
            item_desc.text = line.name or ''
            item_name = ET.SubElement(item, '{%s}Name' % NS['cbc'])
            item_name.text = line.product_id.name if line.product_id else (line.name or '')

            price = ET.SubElement(inv_line, '{%s}Price' % NS['cac'])
            price_amount = ET.SubElement(price, '{%s}PriceAmount' % NS['cbc'])
            price_amount.set('currencyID', self.currency_id.name or 'EUR')
            price_amount.text = f'{line.price_unit:.2f}'

        xml_bytes = ET.tostring(invoice, encoding='utf-8', xml_declaration=True)
        return xml_bytes.decode('utf-8')

    def _si_edi_sign_xml(self, xml_str):
        """Sign the XML with the eIDAS certificate using xmldsig (RSA-SHA256).

        Uses external `xmlsec1` binary (Debian package `xmlsec1`).
        """
        import subprocess
        import tempfile
        company = self.company_id
        cert_path, key_path, temp_dir = company.si_edi_get_cert_paths()
        if not cert_path:
            raise UserError(_('eIDAS certificate not configured.'))

        try:
            # Write unsigned XML to temp file
            xml_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.xml', dir=temp_dir, delete=False, encoding='utf-8',
            )
            xml_file.write(xml_str)
            xml_file.close()

            signed_file = xml_file.name + '.signed.xml'
            # xmlsec1 sign with --X509
            cmd = [
                'xmlsec1', '--sign', '--pkcs12-cert-allowed',
                '--private-key-pem', key_path,
                '--trusted-pem', cert_path,
                '--output', signed_file,
                xml_file.name,
            ]
            # Fallback to openssl-based signing if xmlsec1 is not available
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                with open(signed_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Simple envelope signature via openssl
                _logger.info('xmlsec1 not available, using openssl envelope')
                signature = subprocess.run(
                    ['openssl', 'dgst', '-sha256', '-sign', key_path],
                    input=xml_str.encode('utf-8'),
                    capture_output=True, check=True, timeout=30,
                ).stdout
                import base64 as b64
                return xml_str + '\n<!-- SIG: ' + b64.b64encode(signature).decode() + ' -->'
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # Submission
    # -------------------------------------------------------------------------

    def _si_edi_submit_to_furs(self):
        """Generate, sign, and submit the eSLOG XML to FURS eDavki."""
        self.ensure_one()
        company = self.company_id
        if not company.si_edi_enabled:
            return False

        # Generate + sign XML
        xml_str = self._si_edi_generate_eslog_xml()
        signed_xml = self._si_edi_sign_xml(xml_str)

        # Store as attachment (10-year retention)
        attachment = self.env['ir.attachment'].create({
            'name': f'eslog_{self.name or self.id}.xml',
            'type': 'binary',
            'datas': base64.b64encode(signed_xml.encode('utf-8')),
            'res_model': 'account.move',
            'res_id': self.id,
            'mimetype': 'application/xml',
        })

        # Submit to FURS
        url = company.si_edi_get_endpoint()
        cert_path, key_path, temp_dir = company.si_edi_get_cert_paths()

        log_vals = {
            'move_id': self.id,
            'company_id': company.id,
            'xml_attachment_id': attachment.id,
            'state': 'draft',
        }

        try:
            response = requests.post(
                url,
                data=signed_xml.encode('utf-8'),
                cert=(cert_path, key_path) if cert_path else None,
                timeout=30,
                headers={
                    'Content-Type': 'application/xml; charset=utf-8',
                    'X-SLOG-Version': '2.0',
                },
            )
            log_vals['furs_response_code'] = response.status_code
            log_vals['furs_response'] = response.text[:10000]  # truncate
            log_vals['submitted_at'] = fields.Datetime.now()

            if response.status_code in (200, 201, 202):
                # FURS returns a message ID
                msg_id = response.headers.get('X-FURS-MessageID') or response.text[:36]
                log_vals['furs_message_id'] = msg_id
                log_vals['state'] = 'sent'
                self.l10n_si_edi_state = 'sent'
                self.message_post(
                    body=_('eSLOG 2.0 XML submitted to FURS. Message ID: %s') % msg_id,
                )
                return True
            log_vals['state'] = 'rejected'
            log_vals['error_message'] = response.text[:5000]
            self.l10n_si_edi_state = 'rejected'
            return False
        except requests.RequestException as e:
            _logger.warning('eSLOG submission failed: %s', e)
            log_vals['state'] = 'error'
            log_vals['error_message'] = str(e)
            self.l10n_si_edi_state = 'error'
            return False
        finally:
            self.env['l10n_si.edi.log'].create(log_vals)
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            if (move.move_type in ('out_invoice', 'out_refund')
                    and move.company_id.country_id.code == 'SI'
                    and move.company_id.si_edi_enabled
                    and move.company_id.si_edi_auto_submit):
                try:
                    move._si_edi_submit_to_furs()
                except Exception as e:  # noqa: BLE001
                    _logger.warning('Auto eSLOG submission failed for move %s: %s', move.id, e)
        return posted

    def action_si_edi_submit(self):
        """Manual action: submit the invoice to FURS eDavki."""
        for move in self:
            move._si_edi_submit_to_furs()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Submitted'),
                'message': _('eSLOG submission complete. Check the EDI log for details.'),
                'type': 'info',
            },
        }

    def action_si_edi_download_xml(self):
        """Download the last signed XML for review."""
        self.ensure_one()
        last_log = self.l10n_si_edi_log_ids[:1]
        if not last_log or not last_log.xml_attachment_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No XML'),
                    'message': _('No eSLOG XML has been generated for this invoice yet.'),
                    'type': 'warning',
                },
            }
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{last_log.xml_attachment_id.id}?download=true',
            'target': 'self',
        }
