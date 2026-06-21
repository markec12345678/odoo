# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import shutil

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nSiBusinessPremise(models.Model):
    _inherit = 'l10n_si.business.premise'

    # Override the stub action_register_with_furs from l10n_si_sequence.
    def action_register_with_furs(self):
        """Register the premise with FURS via the SOAP API.

        FURS endpoint: POST /v1/cash_registers/business_premises
        Body (JSON):
        {
            "TaxNumber": "12345678",
            "PremiseID": "BL1",
            "ValidityDate": "2025-01-01",
            "Address": {
                "Street": "Slovenska 1",
                "HouseNumber": "1",
                "City": "Ljubljana",
                "PostalCode": "1000",
                "Country": "SI"
            },
            "TypeOfPremise": "C"  # A=poslovni prostor, B=samopostrežna, C=drugi
        }
        """
        self.ensure_one()
        company = self.company_id
        if not company.si_fiscal_certificate:
            raise UserError(_(
                'Configure the FURS certificate on company %s first.', company.name,
            ))

        cert_path, key_path, temp_dir = company.si_fiscal_get_cert_paths()
        if not cert_path:
            raise UserError(_('FURS certificate could not be parsed.'))

        try:
            payload = {
                'TaxNumber': int(self._extract_tax_number(company)),
                'PremiseID': self.code,
                'ValidityDate': fields.Date.today().isoformat(),
                'Address': {
                    'Street': self.street,
                    'HouseNumber': self._extract_house_number(),
                    'City': self.city,
                    'PostalCode': self.zip,
                    'Country': self.country_id.code or 'SI',
                },
                'TypeOfPremise': 'C',
            }
            url = company.si_fiscal_get_endpoint() + 'business_premises'
            response = requests.post(
                url, json=payload,
                cert=(cert_path, key_path),
                timeout=15,
                headers={'Content-Type': 'application/json'},
            )
            if response.status_code in (200, 201):
                self.write({
                    'furs_premise_id': self.code,  # FURS echoes back the premise ID
                    'furs_registered_on': fields.Datetime.now(),
                })
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Registered'),
                        'message': _('Premise %s is now registered with FURS.') % self.code,
                        'type': 'success',
                    },
                }
            raise UserError(_(
                'FURS premise registration failed (HTTP %s): %s',
            ) % (response.status_code, response.text))
        except requests.RequestException as e:
            raise UserError(_('FURS connection failed: %s') % e) from e
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_tax_number(self, company):
        """Extract 8-digit tax number from company.vat (strip 'SI' prefix)."""
        vat = (company.vat or '').upper().lstrip('SI').strip()
        if not vat.isdigit() or len(vat) != 8:
            raise UserError(_('Company %s has an invalid VAT number.') % company.name)
        return vat

    def _extract_house_number(self):
        """Pull the house number from the end of the street field."""
        if not self.street:
            return '1'
        parts = self.street.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[1]
        return '1'
