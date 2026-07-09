{
    'name': 'Stripe Payment (SI)',
    'summary': 'Stripe payment integration for hotel bookings and online deposits',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment',
    'description': """
Stripe Payment (SI)
===================

Extends the standard Odoo Stripe payment provider with SI-specific features:
* Pre-authorization for hotel deposits (hold amount on card, capture at check-out)
* Automatic payment link generation for booking confirmations
* Multi-currency support (EUR, HRK legacy)
* Stripe webhook handling for payment status updates
* Integration with l10n_si_hotel folio system

Configuration:
    * Settings → Payment Providers → Stripe
    * Enter Publishable Key and Secret Key from Stripe Dashboard
    * Enable 'SI Hotel Deposits' for pre-authorization mode

Requires:
    * payment_stripe (Odoo core)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['payment_stripe', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_provider_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
}
