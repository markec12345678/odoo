# -*- coding: utf-8 -*-
"""Croatian business premise (poslovni prostor)."""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class L10nHrBusinessPremise(models.Model):
    _name = 'l10n_hr.business.premise'
    _description = 'Croatian Business Premise (Poslovni prostor)'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, size=20, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    active = fields.Boolean(default=True)

    street = fields.Char(string='Ulica i broj')
    zip = fields.Char(string='Poštanski broj')
    city = fields.Char(string='Naselje')
    country_id = fields.Many2one(
        'res.country', string='Država',
        default=lambda self: self.env.ref('base.hr').id, required=True,
    )

    work_mon_start = fields.Char(string='Ponedjeljak od', default='08:00')
    work_mon_end = fields.Char(string='Ponedjeljak do', default='20:00')
    work_tue_start = fields.Char(string='Utorak od', default='08:00')
    work_tue_end = fields.Char(string='Utorak do', default='20:00')
    work_wed_start = fields.Char(string='Srijeda od', default='08:00')
    work_wed_end = fields.Char(string='Srijeda do', default='20:00')
    work_thu_start = fields.Char(string='Četvrtak od', default='08:00')
    work_thu_end = fields.Char(string='Četvrtak do', default='20:00')
    work_fri_start = fields.Char(string='Petak od', default='08:00')
    work_fri_end = fields.Char(string='Petak do', default='20:00')
    work_sat_start = fields.Char(string='Subota od', default='08:00')
    work_sat_end = fields.Char(string='Subota do', default='14:00')
    work_sun_start = fields.Char(string='Nedjelja od')
    work_sun_end = fields.Char(string='Nedjelja do')

    premise_type = fields.Selection(
        selection=[('permanentni', 'Stalni poslovni prostor'),
                   ('privremeni', 'Privremeni prostor'),
                   ('prijenosni', 'Prijenosni uređaj')],
        required=True, default='permanentni',
    )

    cisf_uuid = fields.Char(string='CISF UUID (oznaka_pp)', readonly=True, copy=False)
    cisf_registered_at = fields.Datetime(readonly=True, copy=False)

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'Premise code must be unique per company.'),
    ]

    @api.constrains('code')
    def _check_code(self):
        for p in self:
            if not p.code or not p.code.strip():
                raise ValidationError(_('Premise code cannot be empty.'))

    def action_register_with_cisf(self):
        """Submit poslovniProstorZahtjev to CISF via SOAP."""
        import tempfile
        import base64
        import os as _os
        from .cisf_client import (
            CISFClient, CISFAuthError, CISFValidationError,
            CISFConnectionError, CISFUnknownError,
            extract_pfx_to_pem, build_premise_xml,
        )

        Log = self.env['l10n_hr.fiscal.log']
        for premise in self:
            company = premise.company_id
            if not company.hr_fiscal_certificate:
                premise.message_post(body=_('Cannot register: FINA certificate not configured.'))
                continue

            address = {
                'street': premise.street or '',
                'zip': premise.zip or '',
                'city': premise.city or '',
                'country_code': premise.country_id.code if premise.country_id else 'HR',
            }
            working_hours = {
                'mon': (premise.work_mon_start or '', premise.work_mon_end or ''),
                'tue': (premise.work_tue_start or '', premise.work_tue_end or ''),
                'wed': (premise.work_wed_start or '', premise.work_wed_end or ''),
                'thu': (premise.work_thu_start or '', premise.work_thu_end or ''),
                'fri': (premise.work_fri_start or '', premise.work_fri_end or ''),
                'sat': (premise.work_sat_start or '', premise.work_sat_end or ''),
            }
            if premise.work_sun_start:
                working_hours['sun'] = (premise.work_sun_start, premise.work_sun_end or '')

            premise_xml = build_premise_xml(
                oib=(company.vat or '').strip(),
                premise_code=premise.code,
                address=address,
                working_hours=working_hours,
                premise_type=premise.premise_type,
            )
            log_vals = {
                'company_id': company.id,
                'request_type': 'premise',
                'request_xml': premise_xml,
                'state': 'draft',
            }

            pfx_temp = None
            try:
                pfx_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
                pfx_temp.write(base64.b64decode(company.hr_fiscal_certificate))
                pfx_temp.close()
                cert_pem, key_pem = extract_pfx_to_pem(
                    pfx_temp.name, company.hr_fiscal_certificate_password or '',
                )
                client = CISFClient(
                    cert_pem_path=cert_pem, key_pem_path=key_pem,
                    environment=company.hr_fiscal_environment,
                )
                _, raw_response = client.register_premise(premise_xml)
                premise.write({'cisf_registered_at': fields.Datetime.now()})
                log_vals.update({'state': 'sent', 'response_xml': raw_response, 'http_status': 200})
                Log.create(log_vals)
                premise.message_post(body=_('Premise %s registered with CISF.') % premise.code)
            except (CISFAuthError, CISFValidationError, CISFConnectionError, CISFUnknownError) as e:
                _logger.warning('CISF premise registration failed for %s: %s', premise.code, e)
                log_vals.update({'state': 'error', 'error_message': str(e)})
                Log.create(log_vals)
                premise.message_post(body=_('CISF registration failed: %s') % str(e))
            except Exception as e:
                _logger.exception('Unexpected error registering premise %s', premise.code)
                log_vals.update({'state': 'error', 'error_message': str(e)})
                Log.create(log_vals)
            finally:
                if pfx_temp and _os.path.exists(pfx_temp.name):
                    _os.unlink(pfx_temp.name)
