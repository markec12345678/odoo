# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from xml.etree import ElementTree as ET

from odoo import fields, models


class L10nSiRek1Wizard(models.TransientModel):
    """Generate REK-1 (Registracija kupcev) monthly report.

    Lists all B2B sales with VAT to Slovenian VAT-registered buyers.
    Submitted to FURS by 5th of the following month.
    """
    _name = 'l10n_si.rek1.wizard'
    _description = 'REK-1 Monthly Report Generator'
    _inherit = 'l10n_si.report.wizard.mixin'

    report_type = fields.Selection(
        selection=[('ajpes_srs', 'AJPES SRS'),
                   ('rek1', 'REK-1'),
                   ('m4', 'M4')],
        default='rek1',
        required=True,
    )

    def action_generate(self):
        self.ensure_one()
        company = self.company_id

        date_from = fields.Date.to_date(f'{self.year}-{self.month:02d}-01')
        # End of month
        if self.month == 12:
            date_to = fields.Date.to_date(f'{self.year}-12-31')
        else:
            date_to = fields.Date.to_date(f'{self.year}-{self.month + 1:02d}-01')
            date_to = fields.Date.subtract(date_to, days=1)

        # Find all posted customer invoices to SI partners with VAT
        moves = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
            ('partner_id.vat', 'like', 'SI%'),
        ])

        root = ET.Element('REK1', attrib={
            'version': '1.3',
            'xmlns': 'http://edavki.fu.gov.si/rek1/v1.3',
        })
        header = ET.SubElement(root, 'Header')
        ET.SubElement(header, 'TaxNumber').text = (company.vat or '').upper().lstrip('SI')
        ET.SubElement(header, 'Period').text = f'{self.year}-{self.month:02d}'
        ET.SubElement(header, 'GeneratedAt').text = fields.Datetime.now().isoformat()

        body = ET.SubElement(root, 'Body')
        for move in moves:
            partner_vat = (move.partner_id.vat or '').upper().lstrip('SI')
            if not partner_vat or len(partner_vat) != 8:
                continue  # skip invalid VATs

            entry = ET.SubElement(body, 'Entry')
            ET.SubElement(entry, 'BuyerTaxNumber').text = partner_vat
            ET.SubElement(entry, 'BuyerName').text = move.partner_id.name
            ET.SubElement(entry, 'InvoiceNumber').text = move.name
            ET.SubElement(entry, 'InvoiceDate').text = move.invoice_date.isoformat() if move.invoice_date else ''
            ET.SubElement(entry, 'TaxableAmount').text = f'{move.amount_untaxed:.2f}'
            ET.SubElement(entry, 'VatAmount').text = f'{move.amount_tax:.2f}'
            ET.SubElement(entry, 'InvoiceAmount').text = f'{move.amount_total:.2f}'

        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)

        attachment = self.env['ir.attachment'].create({
            'name': f'rek1_{company.vat}_{self.year}-{self.month:02d}.xml',
            'type': 'binary',
            'datas': base64.b64encode(xml_bytes),
            'mimetype': 'application/xml',
        })

        log = self.env['l10n_si.report.log'].create({
            'report_type': 'rek1',
            'company_id': company.id,
            'date_from': date_from,
            'date_to': date_to,
            'xml_attachment_id': attachment.id,
            'state': 'generated',
            'notes': f'{len(moves)} entries for {self.year}-{self.month:02d}',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_si.report.log',
            'res_id': log.id,
            'view_mode': 'form',
            'target': 'current',
        }
