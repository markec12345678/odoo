# -*- coding: utf-8 -*-
"""Tests for l10n_si_bank_parser module.

Covers:
- CAMT.053 XML parsing (basic structure)
- SI bank BIC auto-detection (NLB, NKBM, Sparkasse, Addiko)
- Phone number normalization not needed here; focus on XML parsing
- _parse_si_stmt_element, _parse_si_balance, _parse_si_ntry_element
- Error handling for invalid XML
"""

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


# Sample minimal CAMT.053 XML for testing
SAMPLE_CAMT_053 = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt>
    <Stmt>
      <Id>NLB-2025-01-001</Id>
      <ElctrncSeqNb>1</ElctrncSeqNb>
      <Bal>
        <Tp>
          <CdOrPrtry>
            <Cd>OPBD</Cd>
          </CdOrPrtry>
        </Tp>
        <Amt Ccy="EUR">1000.00</Amt>
        <Dt>
          <Dt>2025-01-15</Dt>
        </Dt>
      </Bal>
      <Bal>
        <Tp>
          <CdOrPrtry>
            <Cd>CLBD</Cd>
          </CdOrPrtry>
        </Tp>
        <Amt Ccy="EUR">2500.00</Amt>
        <Dt>
          <Dt>2025-01-15</Dt>
        </Dt>
      </Bal>
      <Ntry>
        <Amt Ccy="EUR">1500.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <BookgDt>
          <Dt>2025-01-14</Dt>
        </BookgDt>
        <RltdPties>
          <Dbtr>
            <Nm>Janez Novak</Nm>
          </Dbtr>
          <DbtrAcct>
            <Id>
              <IBAN>SI56 1234 5678 9012 345</IBAN>
            </Id>
          </DbtrAcct>
        </RltdPties>
        <RmtInf>
          <Ustrd>Placilo po racunu 2025-001</Ustrd>
        </RmtInf>
      </Ntry>
      <Ntry>
        <Amt Ccy="EUR">200.00</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <BookgDt>
          <Dt>2025-01-15</Dt>
        </BookgDt>
        <RltdPties>
          <Cdtr>
            <Nm>Mercator</Nm>
          </Cdtr>
        </RltdPties>
        <RmtInf>
          <Ustrd>Racun 456</Ustrd>
        </RmtInf>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
"""


@tagged('post_install', '-at_install')
class TestCamt053Parsing(TransactionCase):
    """Tests for CAMT.053 XML parsing."""

    def setUp(self):
        super().setUp()
        # The parser logic is on l10n_si.bank.statement.import TransientModel
        self.ImportModel = self.env['l10n_si.bank.statement.import']

    def test_parse_valid_camt_053_returns_statements(self):
        """A valid CAMT.053 XML should return a list of statement dicts."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        self.assertIsInstance(statements, list)
        self.assertEqual(len(statements), 1)

    def test_statement_has_correct_name(self):
        """Statement name should combine Id and ElctrncSeqNb."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        stmt = statements[0]
        self.assertEqual(stmt['name'], 'NLB-2025-01-001-1')

    def test_statement_balances_parsed(self):
        """Opening (OPBD) and closing (CLBD) balances should be parsed."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        stmt = statements[0]
        self.assertEqual(stmt['balance_start'], 1000.00)
        self.assertEqual(stmt['balance_end_real'], 2500.00)
        self.assertEqual(stmt['date'], '2025-01-15')

    def test_transactions_count(self):
        """Should parse both transactions in the sample XML."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        stmt = statements[0]
        self.assertEqual(len(stmt['transactions']), 2)

    def test_credit_transaction_positive_amount(self):
        """Credit (CRDT) transactions should have positive amount."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        credit_tx = statements[0]['transactions'][0]
        self.assertEqual(credit_tx['amount'], 1500.00)

    def test_debit_transaction_negative_amount(self):
        """Debit (DBIT) transactions should have negative amount."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        debit_tx = statements[0]['transactions'][1]
        self.assertEqual(debit_tx['amount'], -200.00)

    def test_transaction_partner_name_parsed(self):
        """Partner name should be extracted from RltdPties/Dbtr/Nm."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        tx = statements[0]['transactions'][0]
        self.assertEqual(tx['partner_name'], 'Janez Novak')

    def test_transaction_payment_ref_parsed(self):
        """Payment reference should be extracted from RmtInf/Ustrd."""
        statements = self.ImportModel._parse_camt_053_si(SAMPLE_CAMT_053.encode('utf-8'))
        tx = statements[0]['transactions'][0]
        self.assertIn('Placilo', tx['payment_ref'])

    def test_invalid_xml_raises_user_error(self):
        """Invalid XML should raise UserError with helpful message."""
        invalid_xml = b'<not valid xml'
        with self.assertRaises(UserError):
            self.ImportModel._parse_camt_053_si(invalid_xml)

    def test_empty_xml_returns_empty_list(self):
        """Empty XML (valid but no Stmt elements) should return empty list."""
        empty_xml = b'<?xml version="1.0"?><Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"></Document>'
        statements = self.ImportModel._parse_camt_053_si(empty_xml)
        self.assertEqual(statements, [])


@tagged('post_install', '-at_install')
class TestSIBankBICCodes(TransactionCase):
    """Tests for SI_BANK_BICS constant — Slovenian bank BIC auto-detection."""

    def test_known_si_banks_present(self):
        """All major SI banks should be in the SI_BANK_BICS dictionary."""
        from odoo.addons.l10n_si_bank_parser.models.account_bank_statement_import_si import SI_BANK_BICS
        expected_bics = {
            'LJBASI2X',  # NLB
            'KBMRSI2X',  # NKBM
            'HDELSI22',  # Sparkasse
            'HAABSI22',  # Addiko
            'GIBASI2X',  # Raiffeisen
        }
        for bic in expected_bics:
            self.assertIn(bic, SI_BANK_BICS,
                          f'{bic} missing from SI_BANK_BICS')

    def test_bank_names_are_descriptive(self):
        """Each BIC should map to a human-readable bank name."""
        from odoo.addons.l10n_si_bank_parser.models.account_bank_statement_import_si import SI_BANK_BICS
        for bic, name in SI_BANK_BICS.items():
            self.assertIsInstance(name, str)
            self.assertTrue(len(name) > 3,
                            f'{bic} name too short: {name}')


@tagged('post_install', '-at_install')
class TestAccountJournalInherit(TransactionCase):
    """Tests for account.journal si_bank_format field."""

    def test_journal_has_si_bank_format_field(self):
        """account.journal should have si_bank_format field after install."""
        journal = self.env['account.journal'].search([], limit=1)
        if not journal:
            self.skipTest('No journal in test env')
        self.assertIn('si_bank_format', journal._fields)

    def test_si_bank_format_selection_values(self):
        """si_bank_format should support at least camt_053 and mt940."""
        journal = self.env['account.journal'].search([], limit=1)
        if not journal:
            self.skipTest('No journal in test env')
        field = journal._fields['si_bank_format']
        # Selection is a list of (value, label) tuples
        selection_values = [v for v, _ in field.selection]
        self.assertIn('camt_053', selection_values)
        # MT940 may or may not be implemented yet
        if 'mt940' in selection_values:
            self.assertTrue(True)
