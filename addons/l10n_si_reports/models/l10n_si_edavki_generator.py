# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
"""eDavki XML generators for REK-1 and M4 reports.

This module contains three Odoo models:

* :class:`L10nSiEdavkiGenerator` — abstract base with the common
  ``generate(company_id, date_from, date_to)`` API used by all generators.
* :class:`L10nSiRek1Generator` — builds the REK-1 XML (monthly B2B sales
  VAT report) per ``http://edavki.durs.si/Documents/Schemas/REK1_3.xsd``.
* :class:`L10nSiM4Generator` — builds the M4 XML (monthly income tax
  prepayment) per ``http://edavki.durs.si/Documents/Schemas/M4_2.xsd``.

The :class:`L10nSiReportLog` model is extended with quick-action methods
that dispatch to the appropriate generator and store the resulting XML as
an ``ir.attachment``.
"""
import base64
import logging
from xml.etree import ElementTree as ET

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# XML namespaces used by the eDavki schemas (FURS / DURS).
REK1_NS = 'http://edavki.durs.si/Documents/Schemas/REK1_3.xsd'
M4_NS = 'http://edavki.durs.si/Documents/Schemas/M4_2.xsd'


def _si_tax_number(vat):
    """Return the 8-digit Slovenian tax number from a VAT string.

    e.g. ``'SI12345671'`` -> ``'12345671'``; ``'12345671'`` -> ``'12345671'``.
    Returns the empty string for missing input.
    """
    if not vat:
        return ''
    vat = vat.strip().upper()
    if vat.startswith('SI'):
        vat = vat[2:]
    return vat


