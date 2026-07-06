# -*- coding: utf-8 -*-
"""Camping reservation hooks: auto-register/deregister guests with AJPES."""
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class L10nSiCampingReservation(models.Model):
    _inherit = 'l10n_si.camping.reservation'

    def action_check_in(self):
        result = super().action_check_in()
        self._l10n_si_etourism_register_guests()
        return result

    def action_check_out(self):
        self._l10n_si_etourism_deregister_guests()
        return super().action_check_out()

    def _l10n_si_etourism_get_establishment(self):
        self.ensure_one()
        return self.env['l10n_si.etourism.establishment'].search([
            ('company_id', '=', self.company_id.id), ('active', '=', True),
            ('establishment_type', '=', 'camp'),
        ], limit=1)

    def _l10n_si_etourism_register_guests(self):
        Registration = self.env['l10n_si.etourism.guest.registration']
        for res in self:
            if not res.company_id.l10n_si_etourism_auto_register:
                continue
            establishment = res._l10n_si_etourism_get_establishment()
            if not establishment or not establishment.auto_register:
                continue
            existing = Registration.search([
                ('camping_reservation_id', '=', res.id), ('partner_id', '=', res.partner_id.id),
                ('ajpes_status', 'in', ['draft', 'pending', 'submitted']),
            ])
            if existing:
                continue
            reg = Registration.create({
                'establishment_id': establishment.id, 'partner_id': res.partner_id.id,
                'arrival_date': res.check_in, 'camping_reservation_id': res.id,
                'res_model': 'l10n_si.camping.reservation', 'res_id': res.id, 'company_id': res.company_id.id,
                'purpose': 'leisure',
            })
            reg.action_submit_to_ajpes()

    def _l10n_si_etourism_deregister_guests(self):
        Registration = self.env['l10n_si.etourism.guest.registration']
        for res in self:
            if not res.company_id.l10n_si_etourism_auto_deregister:
                continue
            regs = Registration.search([('camping_reservation_id', '=', res.id), ('ajpes_status', '=', 'submitted')])
            for reg in regs:
                reg.departure_date = res.check_out
                reg.action_deregister_with_ajpes()
