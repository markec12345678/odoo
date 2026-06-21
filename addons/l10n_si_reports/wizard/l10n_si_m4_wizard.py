# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from xml.etree import ElementTree as ET

from odoo import _, fields, models


class L10nSiM4Wizard(models.TransientModel):
    """Generate M4 (Obračun akontacije dohodnine) monthly report.

    Lists all employee salary prepayments for the month. Submitted to FURS by
    15th of the following month.

    NOTE: This requires either `l10n_si_hr_payroll` (Enterprise) or custom
    payroll data. The wizard searches for `hr.payslip` lines with the SI
    structure and aggregates them per employee.
    """
    _name = 'l10n_si.m4.wizard'
    _description = 'M4 Monthly Income Tax Prepayment Generator'
    _inherit = 'l10n_si.report.wizard.mixin'

    report_type = fields.Selection(
        selection=[('ajpes_srs', 'AJPES SRS'),
                   ('rek1', 'REK-1'),
                   ('m4', 'M4')],
        default='m4',
        required=True,
    )

    def action_generate(self):
        self.ensure_one()
        company = self.company_id

        date_from = fields.Date.to_date(f'{self.year}-{self.month:02d}-01')
        if self.month == 12:
            date_to = fields.Date.to_date(f'{self.year}-12-31')
        else:
            date_to = fields.Date.to_date(f'{self.year}-{self.month + 1:02d}-01')
            date_to = fields.Date.subtract(date_to, days=1)

        # Try to find payslips (works if hr_payroll is installed)
        payslip_model = self.env.get('hr.payslip')
        payslips = payslip_model.search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'done'),
        ]) if payslip_model else self.env['hr.payslip']

        root = ET.Element('M4', attrib={
            'version': '2.1',
            'xmlns': 'http://edavki.fu.gov.si/m4/v2.1',
        })
        header = ET.SubElement(root, 'Header')
        ET.SubElement(header, 'TaxNumber').text = (company.vat or '').upper().lstrip('SI')
        ET.SubElement(header, 'CompanyName').text = company.name
        ET.SubElement(header, 'Period').text = f'{self.year}-{self.month:02d}'
        ET.SubElement(header, 'GeneratedAt').text = fields.Datetime.now().isoformat()

        body = ET.SubElement(root, 'Body')
        for slip in payslips:
            employee = slip.employee_id
            entry = ET.SubElement(body, 'Entry')
            ET.SubElement(entry, 'EmployeeTaxNumber').text = employee.address_home_id.vat or ''
            ET.SubElement(entry, 'EmployeeName').text = employee.name
            ET.SubElement(entry, 'GrossAmount').text = f'{slip.net_wage or 0.0:.2f}'
            ET.SubElement(entry, 'TaxPrepayment').text = f'{slip.sum_withholdings or 0.0:.2f}'

        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)

        attachment = self.env['ir.attachment'].create({
            'name': f'm4_{company.vat}_{self.year}-{self.month:02d}.xml',
            'type': 'binary',
            'datas': base64.b64encode(xml_bytes),
            'mimetype': 'application/xml',
        })

        log = self.env['l10n_si.report.log'].create({
            'report_type': 'm4',
            'company_id': company.id,
            'date_from': date_from,
            'date_to': date_to,
            'xml_attachment_id': attachment.id,
            'state': 'generated',
            'notes': f'{len(payslips)} employees for {self.year}-{self.month:02d}',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_si.report.log',
            'res_id': log.id,
            'view_mode': 'form',
            'target': 'current',
        }
