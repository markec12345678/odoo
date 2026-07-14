# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def validate_oib(oib):
    """Validate a Croatian OIB (Osobni identifikacijski broj).

    OIB is 11 digits. Validation uses ISO 7064 MOD 11-10 checksum:
    1. Start with r = 10
    2. For each of the first 10 digits:
       r = (r + digit) % 10
       if r == 0: r = 10
       r = (r * 2) % 11
    3. Checksum: r = 11 - r
       if r == 10: r = 0
    4. The 11th digit must equal r.

    Returns True if valid, False otherwise.
    """
    if not oib:
        return False
    oib = str(oib).strip().replace(" ", "").replace("-", "")
    if len(oib) != 11 or not oib.isdigit():
        return False
    digits = [int(c) for c in oib]
    r = 10
    for d in digits[:10]:
        r = (r + d) % 10
        if r == 0:
            r = 10
        r = (r * 2) % 11
    checksum = (11 - r) % 11
    if checksum == 10:
        checksum = 0
    return checksum == digits[10]


class ResPartner(models.Model):
    _inherit = "res.partner"

    # OIB — Croatian personal ID
    oib = fields.Char(
        string="OIB",
        size=11,
        help="Croatian Personal Identification Number (Osobni identifikacijski broj). "
             "11 digits with ISO 7064 MOD 11-10 checksum.",
    )
    oib_valid = fields.Boolean(
        compute="_compute_oib_valid",
        store=False,
    )
    # HR-specific partner categories
    is_croatian_resident = fields.Boolean(
        compute="_compute_is_croatian_resident",
        store=True,
        help="True if partner's country is Croatia.",
    )
    is_related_party = fields.Boolean(
        default=False,
        help="Povezano lice — related party for accounting disclosures.",
    )
    is_vat_registered = fields.Boolean(
        default=False,
        help="Partner is registered for Croatian VAT (PDV).",
    )

    @api.depends("oib")
    def _compute_oib_valid(self):
        for p in self:
            p.oib_valid = validate_oib(p.oib) if p.oib else False

    @api.depends("country_id")
    def _compute_is_croatian_resident(self):
        croatia = self.env.ref("base.hr", raise_if_not_found=False) or \
            self.env["res.country"].search([("code", "=", "HR")], limit=1)
        for p in self:
            p.is_croatian_resident = bool(croatia and p.country_id == croatia)

    @api.constrains("oib")
    def _check_oib(self):
        for partner in self:
            if partner.oib and not validate_oib(partner.oib):
                raise ValidationError(
                    _("Invalid OIB '%s' for partner %s. "
                      "OIB must be 11 digits with valid ISO 7064 MOD 11-10 checksum.")
                    % (partner.oib, partner.name or "")
                )

    @api.onchange("oib")
    def _onchange_oib(self):
        if self.oib and not validate_oib(self.oib):
            return {
                "warning": {
                    "title": _("Invalid OIB"),
                    "message": _("The OIB '%s' is not valid. "
                                 "Please check the 11-digit number.") % self.oib,
                }
            }
