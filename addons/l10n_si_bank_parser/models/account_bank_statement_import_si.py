# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import re
from datetime import datetime
from decimal import Decimal
from xml.etree import ElementTree as ET

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# ISO 20022 namespaces
NS_CAMT = {
    'camt': 'urn:iso:std:iso:20022:tech:xsd:camt.053.001.02',
    'n1': 'urn:iso:std:iso:20022:tech:xsd:camt.053.001.02',
}

# Slovenian bank BIC codes for auto-detection
SI_BANK_BICS = {
    'LJBASI2X': 'NLB (Nova Ljubljanska banka)',
    'KBMRSI2X': 'NKBM (Nova Kreditna banka Maribor)',
    'HDELSI22': 'Sparkasse (Hranilnica Ljubljanska)',
    'HAABSI22': 'Addiko Bank',
    'GIBASI2X': 'Raiffeisen Bank',
    'A1BASI2X': 'A1 Banka',
    'KOPRSI2X': 'NKBM / Primorska banka',
}


class AccountBankStatementImportSi(models.TransientModel):
    """Custom wizard replacing the default Odoo bank statement import.

    Handles SI-specific quirks:
    * NLB prepends "PRILIV " (inbound) or "ODLIV " (outbound) to transaction names
    * NKBM concatenates partner name into a single field with no separators
    * Sparkase uses CSTP/NTRY structures differently from the standard
    """
    _name = 'l10n_si.bank.statement.import'
    _description = 'SI Bank Statement Import Wizard'

    def _parse_si_camt053(self, xml_bytes):
        """Parse an ISO 20022 CAMT.053 statement file.

        Returns a list of dicts in the Odoo statement import format:
            [{
                'name': 'NLB-2025-01-001',
                'date': '2025-01-15',
                'balance_start': 1000.00,
                'balance_end_real': 2500.00,
                'transactions': [{
                    'date': '2025-01-14',
                    'payment_ref': 'Plačilo po računu 2025-001',
                    'amount': 1500.00,
                    'partner_name': 'Janez Novak',
                    'account_number': 'SI56 1234 5678 9012 345',
                    'unique_import_id': 'NLB-2025-01-14-001',
                    'ref': '2025-001',
                }, ...],
            }, ...]
        """
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            raise UserError(_('Invalid XML: %s') % e) from e

        statements = []
        for stmt_elem in root.findall('.//camt:Stmt', NS_CAMT):
            stmt = self._parse_si_stmt_element(stmt_elem)
            if stmt:
                statements.append(stmt)
        return statements

    def _parse_si_stmt_element(self, stmt_elem):
        """Parse a single <Stmt> element."""
        stmt_id = stmt_elem.findtext('camt:Id', '', NS_CAMT)
        seq = stmt_elem.findtext('camt:ElctrncSeqNb', '', NS_CAMT)
        stmt_name = f'{stmt_id}-{seq}' if seq else stmt_id or 'statement'

        # Balance start / end
        bal_start = self._parse_si_balance(stmt_elem, 'OPBD')
        bal_end = self._parse_si_balance(stmt_elem, 'CLBD')

        # Transactions
        transactions = []
        for ntry in stmt_elem.findall('.//camt:Ntry', NS_CAMT):
            tx = self._parse_si_ntry_element(ntry)
            if tx:
                transactions.append(tx)

        return {
            'name': stmt_name,
            'date': bal_end['date'] if bal_end else fields.Date.today().isoformat(),
            'balance_start': bal_start['amount'] if bal_start else 0.0,
            'balance_end_real': bal_end['amount'] if bal_end else 0.0,
            'transactions': transactions,
        }

    def _parse_si_balance(self, stmt_elem, code):
        """Find a balance element by its CD (OPBD=opening, CLBD=closing)."""
        for bal in stmt_elem.findall('.//camt:Bal', NS_CAMT):
            cd = bal.findtext('camt:Tp/camt:CdOrPrtry/camt:Cd', '', NS_CAMT)
            if cd == code:
                amount = bal.findtext('camt:Amt', '0', NS_CAMT)
                date_str = bal.findtext('camt:Dt/camt:Dt', '', NS_CAMT)
                return {
                    'amount': float(Decimal(amount)),
                    'date': date_str,
                }
        return None

    def _parse_si_ntry_element(self, ntry):
        """Parse a single transaction <Ntry> element.

        Handles SI quirks:
        * NLB "PRILIV"/"ODLIV" prefix in addtl_inf
        * NKBM concatenated partner name in RltdPties/Nm
        * SKB double-space normalization
        """
        amount_str = ntry.findtext('camt:Amt', '0', NS_CAMT)
        cdt_dbt = ntry.findtext('camt:CdtDbtInd', 'DBIT', NS_CAMT)
        amount = float(Decimal(amount_str))
        if cdt_dbt == 'DBIT':
            amount = -amount

        # Date: prefer book date, fall back to value date
        date_str = (ntry.findtext('camt:BookgDt/camt:Dt', '', NS_CAMT)
                    or ntry.findtext('camt:ValDt/camt:Dt', '', NS_CAMT))

        # Payment reference
        ref = (ntry.findtext('camt:RmtInf/camt:Strd/camt:CdtrRefInf/camt:Ref', '', NS_CAMT)
               or ntry.findtext('camt:Refs/camt:EndToEndId', '', NS_CAMT))

        # Partner name + account
        partner_name = ''
        partner_account = ''
        if cdt_dbt == 'CRDT':
            # Incoming: partner is the debtor
            party = ntry.find('.//camt:RltdPties/camt:Dbtr', NS_CAMT)
        else:
            party = ntry.find('.//camt:RltdPties/camt:Cdtr', NS_CAMT)
        if party is not None:
            partner_name = party.findtext('camt:Nm', '', NS_CAMT)
            acct = party.find('camt:PstlAdr', NS_CAMT)  # some banks put address here
            partner_account_elem = ntry.find(
                './/camt:RltdPties/camt:DbtrAcct/camt:Id/camt:IBAN', NS_CAMT,
            ) or ntry.find(
                './/camt:RltdPties/camt:CdtrAcct/camt:Id/camt:IBAN', NS_CAMT,
            )
            if partner_account_elem is not None:
                partner_account = partner_account_elem.text or ''

        # Additional info (NLB uses this for "PRILIV"/"ODLIV" classification)
        addtl_inf = ntry.findtext('.//camt:AddtlNtryInf', '', NS_CAMT)
        payment_ref = addtl_inf or ref or partner_name or 'Bank transaction'

        # NLB quirk: remove "PRILIV " / "ODLIV " prefix
        if payment_ref.startswith(('PRILIV ', 'ODLIV ')):
            payment_ref = payment_ref[7:].strip()

        # SKB quirk: collapse double spaces
        payment_ref = re.sub(r'\s+', ' ', payment_ref)
        if partner_name:
            partner_name = re.sub(r'\s+', ' ', partner_name).strip()

        # Unique import ID
        acct_svcr_ref = ntry.findtext('camt:AcctSvcrRef', '', NS_CAMT) or ntry.findtext(
            'camt:Refs/camt:AcctSvcrRef', '', NS_CAMT,
        )
        unique_id = acct_svcr_ref or f'{date_str}-{amount}-{partner_name}'

        return {
            'date': date_str,
            'payment_ref': payment_ref[:500],
            'amount': amount,
            'partner_name': partner_name[:255] if partner_name else '',
            'account_number': partner_account.replace(' ', '') if partner_account else '',
            'unique_import_id': unique_id[:128],
            'ref': (ref or '')[:128],
        }

    def _parse_si_mt940(self, content):
        """Parse MT940 (STA) format used by Raiffeisen and other legacy systems.

        This is a simplified parser — full MT940 has dozens of field variants.
        """
        # MT940 is text-based, encode to bytes for consistent processing
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='replace')

        statements = []
        current_stmt = None
        current_txs = []

        for line in content.split('\n'):
            line = line.strip()
            if line.startswith(':20:'):  # Transaction reference
                if current_stmt:
                    current_stmt['transactions'] = current_txs
                    statements.append(current_stmt)
                current_stmt = {
                    'name': line[4:],
                    'transactions': [],
                    'balance_start': 0.0,
                    'balance_end_real': 0.0,
                }
                current_txs = []
            elif line.startswith(':25:'):  # Account number
                if current_stmt:
                    current_stmt['account_number'] = line[4:].strip()
            elif line.startswith(':60F:'):  # Opening balance
                # :60F:C250114EUR1000,00
                m = re.match(r'^:60F:([CD])(\d{6})([A-Z]{3})([\d,]+)$', line)
                if m and current_stmt:
                    sign = -1 if m.group(1) == 'D' else 1
                    current_stmt['balance_start'] = sign * float(m.group(4).replace(',', '.'))
                    current_stmt['date'] = f'20{m.group(2)[:2]}-{m.group(2)[2:4]}-{m.group(2)[4:6]}'
            elif line.startswith(':62F:'):  # Closing balance
                m = re.match(r'^:62F:([CD])(\d{6})([A-Z]{3})([\d,]+)$', line)
                if m and current_stmt:
                    sign = -1 if m.group(1) == 'D' else 1
                    current_stmt['balance_end_real'] = sign * float(m.group(4).replace(',', '.'))
            elif line.startswith(':61:'):  # Transaction line
                # :61:2501140114DR500,00NTRFNONREF//REF123
                m = re.match(r'^:61:(\d{6})(\d{6})?([CD])([\d,]+)(\w{4})(\w+)?', line)
                if m:
                    date_str = f'20{m.group(1)[:2]}-{m.group(1)[2:4]}-{m.group(1)[4:6]}'
                    sign = -1 if m.group(3) == 'D' else 1
                    amount = sign * float(m.group(4).replace(',', '.'))
                    ref = line.split('//', 1)[-1].strip() if '//' in line else ''
                    current_txs.append({
                        'date': date_str,
                        'payment_ref': ref or 'MT940 transaction',
                        'amount': amount,
                        'partner_name': '',
                        'account_number': '',
                        'unique_import_id': f'{date_str}-{amount}-{len(current_txs)}',
                        'ref': ref[:128],
                    })
            elif line.startswith(':86:'):  # Transaction details
                if current_txs:
                    current_txs[-1]['payment_ref'] = line[4:][:500]

        if current_stmt:
            current_stmt['transactions'] = current_txs
            statements.append(current_stmt)

        return statements

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------

    @api.model
    def _parse_file(self, data_file):
        """Override Odoo's hook to detect CAMT.053 / MT940 with SI quirks."""
        # Try CAMT.053 (XML) first
        if data_file.lstrip().startswith(b'<') or data_file.lstrip()[:5] == b'<?xml':
            try:
                statements = self._parse_si_camt053(data_file)
                if statements:
                    return self._format_si_result(statements, 'camt053')
            except ET.ParseError:
                pass  # fall through to MT940

        # Try MT940
        try:
            content = data_file.decode('utf-8', errors='replace')
            if ':20:' in content and ':61:' in content:
                statements = self._parse_si_mt940(content)
                if statements:
                    return self._format_si_result(statements, 'mt940')
        except Exception as e:  # noqa: BLE001
            _logger.warning('MT940 parse failed: %s', e)

        # Fall back to parent
        return super()._parse_file(data_file)

    def _format_si_result(self, statements, format_name):
        """Return the tuple Odoo expects: (currency_code, account_number, [statements])."""
        currency = 'EUR'
        account_number = statements[0].get('account_number', '') if statements else ''
        return currency, account_number, statements
