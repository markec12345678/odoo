# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

import requests

from odoo import _, api, exceptions, models

_logger = logging.getLogger(__name__)

# Slovenian VAT number: SI + 8 digits where the last digit is a MOD11 checksum.
# Format defined by ZDavR-1, 23. člen.
_SI_VAT_RE = re.compile(r'^SI\s*(\d{8})$', re.IGNORECASE)


def _si_mod11_check(digits8: str) -> bool:
    """Validate an 8-digit Slovenian VAT number using MOD11 (FURS spec).

    Algorithm (FURS Pravilnik o davčnih številkah):
        weights = [8, 7, 6, 5, 4, 3, 2] applied to the first 7 digits
        s = sum(d_i * w_i)
        remainder = s % 11
        checksum = 11 - remainder
        if checksum == 10: invalid
        if checksum == 11: checksum = 0
        The 8th digit must equal `checksum`.

    Args:
        digits8: exactly 8 numeric characters (no 'SI' prefix).

    Returns:
        True if the number passes MOD11, False otherwise.
    """
    if len(digits8) != 8 or not digits8.isdigit():
        return False

    weights = [8, 7, 6, 5, 4, 3, 2]
    s = sum(int(digits8[i]) * weights[i] for i in range(7))
    remainder = s % 11
    checksum = 11 - remainder
    if checksum == 10:
        return False
    if checksum == 11:
        checksum = 0
    return int(digits8[7]) == checksum


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # NOTE: Odoo's base_vat already provides `vat` validation via `simple_vat_check`.
    # We extend it by overriding `_run_vat_test` for SI country and adding FURS lookup.

    @api.constrains('vat', 'country_id')
    def _check_si_vat_format(self):
        """Hard constraint: SI VAT numbers must pass MOD11."""
        for partner in self:
            if not partner.vat or not partner.country_id:
                continue
            if partner.country_id.code != 'SI':
                continue
            match = _SI_VAT_RE.match(partner.vat.strip())
            if not match:
                raise exceptions.ValidationError(_(
                    'Slovenian VAT number must be in the format SI######## (8 digits).\n'
                    'Got: %s'
                ) % partner.vat)
            if not _si_mod11_check(match.group(1)):
                raise exceptions.ValidationError(_(
                    'Slovenian VAT number %s failed the MOD11 checksum.\n'
                    'Please verify the number with FURS.'
                ) % partner.vat)

    def _si_check_vat_with_furs(self):
        """Query FURS REST API to verify the VAT number is active.

        Returns (ok: bool, message: str). Network or cert errors return (True, 'skipped')
        so that we never block partner save due to transient FURS issues.
        """
        self.ensure_one()
        if not self.vat or not self.country_id or self.country_id.code != 'SI':
            return True, 'not_applicable'

        company = self.env.company
        if not company.si_vat_check_enabled:
            return True, 'disabled'

        match = _SI_VAT_RE.match(self.vat.strip())
        if not match:
            return False, 'invalid_format'

        vat_number = match.group(1)
        cert_path, key_path = company._si_get_cert_paths()
        if not cert_path:
            _logger.warning('FURS VAT check enabled but no certificate configured')
            return True, 'no_cert'

        endpoint = company._si_get_vat_endpoint()
        url = f'{endpoint}invoices/{vat_number}'
        try:
            response = requests.get(
                url,
                cert=(cert_path, key_path),
                timeout=10,
                headers={'Accept': 'application/json'},
                verify=True,
            )
            if response.status_code == 200:
                return True, 'valid'
            if response.status_code == 404:
                return False, 'vat_not_found'
            _logger.warning('FURS VAT check returned HTTP %s', response.status_code)
            return True, f'http_{response.status_code}'
        except requests.RequestException as e:
            _logger.warning('FURS VAT check failed: %s', e)
            return True, 'network_error'

    def action_si_check_vat(self):
        """Manual action: check the partner's VAT against FURS and notify."""
        self.ensure_one()
        ok, reason = self._si_check_vat_with_furs()
        if ok and reason in ('valid',):
            msg_type, title, body = 'success', _('VAT valid'), _(
                'FURS confirms that VAT number %s is registered and active.',
            ) % self.vat
        elif ok and reason in ('disabled', 'no_cert', 'network_error', 'not_applicable'):
            msg_type, title, body = 'warning', _('Check skipped'), _(
                'FURS check was skipped. Reason: %(reason)s', reason=reason,
            )
        else:
            msg_type, title, body = 'danger', _('VAT invalid'), _(
                'FURS reports VAT number %(vat)s as not registered. Reason: %(reason)s',
                vat=self.vat, reason=reason,
            )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': title, 'message': body, 'type': msg_type, 'sticky': False},
        }

    @api.onchange('vat', 'country_id')
    def _onchange_si_vat_warn(self):
        """Soft warning in UI — hard error is in `_check_si_vat_format`."""
        for partner in self:
            if not partner.vat or not partner.country_id or partner.country_id.code != 'SI':
                continue
            ok, reason = partner._si_check_vat_with_furs()
            if not ok:
                return {
                    'warning': {
                        'title': _('VAT check failed'),
                        'message': _('FURS reports VAT number %s as not registered. '
                                     'Reason: %s') % (partner.vat, reason),
                    }
                }
