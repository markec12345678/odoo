# -*- coding: utf-8 -*-
"""OCR document — one scanned invoice with extracted data."""
import base64
import logging
import re
import subprocess
import tempfile
import os

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# Slovenian OCR patterns
SI_PATTERNS = {
    'vat': re.compile(r'(?:davčna\s+št(?:evila)?|VAT|ID\s+za\s+DDV)[:\s]*SI\s*(\d{8})', re.IGNORECASE),
    'invoice_number': re.compile(r'(?:račun\s+št(?:evilka)?|invoice\s+no|Št\.?\s*računa)[:\s]*([A-Z0-9\-/]+)', re.IGNORECASE),
    'issue_date': re.compile(r'(?:datum\s+računa|issue\s+date|datum\s+izdaje)[:\s]*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})', re.IGNORECASE),
    'due_date': re.compile(r'(?:plačilo\s+do|datum\s+zapadlosti|due\s+date)[:\s]*(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})', re.IGNORECASE),
    'total': re.compile(r'(?:skupaj\s+za\s+plačilo|total|za\s+plačilo)[:\s]*([\d.,]+)\s*(?:EUR|€|EUR)?', re.IGNORECASE),
    'untaxed': re.compile(r'(?:osnova|untaxed|brez\s+DDV)[:\s]*([\d.,]+)\s*(?:EUR|€)?', re.IGNORECASE),
    'tax': re.compile(r'(?:DDV|VAT)[:\s]*([\d.,]+)\s*(?:EUR|€)?', re.IGNORECASE),
    'iban': re.compile(r'(SI\d{2})\s*(\d{3})\s*(\d{4})\s*(\d{4})\s*(\d{3})', re.IGNORECASE),
}


def _parse_si_amount(amount_str):
    """Convert '1.234,56' to 1234.56."""
    if not amount_str:
        return 0.0
    s = amount_str.strip().replace(' ', '')
    # SI format: 1.234,56 → 1234.56
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_si_date(date_str):
    """Convert '31.12.2025' to '2025-12-31'."""
    if not date_str:
        return False
    s = date_str.replace(' ', '')
    parts = s.split('.')
    if len(parts) == 3:
        try:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            return f'{y:04d}-{m:02d}-{d:02d}'
        except ValueError:
            pass
    return False


