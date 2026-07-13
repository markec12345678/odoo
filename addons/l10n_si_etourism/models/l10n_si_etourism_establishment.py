# -*- coding: utf-8 -*-
"""AJPES nastanitveni obrat — RNO entry (MID + SIFNAS)."""
from odoo import _, fields, models


class L10nSiEtourismEstablishment(models.Model):
    _name = 'l10n_si.etourism.establishment'
    _description = 'Slovenian eTurizem Establishment (RNO)'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    mid = fields.Char(string='MID', required=True, size=20, tracking=True)
    sifnas = fields.Char(string='SIFNAS', required=True, size=20, tracking=True)
    establishment_type = fields.Selection(
        selection=[('hotel', 'Hotel/Gostilna s sobami'), ('apartment', 'Apartma'),
                   ('camp', 'Kamp'), ('farm', 'Kmečki turizem'),
                   ('private_room', 'Zasebne sobe'), ('yacht', 'Plovilo'), ('other', 'Drugo')],
        required=True, default='hotel', tracking=True,
    )
    partner_id = fields.Many2one('res.partner', string='Lastnik / Upravljalec')
    street = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    municipality_id = fields.Many2one('l10n_si.tourist.tax.municipality', string='Občina')
    country_id = fields.Many2one('res.country', string='Država', default=lambda self: self.env.ref('base.si').id, required=True)
    capacity_beds = fields.Integer(string='Ležišča', default=10)
    capacity_rooms = fields.Integer(string='Sobe / Enota', default=5)
    si_pass_username = fields.Char(string='SI-PASS uporabniško ime', tracking=True)
    si_pass_password = fields.Char(string='SI-PASS geslo', copy=False)
    environment = fields.Selection(
        selection=[('test', 'TEST'), ('prod', 'PROD')], default='test', required=True, tracking=True,
    )
    auto_register = fields.Boolean(string='Samodejna prijava gostov', default=True)
    auto_deregister = fields.Boolean(string='Samodejna odjava gostov', default=True)

    _sql_constraints = [
        ('mid_sifnas_company_uniq', 'unique(mid, sifnas, company_id)', 'MID + SIFNAS must be unique per company.'),
    ]

    def action_test_connection(self):
        """Test connectivity to AJPES eTurizem endpoint."""
        import requests
        self.ensure_one()
        url = self._get_endpoint()
        try:
            response = requests.head(url, timeout=10, verify=True)
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': _('Connection test'), 'message': _('Endpoint %s returned HTTP %d') % (url, response.status_code),
                               'type': 'success' if response.status_code < 500 else 'danger'}}
        except requests.RequestException as e:
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': _('Connection failed'), 'message': str(e), 'type': 'danger'}}

    def _get_endpoint(self):
        return ENDPOINT_PRODUCTION if self.environment == 'prod' else ENDPOINT_TEST


from .ajpes_client import ENDPOINT_PRODUCTION, ENDPOINT_TEST  # noqa: E402
