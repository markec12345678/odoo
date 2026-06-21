# -*- coding: utf-8 -*-
{
    'name': 'Slovenian OCR Invoice Import',
    'summary': 'OCR-scan supplier invoices into draft bills — Tesseract or cloud OCR',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian OCR Invoice Import
=============================

Scan PDF/images of supplier invoices and auto-extract data into draft bills.

Features:
* Two OCR backends:
    1. **Tesseract** (free, local) — 70-80% accuracy
    2. **Google Document AI** (paid, ~10€ per 1000 pages) — 95%+ accuracy
* Auto-detect:
    - Supplier by VAT or IBAN
    - Invoice number
    - Issue date + due date
    - Amounts (untaxed, tax, total)
    - Tax rates (22%, 9.5%, 5%, 0%)
* SI-specific parsing:
    - "Davčna številka: SI12345678"
    - "Skupaj za plačilo: 1.234,56 EUR"
    - "Plačilo do: 31.12.2025"
* Multi-page PDF support
* Confidence score per field
* Manual correction before posting
* Multi-supplier learning (remembers corrections per supplier)

Replaces Enterprise `account_ocr`.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_ocr_document_views.xml',
        'wizard/l10n_si_ocr_upload_wizard_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
