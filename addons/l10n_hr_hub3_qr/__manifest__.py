# -*- coding: utf-8 -*-
{
    "name": "HR HUB3 QR Code",
    "version": "19.0.1.0.0",
    "summary": "Generates HUB3 (HRK) QR code for Croatian bank payments. "
    "Customer scans QR code with bank app — all payment fields auto-filled.",
    "description": """
HR HUB3 QR Code
===============

Generates the HUB3 standard QR code that Croatian banks recognize for
instant payments. The customer scans the QR code with their bank app
and all payment fields are automatically filled (IBAN, amount, model,
reference, payee, description).

The HUB3 format is defined by the Croatian Banking Association (HUB)
and is widely supported by all Croatian banks (Zagrebačka, PBZ, RBA,
Erste, Addiko, OTP, etc.).

Format: HUB3 string with pipe-separated fields:
  HUB|Iznos|IBAN|Model|PozivNaBroj|NazivPrimaoca|Opis|SifraValute|

This module:
1. Adds a `hub3_qr_code` Binary field on account.move (out_invoice)
2. Generates the QR code automatically on invoice confirmation
3. Displays the QR code on the printed invoice PDF
4. Provides a button to regenerate if data changes

Integrates with:
  * account (invoice)
  * l10n_hr (Croatian company data — IBAN, model, reference)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Payment",
    "depends": ["account", "l10n_hr"],
    "external_dependencies": {
        "python": ["qrcode"],
    },
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "reports/invoice_report.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
