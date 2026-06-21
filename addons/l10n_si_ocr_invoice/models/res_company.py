# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_ocr_backend = fields.Selection(
        selection=[('tesseract', 'Tesseract (lokalno, brezplačno)'),
                   ('google_docai', 'Google Document AI (plačano, 95%+)'),
                   ('aws_textract', 'AWS Textract (plačano)')],
        default='tesseract',
        string='OCR backend',
    )
    si_ocr_google_project_id = fields.Char(string='Google Project ID')
    si_ocr_google_processor_id = fields.Char(string='Google Processor ID')
    si_ocr_google_credentials = fields.Binary(string='Google service account JSON')
    si_ocr_auto_create_bill = fields.Boolean(
        string='Auto-create bill',
        default=False,
        help='If True, creates account.move draft immediately after OCR. If False, '
             'user reviews extracted data first.',
    )
