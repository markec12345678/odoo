# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

try:
    import qrcode
except ImportError:
    qrcode = None
    _logger.warning("qrcode library not installed — HUB3 QR codes will not be generated. "
                    "Run: pip install qrcode")


class AccountMove(models.Model):
    _inherit = "account.move"

    hub3_qr_code = fields.Binary(
        string="HUB3 QR Code",
        readonly=True,
        copy=False,
        help="HUB3 standard QR code for Croatian bank payments.",
    )
    hub3_string = fields.Char(
        readonly=True,
        copy=False,
        help="The raw HUB3 string encoded in the QR code.",
    )

    def action_generate_hub3_qr(self):
        """Generate the HUB3 QR code for this invoice."""
        for move in self:
            if move.move_type not in ("out_invoice", "out_refund"):
                continue
            hub3_str = move._build_hub3_string()
            if not hub3_str:
                continue
            if qrcode is None:
                _logger.warning("Cannot generate HUB3 QR: qrcode library not installed.")
                continue
            try:
                qr = qrcode.QRCode(
                    version=None,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=6,
                    border=2,
                )
                qr.add_data(hub3_str)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                move.write(
                    {
                        "hub3_qr_code": base64.b64encode(buf.getvalue()).decode(),
                        "hub3_string": hub3_str,
                    }
                )
            except Exception as e:  # noqa: BLE001
                _logger.error("HUB3 QR generation failed for move %s: %s", move.name, e)

    def _build_hub3_string(self):
        """Build the HUB3 string for this invoice.

        Format: HUB|Iznos|IBAN|Model|PozivNaBroj|NazivPrimaoca|Opis|SifraValute|
        """
        self.ensure_one()
        if not self.partner_bank_id or not self.partner_bank_id.acc_number:
            return False
        # Format amount with 2 decimals, comma as decimal separator
        amount = abs(self.amount_residual or self.amount_total)
        # HUB3 expects format: 000000123456 (14 digits, no decimal point, last 2 = decimals)
        amount_str = f"{int(round(amount * 100)):014d}"
        iban = self.partner_bank_id.sanitized_acc_number or ""
        # Croatian payment model (e.g. "HR01" or "01")
        model = getattr(self.partner_bank_id, "payment_model", "") or ""
        # Reference / call number (poziv na broj)
        reference = (self.payment_reference or self.name or "").replace("/", "")
        payee = self.company_id.name or ""
        # Truncate payee to 30 chars per HUB3 spec
        if len(payee) > 30:
            payee = payee[:30]
        description = (self.name or "")[:30]
        currency = self.currency_id.name or "EUR"
        # Build HUB3 string
        parts = [
            "HUB",
            amount_str,
            iban,
            model,
            reference,
            payee,
            description,
            currency,
        ]
        return "|".join(parts) + "|"

    def action_post(self):
        """Override to generate HUB3 QR code after invoice confirmation."""
        result = super().action_post()
        for move in self:
            if move.move_type in ("out_invoice", "out_refund"):
                move.action_generate_hub3_qr()
        return result
