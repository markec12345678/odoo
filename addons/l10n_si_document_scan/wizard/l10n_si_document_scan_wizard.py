# -*- coding: utf-8 -*-
"""Wizard za hitro skeniranje dokumenta."""
from odoo import fields, models


class L10nSiDocumentScanWizard(models.TransientModel):
    _name = 'l10n_si.document.scan.wizard'
    _description = 'Document Scan Wizard'

    document_type = fields.Selection(
        selection=[('passport', 'Potni list'),
                   ('id_card', 'Osebna izkaznica'),
                   ('driver_license', 'Vozni list'),
                   ('other', 'Drugo')],
        default='id_card',
        required=True,
        string='Vrsta dokumenta',
    )
    document_image = fields.Binary(
        string='Slika dokumenta', required=True,
        help='Fotografirajte ali naložite sliko osebnega dokumenta',
    )

    def action_scan_and_create(self):
        """Ustvari document.scan zapis in zažene OCR."""
        self.ensure_one()
        scan = self.env['l10n_si.document.scan'].create({
            'document_type': self.document_type,
            'document_image': self.document_image,
        })
        # Avtomatsko zaženi OCR
        scan.action_run_ocr()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Scan',
            'res_model': 'l10n_si.document.scan',
            'res_id': scan.id,
            'view_mode': 'form',
            'target': 'current',
        }
