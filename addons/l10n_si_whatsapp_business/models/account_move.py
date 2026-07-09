from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_send_whatsapp(self):
        """Send invoice summary via WhatsApp."""
        self.ensure_one()
        partner = self.partner_id
        if not partner.mobile and not partner.phone:
            return False
        phone = (partner.mobile or partner.phone).replace('+', '').replace(' ', '').replace('-', '')
        body = f"Račun {self.name}\nZnesek: {self.amount_total:.2f} {self.currency_id.name}\nDatum: {self.invoice_date}\nHvala za vaše zaupanje!"
        msg = self.env['wa.message'].create({
            'partner_id': partner.id,
            'phone': phone,
            'message_body': body,
            'company_id': self.company_id.id,
        })
        msg.action_send()
        return True
