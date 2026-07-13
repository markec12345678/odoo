# -*- coding: utf-8 -*-
"""Quick upload + sign wizard — sign a single document immediately."""

from odoo import fields, models


class L10nSiSignUploadWizard(models.TransientModel):
    _name = 'l10n_si.sign.upload.wizard'
    _description = 'Quick Sign Wizard'

    name = fields.Char(required=True)
    partner_id = fields.Many2one('res.partner')
    document = fields.Binary(required=True)
    document_filename = fields.Char()
    note = fields.Text()

    def action_sign(self):
        """Create a request and immediately sign with the company cert."""
        self.ensure_one()
        company = self.env.company
        attachment = self.env['ir.attachment'].create({
            'name': self.document_filename or 'document.pdf',
            'type': 'binary',
            'datas': self.document,
            'mimetype': 'application/pdf',
        })
        req = self.env['l10n_si.sign.request'].create({
            'name': self.name,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'company_id': company.id,
            'document_attachment_id': attachment.id,
            'workflow_type': 'sequential',
            'notes': self.note,
        })
        sig = self.env['l10n_si.sign.signature'].create({
            'request_id': req.id,
            'signer_user_id': self.env.user.id,
            'role': 'employee',
        })
        req.action_send()
        sig.action_sign()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_si.sign.request',
            'res_id': req.id,
            'view_mode': 'form',
            'target': 'current',
        }
