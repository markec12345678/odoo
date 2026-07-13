# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from xml.etree import ElementTree as ET

from odoo import fields, models


class L10nSiAjpesSrsWizard(models.TransientModel):
    """Generate AJPES SRS (Standardni računovodski izkaz) annual report.

    Produces an XML file in the AJPES SRS v3.0 format.
    """
    _name = 'l10n_si.ajpes.srs.wizard'
    _description = 'AJPES SRS Annual Report Generator'
    _inherit = 'l10n_si.report.wizard.mixin'

    report_type = fields.Selection(
        selection=[('ajpes_srs', 'AJPES SRS'),
                   ('rek1', 'REK-1'),
                   ('m4', 'M4')],
        default='ajpes_srs',
        required=True,
    )

    def action_generate(self):
        self.ensure_one()
        company = self.company_id

        # Compute balances for the year
        date_from = fields.Date.to_date(f'{self.year}-01-01')
        date_to = fields.Date.to_date(f'{self.year}-12-31')

        # Read trial balance from account.move.line
        lines = self.env['account.move.line'].search([
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
        ])

        balances = {}
        for line in lines:
            code = line.account_id.code
            if code not in balances:
                balances[code] = {'debit': 0.0, 'credit': 0.0}
            balances[code]['debit'] += line.debit
            balances[code]['credit'] += line.credit

        # Build XML
        root = ET.Element('AJPES_SRS', attrib={
            'version': '3.0',
            'xmlns': 'http://www.ajpes.si/srs/v3',
        })
        header = ET.SubElement(root, 'Header')
        ET.SubElement(header, 'TaxNumber').text = (company.vat or '').upper().lstrip('SI')
        ET.SubElement(header, 'CompanyName').text = company.name
        ET.SubElement(header, 'Year').text = str(self.year)
        ET.SubElement(header, 'GeneratedAt').text = fields.Datetime.now().isoformat()

        body = ET.SubElement(root, 'Body')
        balance_sheet = ET.SubElement(body, 'BalanceSheet')
        for code in sorted(balances):
            if code and code[0] in '01':  # 0xx and 1xx accounts = balance sheet
                bal = balances[code]
                account_elem = ET.SubElement(balance_sheet, 'Account')
                ET.SubElement(account_elem, 'Code').text = code
                ET.SubElement(account_elem, 'Debit').text = f'{bal["debit"]:.2f}'
                ET.SubElement(account_elem, 'Credit').text = f'{bal["credit"]:.2f}'

        income_statement = ET.SubElement(body, 'IncomeStatement')
        for code in sorted(balances):
            if code and code[0] in '4567':  # 4xx-7xx = income statement
                bal = balances[code]
                account_elem = ET.SubElement(income_statement, 'Account')
                ET.SubElement(account_elem, 'Code').text = code
                ET.SubElement(account_elem, 'Debit').text = f'{bal["debit"]:.2f}'
                ET.SubElement(account_elem, 'Credit').text = f'{bal["credit"]:.2f}'

        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)

        attachment = self.env['ir.attachment'].create({
            'name': f'ajpes_srs_{company.vat}_{self.year}.xml',
            'type': 'binary',
            'datas': base64.b64encode(xml_bytes),
            'mimetype': 'application/xml',
        })

        log = self.env['l10n_si.report.log'].create({
            'report_type': 'ajpes_srs',
            'company_id': company.id,
            'date_from': date_from,
            'date_to': date_to,
            'xml_attachment_id': attachment.id,
            'state': 'generated',
            'notes': f'Auto-generated for year {self.year}',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_si.report.log',
            'res_id': log.id,
            'view_mode': 'form',
            'target': 'current',
        }