class L10nSiEdavkiGenerator(models.AbstractModel):
    """Abstract base for all eDavki XML generators.

    Concrete generators must override :meth:`generate` to return the XML
    as ``bytes`` and may override :meth:`_report_type` to identify which
    ``l10n_si.report.log`` report_type the generator belongs to.
    """
    _name = 'l10n_si.edavki.generator'
    _description = 'Slovenian eDavki XML Generator (abstract)'

    def _report_type(self):
        """Return the matching ``l10n_si.report.log`` report_type."""
        raise NotImplementedError

    def generate(self, company_id, date_from, date_to):
        """Build the XML body for the given period.

        :param res.company company_id: company the report is generated for
        :param date date_from: inclusive start date
        :param date date_to: inclusive end date
        :return: ``bytes`` containing the UTF-8 encoded XML document
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helpers shared by all concrete generators
    # ------------------------------------------------------------------
    def _format_date(self, value):
        """Format a date/datetime as ``YYYY-MM-DD`` (safe for None)."""
        if not value:
            return ''
        if isinstance(value, str):
            return value[:10]
        return fields.Date.to_string(value) if hasattr(value, 'year') else str(value)[:10]

    def _format_amount(self, value):
        """Format a number with two decimals using a dot as separator."""
        return f'{float(value or 0.0):.2f}'

    def _format_period(self, date_from, date_to):
        """Return ``YYYY-MM`` derived from the period start date."""
        return self._format_date(date_from)[:7]


class L10nSiRek1Generator(models.AbstractModel):
    """REK-1 generator — monthly B2B sales VAT report (ZDDV-1, 81. člen).

    Searches posted customer invoices in the period where the partner has a
    valid Slovenian VAT number and emits one ``<Postavka>`` per invoice.
    """
    _name = 'l10n_si.edavki.rek1.generator'
    _description = 'Slovenian eDavki REK-1 XML Generator'
    _inherit = 'l10n_si.edavki.generator'

    def _report_type(self):
        return 'rek1'

    def generate(self, company_id, date_from, date_to):
        self.ensure_one()
        company = company_id

        # Posted customer invoices in the period for SI VAT-registered partners.
        moves = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('company_id', '=', company.id),
            ('partner_id.vat', 'like', 'SI%'),
        ])

        root = ET.Element('REK1', attrib={'xmlns': REK1_NS})

        # --- Napaka (error indicator, 'false' means report is valid) -------
        ET.SubElement(root, 'Napaka').text = 'false'

        # --- Racun (header) ------------------------------------------------
        racun = ET.SubElement(root, 'Racun')
        ET.SubElement(racun, 'Period').text = self._format_period(date_from, date_to)
        ET.SubElement(racun, 'DavcnaStevilka').text = _si_tax_number(company.vat)
        ET.SubElement(racun, 'DatumNastanka').text = self._format_date(fields.Date.today())

        total_base = 0.0
        total_vat = 0.0
        total_total = 0.0

        # --- Postavka per invoice -----------------------------------------
        for move in moves:
            buyer_vat = _si_tax_number(move.partner_id.vat)
            if not buyer_vat or len(buyer_vat) != 8:
                # Skip partners with invalid SI VAT (REK-1 is SI-only).
                continue

            partner = move.partner_id
            address_parts = [p for p in [partner.street, partner.zip, partner.city] if p]
            address = ', '.join(address_parts)

            postavka = ET.SubElement(racun, 'Postavka')
            ET.SubElement(postavka, 'DavcnaStevilkaKupca').text = buyer_vat
            ET.SubElement(postavka, 'NazivKupca').text = partner.name or ''
            ET.SubElement(postavka, 'NaslovKupca').text = address
            ET.SubElement(postavka, 'StevilkaRacunaKupca').text = move.name or ''
            ET.SubElement(postavka, 'DatumRacuna').text = self._format_date(move.invoice_date or move.date)

            base = float(move.amount_untaxed or 0.0)
            vat = float(move.amount_tax or 0.0)
            total = float(move.amount_total or 0.0)
            ET.SubElement(postavka, 'Osnova').text = self._format_amount(base)
            ET.SubElement(postavka, 'DDV').text = self._format_amount(vat)
            ET.SubElement(postavka, 'VrednostRacuna').text = self._format_amount(total)

            total_base += base
            total_vat += vat
            total_total += total

        # --- Skupaj totals -------------------------------------------------
        skupaj = ET.SubElement(racun, 'Skupaj')
        ET.SubElement(skupaj, 'Osnova').text = self._format_amount(total_base)
        ET.SubElement(skupaj, 'DDV').text = self._format_amount(total_vat)
        ET.SubElement(skupaj, 'VrednostRacuna').text = self._format_amount(total_total)

        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        return xml_bytes


class L10nSiM4Generator(models.AbstractModel):
    """M4 generator — monthly income tax prepayment (ZDoh-2, 28. člen).

    Searches ``hr.payslip`` if the model is available (graceful fallback to
    an empty body if HR Payroll is not installed).
    """
    _name = 'l10n_si.edavki.m4.generator'
    _description = 'Slovenian eDavki M4 XML Generator'
    _inherit = 'l10n_si.edavki.generator'

    def _report_type(self):
        return 'm4'

    def _get_payslips(self, company, date_from, date_to):
        """Return payslips for the period (or empty recordset if HR missing)."""
        Payslip = self.env.get('hr.payslip')
        if Payslip is None:
            _logger.info('M4: hr.payslip model not available, generating empty body.')
            return self.env['hr.payslip'] if 'hr.payslip' in self.env else Payslip
        return Payslip.search([
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('company_id', '=', company.id),
            ('state', '=', 'done'),
        ])

    def generate(self, company_id, date_from, date_to):
        self.ensure_one()
        company = company_id

        payslips = self._get_payslips(company, date_from, date_to)

        root = ET.Element('M4', attrib={'xmlns': M4_NS})

        # --- Obdobje + DavcnaStevilka (header) -----------------------------
        ET.SubElement(root, 'Obdobje').text = self._format_period(date_from, date_to)
        ET.SubElement(root, 'DavcnaStevilka').text = _si_tax_number(company.vat)

        total_gross = 0.0
        total_tax = 0.0

        # --- Postavka per employee -----------------------------------------
        for slip in payslips:
            employee = slip.employee_id
            # Address home partner is required for the employee's SI VAT.
            partner = getattr(employee, 'address_home_id', None)
            employee_vat = _si_tax_number(partner.vat) if partner else ''

            postavka = ET.SubElement(root, 'Postavka')
            ET.SubElement(postavka, 'DavcnaStevilka').text = employee_vat
            ET.SubElement(postavka, 'PriimekInIme').text = employee.name or ''

            gross = float(getattr(slip, 'net_wage', 0.0) or 0.0)
            tax = float(getattr(slip, 'sum_withholdings', 0.0) or 0.0)
            ET.SubElement(postavka, 'BrutoZnesek').text = self._format_amount(gross)
            ET.SubElement(postavka, 'AkontacijaDohodnine').text = self._format_amount(tax)

            total_gross += gross
            total_tax += tax

        # --- Skupaj totals -------------------------------------------------
        skupaj = ET.SubElement(root, 'Skupaj')
        ET.SubElement(skupaj, 'BrutoZnesek').text = self._format_amount(total_gross)
        ET.SubElement(skupaj, 'AkontacijaDohodnine').text = self._format_amount(total_tax)

        xml_bytes = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        return xml_bytes


class L10nSiReportLog(models.Model):
    """Extend the SI report log with quick-generate actions."""
    _inherit = 'l10n_si.report.log'

    # ------------------------------------------------------------------
    # Dispatch helpers
    # ------------------------------------------------------------------
    def _get_generator(self):
        """Return the generator instance matching ``report_type``."""
        self.ensure_one()
        mapping = {
            'rek1': 'l10n_si.edavki.rek1.generator',
            'm4': 'l10n_si.edavki.m4.generator',
        }
        generator_name = mapping.get(self.report_type)
        if not generator_name:
            raise UserError(_(
                'No eDavki generator available for report type "%s".',
            ) % self.report_type)
        return self.env[generator_name]

    def _generate_and_attach(self):
        """Generate XML via the appropriate generator, save as ir.attachment.

        Returns ``self`` (the log record) for chaining.
        """
        self.ensure_one()
        generator = self._get_generator()
        xml_bytes = generator.generate(self.company_id, self.date_from, self.date_to)

        # Increment version when re-generating.
        existing = self.xml_attachment_id
        new_version = (self.version or 1) + (1 if existing else 0)

        filename = f'{self.report_type}_{self.company_id.vat or "novat"}_' \
                   f'{fields.Date.to_string(self.date_from)}.xml'

        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(xml_bytes),
            'mimetype': 'application/xml',
            'res_model': 'l10n_si.report.log',
            'res_id': self.id,
        })
        self.write({
            'xml_attachment_id': attachment.id,
            'version': new_version,
            'state': 'generated',
            'notes': (_(f'Re-generated v{new_version} on {fields.Datetime.now()}.\n')
                      if existing else ''),
        })
        return self

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------
    def action_generate_xml(self):
        """Dispatch to the correct generator and save as ir.attachment."""
        for log in self:
            log._generate_and_attach()
        return True

    def action_generate_rek1_current_month(self):
        """Quick action: build REK-1 for the current month."""
        today = fields.Date.today()
        date_from = today.replace(day=1)
        # Last day of the current month:
        if today.month == 12:
            date_to = today.replace(day=31)
        else:
            date_to = today.replace(month=today.month + 1, day=1)
            date_to = fields.Date.subtract(date_to, days=1)

        log = self.env['l10n_si.report.log'].create({
            'report_type': 'rek1',
            'company_id': self.env.company.id,
            'date_from': date_from,
            'date_to': date_to,
        })
        log._generate_and_attach()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_si.report.log',
            'res_id': log.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_generate_m4_current_month(self):
        """Quick action: build M4 for the current month."""
        today = fields.Date.today()
        date_from = today.replace(day=1)
        if today.month == 12:
            date_to = today.replace(day=31)
        else:
            date_to = today.replace(month=today.month + 1, day=1)
            date_to = fields.Date.subtract(date_to, days=1)

        log = self.env['l10n_si.report.log'].create({
            'report_type': 'm4',
            'company_id': self.env.company.id,
            'date_from': date_from,
            'date_to': date_to,
        })
        log._generate_and_attach()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'l10n_si.report.log',
            'res_id': log.id,
            'view_mode': 'form',
            'target': 'current',
        }
