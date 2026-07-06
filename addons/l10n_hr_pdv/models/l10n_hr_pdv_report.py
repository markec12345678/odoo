# -*- coding: utf-8 -*-
"""Croatian PDV (VAT) report model — l10n_hr.pdv.report.

A PDV report aggregates posted account.move entries within a period
(monthly or quarterly) and produces:

* VAT breakdown by rate (25% / 13% / 5%) for both output (Izlazni PDV)
  and input (Ulazni PDV).
* Reverse-charge amount (Obrnuti porezni teret).
* EU intra-Community acquisitions (EUNabave) and supplies (EUIsporuke).
* VAT payable / refundable (PdvZaUplatu / PdvZaPovrat).
* ePorezna XML representation (<PdvObrazac>).

Deadlines (rokovi):
    - Monthly reporters:  20th of the next month.
    - Quarterly reporters: 20th after quarter end.
"""
import base64
import calendar
import logging
from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class L10nHrPdvReport(models.Model):
    _name = 'l10n_hr.pdv.report'
    _description = 'Croatian PDV Report (PDV obrazac / Knjiga PDV-a)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'year desc, period_number desc, company_id'

    # -----------------------------------------------------------------
    # Identification & period
    # -----------------------------------------------------------------
    name = fields.Char(
        string='Naziv', compute='_compute_name', store=True, index=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Tvrtka', required=True, index=True,
        default=lambda self: self.env.company, tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', store=True,
    )
    period_type = fields.Selection(
        selection=[('monthly', 'Mjesečno'),
                   ('quarterly', 'Kvartalno')],
        string='Tip razdoblja', required=True, default='monthly', tracking=True,
    )
    year = fields.Integer(
        string='Godina', required=True,
        default=lambda self: fields.Date.today().year, tracking=True,
    )
    period_number = fields.Integer(
        string='Broj razdoblja', required=True, default=1, tracking=True,
        help='Mjesec (1-12) ili kvartal (1-4).',
    )

    date_from = fields.Date(
        string='Datum od', compute='_compute_dates', store=True,
    )
    date_to = fields.Date(
        string='Datum do', compute='_compute_dates', store=True,
    )
    deadline = fields.Date(
        string='Rok predaje', compute='_compute_dates', store=True,
    )

    # -----------------------------------------------------------------
    # Output VAT (Izlazni PDV)
    # -----------------------------------------------------------------
    output_vat_25 = fields.Monetary(
        string='Izlazni PDV 25%', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    output_vat_13 = fields.Monetary(
        string='Izlazni PDV 13%', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    output_vat_5 = fields.Monetary(
        string='Izlazni PDV 5%', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    output_vat_total = fields.Monetary(
        string='Ukupni izlazni PDV', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )

    # -----------------------------------------------------------------
    # Input VAT (Ulazni PDV)
    # -----------------------------------------------------------------
    input_vat_25 = fields.Monetary(
        string='Ulazni PDV 25%', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    input_vat_13 = fields.Monetary(
        string='Ulazni PDV 13%', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    input_vat_5 = fields.Monetary(
        string='Ulazni PDV 5%', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    input_vat_total = fields.Monetary(
        string='Ukupni ulazni PDV', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )

    # -----------------------------------------------------------------
    # Bottom line
    # -----------------------------------------------------------------
    vat_payable = fields.Monetary(
        string='PDV za uplatu', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    vat_refundable = fields.Monetary(
        string='PDV za povrat', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )

    # -----------------------------------------------------------------
    # Special categories
    # -----------------------------------------------------------------
    reverse_charge_amount = fields.Monetary(
        string='Obrnuti porezni teret', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    eu_acquisitions = fields.Monetary(
        string='EU nabave (osnovica)', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )
    eu_supplies = fields.Monetary(
        string='EU isporuke (osnovica)', compute='_compute_amounts', store=True,
        currency_field='currency_id',
    )

    # -----------------------------------------------------------------
    # State & relations
    # -----------------------------------------------------------------
    state = fields.Selection(
        selection=[('draft', 'Nacrt'),
                   ('computed', 'Izračunato'),
                   ('submitted', 'Poslano'),
                   ('accepted', 'Prihvaćeno'),
                   ('rejected', 'Odbijeno')],
        string='Status', default='draft', required=True, tracking=True,
        copy=False,
    )
    line_ids = fields.One2many(
        'l10n_hr.pdv.report.line', 'report_id', string='Stavke Knjige PDV-a',
        copy=False,
    )
    move_count = fields.Integer(
        string='Broj dokumenata', compute='_compute_amounts', store=True,
    )
    eporezna_xml = fields.Text(
        string='ePorezna XML', copy=False, readonly=True,
    )
    eporezna_xml_generated_at = fields.Datetime(copy=False, readonly=True)
    submission_ref = fields.Char(
        string='Referenca prijave', copy=False, readonly=True,
    )

    _sql_constraints = [
        ('period_company_uniq',
         'unique(company_id, period_type, year, period_number)',
         'PDV izvještaj za isto razdoblje i tvrtku već postoji.'),
    ]

    # -----------------------------------------------------------------
    # Constraints & validations
    # -----------------------------------------------------------------
    @api.constrains('period_type', 'period_number')
    def _check_period_number(self):
        for report in self:
            if report.period_type == 'monthly' and not 1 <= report.period_number <= 12:
                raise ValidationError(_(
                    'Za mjesečno izvještavanje broj razdoblja mora biti 1-12 '
                    '(dano: %s).', report.period_number,
                ))
            if report.period_type == 'quarterly' and not 1 <= report.period_number <= 4:
                raise ValidationError(_(
                    'Za kvartalno izvještavanje broj razdoblja mora biti 1-4 '
                    '(dano: %s).', report.period_number,
                ))

    # -----------------------------------------------------------------
    # Computes
    # -----------------------------------------------------------------
    @api.depends('company_id', 'period_type', 'year', 'period_number')
    def _compute_name(self):
        month_hr = ['', 'siječanj', 'veljača', 'ožujak', 'travanj', 'svibanj',
                    'lipanj', 'srpanj', 'kolovoz', 'rujan', 'listopad',
                    'studeni', 'prosinac']
        for report in self:
            if not (report.year and report.period_number):
                report.name = '/'
                continue
            if report.period_type == 'monthly':
                m = report.period_number
                month_name = month_hr[m] if 1 <= m <= 12 else str(m)
                report.name = _('PDV %s %s — %s') % (
                    month_name, report.year, report.company_id.name or '',
                )
            else:
                report.name = _('PDV Q%s %s — %s') % (
                    report.period_number, report.year,
                    report.company_id.name or '',
                )

    @api.depends('period_type', 'year', 'period_number')
    def _compute_dates(self):
        for report in self:
            if not (report.year and report.period_number):
                report.date_from = False
                report.date_to = False
                report.deadline = False
                continue
            if report.period_type == 'monthly':
                m = report.period_number
                report.date_from = date(report.year, m, 1)
                last_day = calendar.monthrange(report.year, m)[1]
                report.date_to = date(report.year, m, last_day)
                # Deadline: 20th of next month
                if m == 12:
                    report.deadline = date(report.year + 1, 1, 20)
                else:
                    report.deadline = date(report.year, m + 1, 20)
            else:
                q = report.period_number
                start_month = (q - 1) * 3 + 1
                report.date_from = date(report.year, start_month, 1)
                end_month = start_month + 2
                last_day = calendar.monthrange(report.year, end_month)[1]
                report.date_to = date(report.year, end_month, last_day)
                # Deadline: 20th after quarter end
                if end_month == 12:
                    report.deadline = date(report.year + 1, 1, 20)
                else:
                    report.deadline = date(report.year, end_month + 1, 20)

    @api.depends('line_ids', 'line_ids.tax_25', 'line_ids.tax_13', 'line_ids.tax_5',
                 'line_ids.base_25', 'line_ids.base_13', 'line_ids.base_5',
                 'line_ids.base_exempt', 'line_ids.direction',
                 'line_ids.is_reverse_charge', 'line_ids.is_eu_acquisition',
                 'line_ids.is_eu_supply')
    def _compute_amounts(self):
        """Aggregate amounts from report lines.

        Output VAT (Izlazni PDV) comes from direction='output' lines.
        Input VAT (Ulazni PDV) comes from direction='input' lines.
        Reverse-charge, EU acquisitions, EU supplies come from the
        relevant base_exempt buckets on flagged lines.
        """
        for report in self:
            out25 = out13 = out5 = 0.0
            in25 = in13 = in5 = 0.0
            rc_amount = eu_acq = eu_sup = 0.0
            move_count = 0
            seen_moves = set()
            for line in report.line_ids:
                if line.direction == 'output':
                    out25 += line.tax_25
                    out13 += line.tax_13
                    out5 += line.tax_5
                else:
                    in25 += line.tax_25
                    in13 += line.tax_13
                    in5 += line.tax_5
                if line.is_reverse_charge:
                    rc_amount += line.base_25 + line.base_13 + line.base_5 + line.base_exempt
                if line.is_eu_acquisition:
                    eu_acq += line.base_25 + line.base_13 + line.base_5 + line.base_exempt
                if line.is_eu_supply:
                    eu_sup += line.base_25 + line.base_13 + line.base_5 + line.base_exempt
                if line.move_id.id not in seen_moves:
                    seen_moves.add(line.move_id.id)
                    move_count += 1
            output_total = out25 + out13 + out5
            input_total = in25 + in13 + in5
            balance = output_total - input_total
            if balance >= 0:
                payable = balance
                refundable = 0.0
            else:
                payable = 0.0
                refundable = -balance
            report.update({
                'output_vat_25': out25,
                'output_vat_13': out13,
                'output_vat_5': out5,
                'output_vat_total': output_total,
                'input_vat_25': in25,
                'input_vat_13': in13,
                'input_vat_5': in5,
                'input_vat_total': input_total,
                'vat_payable': payable,
                'vat_refundable': refundable,
                'reverse_charge_amount': rc_amount,
                'eu_acquisitions': eu_acq,
                'eu_supplies': eu_sup,
                'move_count': move_count,
            })

    # -----------------------------------------------------------------
    # Period helpers
    # -----------------------------------------------------------------
    @api.model
    def _get_period_for_date(self, ref_date, period_type='monthly'):
        """Return (year, period_number) for a date and period type."""
        if not ref_date:
            ref_date = fields.Date.today()
        if period_type == 'monthly':
            return ref_date.year, ref_date.month
        # Quarterly: 1=Jan-Mar, 2=Apr-Jun, 3=Jul-Sep, 4=Oct-Dec
        return ref_date.year, (ref_date.month - 1) // 3 + 1

    @api.model
    def _get_previous_period(self, period_type='monthly', ref_date=None):
        """Return the (year, period_number) immediately preceding ref_date."""
        if ref_date is None:
            ref_date = fields.Date.today()
        # Use the first day of the current period, subtract 1 day to land
        # in the previous period, then bucket.
        if period_type == 'monthly':
            first_of_month = date(ref_date.year, ref_date.month, 1)
            prev = first_of_month - timedelta(days=1)
            return prev.year, prev.month
        q = (ref_date.month - 1) // 3 + 1
        first_of_q = date(ref_date.year, (q - 1) * 3 + 1, 1)
        prev = first_of_q - timedelta(days=1)
        return prev.year, (prev.month - 1) // 3 + 1

    # -----------------------------------------------------------------
    # Tax/move helpers
    # -----------------------------------------------------------------
    def _get_period_moves_domain(self):
        """Return the domain used to fetch account.move within the period."""
        self.ensure_one()
        return [
            ('company_id', '=', self.company_id.id),
            ('state', '=', 'posted'),
            ('move_type', 'in',
             ('out_invoice', 'out_refund', 'out_receipt',
              'in_invoice', 'in_refund', 'in_receipt')),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
        ]

    @api.model
    def _is_output_move(self, move_type):
        return move_type in ('out_invoice', 'out_refund', 'out_receipt')

    @api.model
    def _is_input_move(self, move_type):
        return move_type in ('in_invoice', 'in_refund', 'in_receipt')

    @api.model
    def _is_refund_move(self, move_type):
        return move_type in ('out_refund', 'in_refund')

    def _get_move_vat_breakdown(self, move):
        """Compute the VAT breakdown for a single account.move.

        Returns a dict keyed by rate-bucket ('25', '13', '5', 'exempt'):
            { '25': {'base': float, 'tax': float},
              '13': {...}, '5': {...}, 'exempt': {'base': float, 'tax': 0.0} }

        Refunds (out_refund / in_refund) flip the sign of their base/tax
        so they correctly net against invoices in the report.
        """
        Line = self.env['l10n_hr.pdv.report.line']
        breakdown = {
            '25': {'base': 0.0, 'tax': 0.0},
            '13': {'base': 0.0, 'tax': 0.0},
            '5': {'base': 0.0, 'tax': 0.0},
            'exempt': {'base': 0.0, 'tax': 0.0},
        }
        sign = -1.0 if self._is_refund_move(move.move_type) else 1.0

        for aml in move.invoice_line_ids:
            base = aml.price_subtotal * sign
            taxes = aml.tax_ids
            if not taxes:
                breakdown['exempt']['base'] += base
                continue
            # If any tax on the line is a real VAT tax, accumulate
            # per rate bucket; lines with no VAT taxes go to exempt.
            applied_vat = False
            for tax in taxes:
                # Detect VAT taxes: percentage / division with non-zero amount
                if tax.amount_type not in ('percent', 'division'):
                    continue
                if not tax.amount:
                    continue
                bucket = Line._rate_bucket(tax.amount)
                if bucket is None:
                    # Non-standard rate — bucket as exempt for now
                    continue
                applied_vat = True
                # Compute tax amount for this rate
                if tax.amount_type == 'percent':
                    tax_amount = base * (float(tax.amount) / 100.0)
                else:  # division (price-included)
                    if float(tax.amount) == 100.0:
                        tax_amount = 0.0
                    else:
                        tax_amount = base - base / (1.0 + float(tax.amount) / 100.0)
                breakdown[bucket]['base'] += base
                breakdown[bucket]['tax'] += tax_amount
            if not applied_vat:
                breakdown['exempt']['base'] += base
        return breakdown

    @api.model
    def _detect_move_flags(self, move):
        """Detect reverse-charge / EU acquisition / EU supply for a move."""
        Line = self.env['l10n_hr.pdv.report.line']
        partner = move.partner_id
        info = Line._classify_partner(partner)
        flags = {
            'is_reverse_charge': False,
            'is_eu_acquisition': False,
            'is_eu_supply': False,
        }
        # EU acquisition: domestic company buys from EU partner (in_invoice)
        if (self._is_input_move(move.move_type)
                and info['is_eu']
                and not info['is_hr']):
            flags['is_eu_acquisition'] = True
        # EU supply: domestic company sells to EU partner (out_invoice)
        if (self._is_output_move(move.move_type)
                and info['is_eu']
                and not info['is_hr']):
            flags['is_eu_supply'] = True
        # Reverse charge: partner is domestic (HR) and move has reverse
        # charge tax. We detect this by checking if any tax has a
        # 'reverse charge' hint in its name ( Croatian: 'obrnuti' / 'reverse'),
        # or by absence of VAT tax on what should be a VAT-able transaction.
        tax_names = []
        for aml in move.invoice_line_ids:
            for tax in aml.tax_ids:
                if tax.name:
                    tax_names.append(tax.name.lower())
        if any(('obrnuti' in n) or ('reverse' in n) for n in tax_names):
            flags['is_reverse_charge'] = True
        return flags

    # -----------------------------------------------------------------
    # Actions
    # -----------------------------------------------------------------
    def action_compute(self):
        """Recompute the report: regenerate per-invoice line items
        and aggregate amounts.
        """
        Line = self.env['l10n_hr.pdv.report.line']
        for report in self:
            if not (report.date_from and report.date_to):
                raise UserError(_(
                    'Razdoblje nije ispravno postavljeno za izvještaj %s.',
                    report.name,
                ))
            # Remove existing lines
            old_lines = report.line_ids
            report.line_ids = [(5, 0, 0)]
            old_lines.unlink()

            moves = self.env['account.move'].search(
                report._get_period_moves_domain(),
                order='date, name',
            )
            new_lines_vals = []
            for move in moves:
                direction = 'output' if self._is_output_move(move.move_type) else 'input'
                breakdown = report._get_move_vat_breakdown(move)
                flags = report._detect_move_flags(move)
                partner_info = Line._classify_partner(move.partner_id)
                new_lines_vals.append({
                    'report_id': report.id,
                    'move_id': move.id,
                    'date': move.date,
                    'direction': direction,
                    'base_25': breakdown['25']['base'],
                    'tax_25': breakdown['25']['tax'],
                    'base_13': breakdown['13']['base'],
                    'tax_13': breakdown['13']['tax'],
                    'base_5': breakdown['5']['base'],
                    'tax_5': breakdown['5']['tax'],
                    'base_exempt': breakdown['exempt']['base'],
                    'partner_vat': move.partner_id.vat or '',
                    'partner_country_code': partner_info['country_code'],
                    'is_reverse_charge': flags['is_reverse_charge'],
                    'is_eu_acquisition': flags['is_eu_acquisition'],
                    'is_eu_supply': flags['is_eu_supply'],
                })
            if new_lines_vals:
                Line.create(new_lines_vals)
            report.state = 'computed'
            _logger.info(
                'PDV report %s computed: %d moves, %d lines',
                report.name, len(moves), len(new_lines_vals),
            )
        return True

    def action_generate_xml(self):
        """Generate ePorezna <PdvObrazac> XML for each report."""
        for report in self:
            if report.state == 'draft':
                raise UserError(_(
                    'Izvještaj %s je u statusu "Nacrt". Kliknite "Izračunaj" '
                    'prije generiranja XML-a.', report.name,
                ))
            xml = report._build_eporezna_xml()
            report.write({
                'eporezna_xml': xml,
                'eporezna_xml_generated_at': fields.Datetime.now(),
                'state': 'submitted' if report.state == 'computed' else report.state,
            })
            _logger.info('ePorezna XML generated for report %s', report.name)
        return True

    def _build_eporezna_xml(self):
        """Build the ePorezna <PdvObrazac> XML as a string.

        The XML structure mirrors the Porezna uprava specification:

        <PdvObrazac xmlns="urn:eporezna.porezna-uprava.hr">
            <Razdoblje>
                <Tip>mjesec|kvartal</Tip>
                <Godina>2024</Godina>
                <Broj>1</Broj>
                <DatumOd>2024-01-01</DatumOd>
                <DatumDo>2024-01-31</DatumDo>
            </Razdoblje>
            <Obveznik>
                <OIB>12345678901</OIB>
                <Naziv>Company name</Naziv>
            </Obveznik>
            <IzlazniPdv>
                <Stopa25><Osnovica/><Porez/></Stopa25>
                <Stopa13><Osnovica/><Porez/></Stopa13>
                <Stopa5><Osnovica/><Porez/></Stopa5>
            </IzlazniPdv>
            <UlazniPdv>
                <Stopa25><Osnovica/><Porez/></Stopa25>
                <Stopa13><Osnovica/><Porez/></Stopa13>
                <Stopa5><Osnovica/><Porez/></Stopa5>
            </UlazniPdv>
            <ObrnutiPorezniTeret>...</ObrnutiPorezniTeret>
            <EUNabave>...</EUNabave>
            <EUIsporuke>...</EUIsporuke>
            <PdvZaUplatu>...</PdvZaUplatu>
            <PdvZaPovrat>...</PdvZaPovrat>
        </PdvObrazac>
        """
        self.ensure_one()
        company = self.company_id
        oib = (company.vat or '').strip()
        if oib and oib.startswith('HR'):
            oib = oib[2:]
        # Compute base amounts per rate (tax comes from already-computed fields)
        out_base_25 = out_base_13 = out_base_5 = 0.0
        in_base_25 = in_base_13 = in_base_5 = 0.0
        for line in self.line_ids:
            if line.direction == 'output':
                out_base_25 += line.base_25
                out_base_13 += line.base_13
                out_base_5 += line.base_5
            else:
                in_base_25 += line.base_25
                in_base_13 += line.base_13
                in_base_5 += line.base_5

        def _f(value):
            return f'{value or 0.0:.2f}'

        tip = 'mjesec' if self.period_type == 'monthly' else 'kvartal'
        date_from = self.date_from.strftime('%Y-%m-%d') if self.date_from else ''
        date_to = self.date_to.strftime('%Y-%m-%d') if self.date_to else ''

        # Use simple string formatting to avoid external dependencies
        # on lxml / xml.etree namespaces; the resulting XML is well-formed.
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<PdvObrazac xmlns="urn:eporezna.porezna-uprava.hr">',
            '  <Razdoblje>',
            f'    <Tip>{tip}</Tip>',
            f'    <Godina>{self.year}</Godina>',
            f'    <Broj>{self.period_number}</Broj>',
            f'    <DatumOd>{date_from}</DatumOd>',
            f'    <DatumDo>{date_to}</DatumDo>',
            '  </Razdoblje>',
            '  <Obveznik>',
            f'    <OIB>{_escape_xml(oib)}</OIB>',
            f'    <Naziv>{_escape_xml(company.name or "")}</Naziv>',
            '  </Obveznik>',
            '  <IzlazniPdv>',
            '    <Stopa25>',
            f'      <Osnovica>{_f(out_base_25)}</Osnovica>',
            f'      <Porez>{_f(self.output_vat_25)}</Porez>',
            '    </Stopa25>',
            '    <Stopa13>',
            f'      <Osnovica>{_f(out_base_13)}</Osnovica>',
            f'      <Porez>{_f(self.output_vat_13)}</Porez>',
            '    </Stopa13>',
            '    <Stopa5>',
            f'      <Osnovica>{_f(out_base_5)}</Osnovica>',
            f'      <Porez>{_f(self.output_vat_5)}</Porez>',
            '    </Stopa5>',
            '  </IzlazniPdv>',
            '  <UlazniPdv>',
            '    <Stopa25>',
            f'      <Osnovica>{_f(in_base_25)}</Osnovica>',
            f'      <Porez>{_f(self.input_vat_25)}</Porez>',
            '    </Stopa25>',
            '    <Stopa13>',
            f'      <Osnovica>{_f(in_base_13)}</Osnovica>',
            f'      <Porez>{_f(self.input_vat_13)}</Porez>',
            '    </Stopa13>',
            '    <Stopa5>',
            f'      <Osnovica>{_f(in_base_5)}</Osnovica>',
            f'      <Porez>{_f(self.input_vat_5)}</Porez>',
            '    </Stopa5>',
            '  </UlazniPdv>',
            f'  <ObrnutiPorezniTeret>{_f(self.reverse_charge_amount)}</ObrnutiPorezniTeret>',
            f'  <EUNabave>{_f(self.eu_acquisitions)}</EUNabave>',
            f'  <EUIsporuke>{_f(self.eu_supplies)}</EUIsporuke>',
            f'  <PdvZaUplatu>{_f(self.vat_payable)}</PdvZaUplatu>',
            f'  <PdvZaPovrat>{_f(self.vat_refundable)}</PdvZaPovrat>',
            '</PdvObrazac>',
        ]
        return '\n'.join(xml_parts)

    def action_view_lines(self):
        """Open the Knjiga PDV-a line items view for this report."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Knjiga PDV-a — %s') % self.name,
            'res_model': 'l10n_hr.pdv.report.line',
            'view_mode': 'tree',
            'domain': [('report_id', '=', self.id)],
            'context': {'default_report_id': self.id},
        }

    def action_set_accepted(self):
        """Mark report as accepted by Porezna uprava."""
        for report in self:
            report.state = 'accepted'
        return True

    def action_set_rejected(self):
        """Mark report as rejected by Porezna uprava."""
        for report in self:
            report.state = 'rejected'
        return True

    def action_reset_to_draft(self):
        """Reset the report to draft state."""
        for report in self:
            report.state = 'draft'
        return True

    def action_download_xml(self):
        """Download the generated ePorezna XML as an attachment."""
        self.ensure_one()
        if not self.eporezna_xml:
            raise UserError(_('XML još nije generiran. Kliknite "Generiraj XML".'))
        filename = 'PDV_%s_%s_%s.xml' % (
            self.company_id.name or 'hr',
            self.year,
            self.period_number,
        )
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(self.eporezna_xml.encode('utf-8')),
            'res_model': 'l10n_hr.pdv.report',
            'res_id': self.id,
            'mimetype': 'application/xml',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % attachment.id,
            'target': 'self',
        }

    # -----------------------------------------------------------------
    # Cron
    # -----------------------------------------------------------------
    @api.model
    def _cron_generate_pdv_reports(self):
        """Auto-generate monthly PDV reports for the previous month
        for every HR company.
        """
        companies = self.env['res.company'].search([
            ('country_id.code', '=', 'HR'),
        ])
        today = fields.Date.today()
        prev_year, prev_month = self._get_previous_period('monthly', today)
        for company in companies:
            existing = self.search([
                ('company_id', '=', company.id),
                ('period_type', '=', 'monthly'),
                ('year', '=', prev_year),
                ('period_number', '=', prev_month),
            ], limit=1)
            if existing:
                _logger.info(
                    'PDV report already exists for %s %d-%d (company %s)',
                    'monthly', prev_year, prev_month, company.name,
                )
                continue
            try:
                report = self.create({
                    'company_id': company.id,
                    'period_type': 'monthly',
                    'year': prev_year,
                    'period_number': prev_month,
                })
                report.action_compute()
                _logger.info(
                    'Auto-generated monthly PDV report %s for %s',
                    report.name, company.name,
                )
            except Exception:
                _logger.exception(
                    'Failed to auto-generate PDV report for company %s '
                    '(%d-%d)', company.name, prev_year, prev_month,
                )


def _escape_xml(value):
    """Minimal XML entity escaping for safe inclusion in text content."""
    if value is None:
        return ''
    s = str(value)
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    return s


class AccountMove(models.Model):
    """Minor extension of account.move to surface PDV-relevant flags
    used by the Knjiga PDV-a and PDV obrazac.

    These are computed on the fly from partner country and tax names
    (no extra DB columns needed).
    """
    _inherit = 'account.move'

    l10n_hr_pdv_is_reverse_charge = fields.Boolean(
        string='Obrnuti porezni teret',
        compute='_compute_l10n_hr_pdv_flags',
    )
    l10n_hr_pdv_is_eu_acquisition = fields.Boolean(
        string='EU nabava',
        compute='_compute_l10n_hr_pdv_flags',
    )
    l10n_hr_pdv_is_eu_supply = fields.Boolean(
        string='EU isporuka',
        compute='_compute_l10n_hr_pdv_flags',
    )

    @api.depends('partner_id', 'partner_id.country_id', 'invoice_line_ids.tax_ids',
                 'move_type')
    def _compute_l10n_hr_pdv_flags(self):
        Report = self.env['l10n_hr.pdv.report']
        for move in self:
            flags = Report._detect_move_flags(move)
            move.l10n_hr_pdv_is_reverse_charge = flags['is_reverse_charge']
            move.l10n_hr_pdv_is_eu_acquisition = flags['is_eu_acquisition']
            move.l10n_hr_pdv_is_eu_supply = flags['is_eu_supply']