class L10nSiOcrDocument(models.Model):
    _name = 'l10n_si.ocr.document'
    _description = 'Slovenian OCR Document'
    _order = 'create_date DESC'

    name = fields.Char(required=True)
    state = fields.Selection(
        selection=[('pending', 'V čakalni vrsti'),
                   ('processing', 'V obdelavi'),
                   ('extracted', 'Podatki izvlečeni'),
                   ('posted', 'Knjižen'),
                   ('error', 'Napaka')],
        default='pending',
        tracking=True,
    )

    # Input
    pdf_attachment_id = fields.Many2one('ir.attachment', required=True, ondelete='restrict')
    page_count = fields.Integer(default=1)

    # Extracted
    extracted_text = fields.Text(readonly=True)
    confidence = fields.Float(readonly=True, help='0.0 to 1.0')
    partner_id = fields.Many2one('res.partner', string='Dobavitelj')
    invoice_number = fields.Char(readonly=True)
    invoice_date = fields.Date(readonly=True)
    date_due = fields.Date(readonly=True)
    amount_untaxed = fields.Monetary(readonly=True, currency_field='currency_id')
    amount_tax = fields.Monetary(readonly=True, currency_field='currency_id')
    amount_total = fields.Monetary(readonly=True, currency_field='currency_id')
    vat_number = fields.Char(readonly=True, help='SI VAT detected on the invoice')
    iban = fields.Char(readonly=True)
    tax_rate_detected = fields.Float(readonly=True, help='Detected tax rate %')

    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id, required=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Output
    move_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)
    error_message = fields.Text(readonly=True)

    def action_run_ocr(self):
        """Run OCR on the document and extract structured data."""
        for doc in self:
            doc.state = 'processing'
            try:
                text = doc._run_ocr_backend()
                doc.extracted_text = text
                doc._extract_fields(text)
                doc.state = 'extracted'

                if doc.company_id.si_ocr_auto_create_bill:
                    doc.action_create_bill()
            except Exception as e:  # noqa: BLE001
                doc.write({
                    'state': 'error',
                    'error_message': str(e),
                })

    def _run_ocr_backend(self):
        """Run OCR based on company config."""
        self.ensure_one()
        company = self.company_id
        pdf_data = base64.b64decode(self.pdf_attachment_id.datas)

        if company.si_ocr_backend == 'tesseract':
            return self._run_tesseract(pdf_data)
        elif company.si_ocr_backend == 'google_docai':
            return self._run_google_docai(pdf_data)
        elif company.si_ocr_backend == 'aws_textract':
            return self._run_aws_textract(pdf_data)
        else:
            return ''

    def _run_tesseract(self, pdf_data):
        """Use local Tesseract to extract text."""
        # Convert PDF to images using pdftoppm, then OCR each with tesseract
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, 'input.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)

            # Convert PDF to PNG pages
            try:
                subprocess.run(
                    ['pdftoppm', '-png', '-r', '300', pdf_path, 'page'],
                    cwd=tmpdir, check=True, capture_output=True, timeout=120,
                )
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise UserError(_('pdftoppm not installed. Install poppler-utils.')) from e

            # OCR each page
            all_text = []
            for page_file in sorted(os.listdir(tmpdir)):
                if not page_file.startswith('page') or not page_file.endswith('.png'):
                    continue
                page_path = os.path.join(tmpdir, page_file)
                try:
                    result = subprocess.run(
                        ['tesseract', page_path, '-', '-l', 'slv+eng'],
                        capture_output=True, timeout=60,
                    )
                    all_text.append(result.stdout.decode('utf-8', errors='replace'))
                    self.page_count += 1
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    _logger.warning('Tesseract failed for %s: %s', page_file, e)
                    continue

            return '\n---\n'.join(all_text)

    def _run_google_docai(self, pdf_data):
        """Run Google Document AI OCR (placeholder — requires google-cloud-documentai)."""
        # Real implementation would call google.cloud.documentai
        # For now, log and fall back to Tesseract
        _logger.info('Google Document AI not configured, falling back to Tesseract')
        return self._run_tesseract(pdf_data)

    def _run_aws_textract(self, pdf_data):
        """Run AWS Textract OCR (placeholder — requires boto3)."""
        _logger.info('AWS Textract not configured, falling back to Tesseract')
        return self._run_tesseract(pdf_data)

    def _extract_fields(self, text):
        """Extract structured data from OCR text using SI regex patterns."""
        self.ensure_one()

        # VAT
        vat_match = SI_PATTERNS['vat'].search(text)
        if vat_match:
            self.vat_number = 'SI' + vat_match.group(1)
            # Try to find matching partner
            partner = self.env['res.partner'].search([
                ('vat', '=', self.vat_number),
                '|', ('is_company', '=', True), ('parent_id', '!=', False),
            ], limit=1)
            if partner:
                self.partner_id = partner.id

        # Invoice number
        inv_match = SI_PATTERNS['invoice_number'].search(text)
        if inv_match:
            self.invoice_number = inv_match.group(1)

        # Dates
        issue_match = SI_PATTERNS['issue_date'].search(text)
        if issue_match:
            self.invoice_date = _parse_si_date(issue_match.group(1))

        due_match = SI_PATTERNS['due_date'].search(text)
        if due_match:
            self.date_due = _parse_si_date(due_match.group(1))

        # Amounts
        total_match = SI_PATTERNS['total'].search(text)
        if total_match:
            self.amount_total = _parse_si_amount(total_match.group(1))

        untaxed_match = SI_PATTERNS['untaxed'].search(text)
        if untaxed_match:
            self.amount_untaxed = _parse_si_amount(untaxed_match.group(1))

        tax_match = SI_PATTERNS['tax'].search(text)
        if tax_match:
            self.amount_tax = _parse_si_amount(tax_match.group(1))

        # If no untaxed but have total+tax, compute
        if self.amount_total and self.amount_tax and not self.amount_untaxed:
            self.amount_untaxed = self.amount_total - self.amount_tax

        # IBAN
        iban_match = SI_PATTERNS['iban'].search(text)
        if iban_match:
            self.iban = ''.join(iban_match.groups())

        # Tax rate (heuristic: 22% if amount_tax/amount_untaxed ≈ 0.22)
        if self.amount_untaxed and self.amount_tax:
            rate = self.amount_tax / self.amount_untaxed
            if abs(rate - 0.22) < 0.02:
                self.tax_rate_detected = 22.0
            elif abs(rate - 0.095) < 0.01:
                self.tax_rate_detected = 9.5
            elif abs(rate - 0.05) < 0.01:
                self.tax_rate_detected = 5.0

        # Confidence: rough estimate based on how many fields were extracted
        filled = sum(1 for f in ['vat_number', 'invoice_number', 'invoice_date',
                                 'amount_total', 'amount_untaxed']
                     if getattr(self, f))
        self.confidence = filled / 5.0

    def action_create_bill(self):
        """Create draft account.move from extracted data."""
        for doc in self:
            if not doc.partner_id:
                raise UserError(_('Cannot create bill: supplier not detected.'))
            move = self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': doc.partner_id.id,
                'invoice_date': doc.invoice_date or fields.Date.today(),
                'date': doc.invoice_date or fields.Date.today(),
                'invoice_date_due': doc.date_due,
                'company_id': doc.company_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': f'OCR: {doc.invoice_number or doc.name}',
                    'price_unit': doc.amount_untaxed,
                    'tax_ids': [(6, 0, self._get_default_tax(doc.tax_rate_detected))],
                })],
            })
            doc.write({'move_id': move.id, 'state': 'posted'})

    def _get_default_tax(self, rate):
        """Find a purchase tax matching the detected rate."""
        if not rate:
            return []
        Tax = self.env['account.tax']
        tax = Tax.search([
            ('amount', '=', rate),
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        return [tax.id] if tax else []
