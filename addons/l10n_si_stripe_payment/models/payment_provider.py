import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    def _stripe_make_payment_request(self, amount, currency_id, partner_id, **kwargs):
        """Override to support SI deposit mode (pre-authorization)."""
        if self.code != 'stripe':
            return super()._stripe_make_payment_request(amount, currency_id, partner_id, **kwargs)

        company = self.env.company
        if company.si_stripe_deposit_mode and kwargs.get('capture_method') != 'automatic':
            kwargs['capture_method'] = 'manual'

        return super()._stripe_make_payment_request(amount, currency_id, partner_id, **kwargs)
