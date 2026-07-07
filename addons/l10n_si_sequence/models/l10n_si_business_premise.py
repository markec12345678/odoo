# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiBusinessPremise(models.Model):
    """Slovenian 'poslovni prostor' registered with FURS.

    Each premise has a unique code (e.g. 'BL1', 'POS1') that is registered with
    FURS before any invoice is issued from that premise.
    """
    _name = 'l10n_si.business.premise'
    _description = 'Slovenian Business Premise (FURS registration)'
    _order = 'company_id, code'

    name = fields.Char(string='Premise Name', required=True, translate=True)
    code = fields.Char(
        string='Premise Code',
        required=True,
        help='Short code identifying this premise in invoice numbers. '
             'Must match the FURS registration. Max 20 chars.',
        size=20,
    )
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                  default=lambda self: self.env.company)
    street = fields.Char(string='Street', required=True)
    street2 = fields.Char(string='Street2')
    zip = fields.Char(string='Postal Code', required=True, size=10)
    city = fields.Char(string='City', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True,
                                  default=lambda self: self.env.ref('base.si'))
    furs_premise_id = fields.Char(
        string='FURS Premise ID',
        help='Internal FURS identifier returned after registration. '
             'Leave empty if not yet registered.',
        readonly=True,
        copy=False,
    )
    furs_registered_on = fields.Datetime(string='FURS Registered On', readonly=True, copy=False)
    active = fields.Boolean(default=True)
    electronic_device_ids = fields.One2many(
        'l10n_si.electronic.device', 'business_premise_id', string='Electronic Devices',
    )
    device_count = fields.Integer(compute='_compute_device_count', store=True)

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'Premise code must be unique per company.'),
    ]

    @api.depends('electronic_device_ids')
    def _compute_device_count(self):
        for premise in self:
            premise.device_count = len(premise.electronic_device_ids)

    def action_view_devices(self):
        """Open the electronic devices view filtered by this premise."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Electronic Devices'),
            'res_model': 'l10n_si.electronic.device',
            'view_mode': 'list,form',
            'domain': [('business_premise_id', '=', self.id)],
            'context': {
                'default_business_premise_id': self.id,
                'search_default_business_premise_id': self.id,
            },
        }

    @api.constrains('code')
    def _check_code_format(self):
        for premise in self:
            if not premise.code or not premise.code.isalnum():
                raise ValidationError(_(
                    'Premise code must be alphanumeric (no spaces or special chars). Got: %s',
                ) % premise.code)

    def action_register_with_furs(self):
        """Stub: real FURS registration is performed by `l10n_si_fiscal`.
        This button is overridden in that module when installed.
        """
        self.ensure_one()
        if self.furs_premise_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Already registered'),
                    'message': _('Premise %s was registered with FURS on %s.') % (
                        self.code, self.furs_registered_on,
                    ),
                    'type': 'info',
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('FURS module required'),
                'message': _('Install l10n_si_fiscal to perform FURS registration.'),
                'type': 'warning',
            },
        }
