# -*- coding: utf-8 -*-
"""Quick upload wizard — upload PDF, run OCR immediately."""

from odoo import fields, models


class L10nSiOcrUploadWizard(models.TransientModel):
    _name = 'l10n_si.ocr.upload.wizard'
    _description = 'SI OCR Upload Wizard'

    name = fields.Char(required=True, default='New scan')
    pdf_file = fields.Binary(required=True, string='PDF')
    pdf_filename = fields.Char()
    auto_create_bill = fields.Boolean(default=False)

    def action_upload_and_ocr(self):
        self.ensure_one()
        attachment = self.env['ir.attachment'].create({
            'name': self.pdf_filename or 'invoice.pdf',
            'type': 'binary',
            'datas': self.pdf_file,
            'mimetype': 'application/pdf',
        })
        doc = self.env['l10n_si.ocr.document'].create({
            'name': self.name,
            'pdf_attachment_id': attachment.id,
            'company_id': self.env.company.id,
        })
        # Override auto-create if set on wizard
        if self.auto_create_bill:
            doc.company_id.sudo().write({'si_ocr_auto_create_bill': True})
        doc.action_run_ocr()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_si.ocr.document',
            'res_id': doc.id,
            'view_mode': 'form',
            'target': 'current',
        }
