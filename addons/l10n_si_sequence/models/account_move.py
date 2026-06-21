# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_si_business_premise_id = fields.Many2one(
        'l10n_si.business.premise', string='SI Business Premise',
        compute='_compute_si_premise', store=True, readonly=False,
        help='Used for SI invoice numbering. Auto-filled from the journal.',
    )
    l10n_si_electronic_device_id = fields.Many2one(
        'l10n_si.electronic.device', string='SI Device',
        compute='_compute_si_premise', store=True, readonly=False,
    )
    l10n_si_sequence_number = fields.Char(
        string='SI Sequence Number', copy=False, readonly=True,
        help='The full SI-formatted number assigned to this invoice (BL1-KASA1-2025-00001).',
    )

    @api.depends('journal_id', 'move_type', 'company_id')
    def _compute_si_premise(self):
        """Auto-fill premise+device from the journal's default (set per company)."""
        for move in self:
            if move.move_type not in ('out_invoice', 'out_refund', 'out_receipt'):
                move.l10n_si_business_premise_id = False
                move.l10n_si_electronic_device_id = False
                continue
            company = move.company_id
            if company.l10n_si_default_premise_id:
                move.l10n_si_business_premise_id = company.l10n_si_default_premise_id
            if company.l10n_si_default_device_id:
                move.l10n_si_electronic_device_id = company.l10n_si_default_device_id

    def _get_si_sequence(self):
        """Return the ir.sequence to use for this move, or False if not configured."""
        self.ensure_one()
        if not self.l10n_si_electronic_device_id:
            return False
        return self.l10n_si_electronic_device_id._get_or_create_yearly_sequence()

    def _post(self, soft=True):
        """Override posting to assign the SI sequence number before the standard post."""
        for move in self:
            if (move.move_type in ('out_invoice', 'out_refund', 'out_receipt')
                    and move.company_id.country_id.code == 'SI'
                    and not move.l10n_si_sequence_number
                    and move.l10n_si_electronic_device_id):
                seq = move._get_si_sequence()
                if seq:
                    move.l10n_si_sequence_number = seq.next_by_id()
                    # Use the SI number as the official invoice name if not yet set.
                    if not move.name or move.name == '/':
                        move.name = move.l10n_si_sequence_number
        return super()._post(soft=soft)
