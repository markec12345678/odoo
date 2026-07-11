# -*- coding: utf-8 -*-
"""Tests for l10n_hr_kuna module (Croatian RRIF chart of accounts).

Covers:
- CSV template data integrity (account, tax, fiscal position, tax group)
- Account code pattern validation (RRIF chart uses 4-digit codes)
- Template model methods return expected structure
- Tax report XML is well-formed
"""
import csv
import os
from pathlib import Path

from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import file_path


def _read_csv(module_name, filename):
    """Helper: read a CSV file from a module's data/template/ directory."""
    path = file_path(f'{module_name}/data/template/{filename}')
    with open(path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


@tagged('post_install', '-at_install')
class TestHrKunaChartTemplate(TransactionCase):
    """Tests for the Croatian RRIF chart template model."""

    def test_template_model_exists(self):
        """account.chart.template should be extended by l10n_hr_kuna."""
        # The _inherit is on account.chart.template
        chart_template = self.env['account.chart.template']
        self.assertTrue(chart_template)

    def test_get_hr_kuna_template_data(self):
        """_get_hr_kuna_template_data should return the expected dict."""
        # Get an instance of the abstract model
        chart_template = self.env['account.chart.template']
        # The method is decorated with @template('hr_kuna')
        # We can call it directly to verify structure
        result = chart_template._get_hr_kuna_template_data()
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], 'RRIF-ov računski plan za poduzetnike')
        self.assertEqual(result['code_digits'], '6')
        self.assertTrue(result['use_storno_accounting'])
        # Property account references
        self.assertEqual(result['property_account_receivable_id'], 'kp_rrif1200')
        self.assertEqual(result['property_account_payable_id'], 'kp_rrif2200')

    def test_get_hr_kuna_res_company(self):
        """_get_hr_kuna_res_company should return company config dict."""
        chart_template = self.env['account.chart.template']
        result = chart_template._get_hr_kuna_res_company()
        self.assertIsInstance(result, dict)
        # Should map company_id -> dict of fields
        for company_id, vals in result.items():
            self.assertEqual(vals['account_fiscal_country_id'], 'base.hr')
            self.assertEqual(vals['bank_account_code_prefix'], '101')
            self.assertEqual(vals['cash_account_code_prefix'], '102')
            self.assertEqual(vals['transfer_account_code_prefix'], '1009')
            self.assertEqual(vals['expense_account_id'], 'kp_rrif4199')
            self.assertEqual(vals['income_account_id'], 'kp_rrif7500')


@tagged('post_install', '-at_install')
class TestHrKunaAccountCSV(TransactionCase):
    """Tests for the account.account-hr_kuna.csv file."""

    def setUp(self):
        super().setUp()
        self.accounts = _read_csv('l10n_hr_kuna', 'account.account-hr_kuna.csv')

    def test_csv_has_accounts(self):
        """The RRIF chart should have a substantial number of accounts."""
        self.assertGreater(len(self.accounts), 100,
                          'RRIF chart should have at least 100 accounts')

    def test_csv_has_required_columns(self):
        """CSV should have id, code, account_type, reconcile, name columns."""
        first = self.accounts[0]
        self.assertIn('id', first)
        self.assertIn('code', first)
        self.assertIn('account_type', first)
        self.assertIn('reconcile', first)
        self.assertIn('name', first)

    def test_all_accounts_have_id(self):
        """Every account row should have an id."""
        for acc in self.accounts:
            self.assertTrue(acc['id'], f'Account missing id: {acc}')

    def test_all_accounts_have_code(self):
        """Every account row should have a code."""
        for acc in self.accounts:
            self.assertTrue(acc['code'], f'Account {acc["id"]} missing code')

    def test_all_accounts_have_name(self):
        """Every account row should have a name."""
        for acc in self.accounts:
            self.assertTrue(acc['name'], f'Account {acc["id"]} missing name')

    def test_all_accounts_have_account_type(self):
        """Every account row should have an account_type."""
        for acc in self.accounts:
            self.assertTrue(acc['account_type'],
                            f'Account {acc["id"]} missing account_type')

    def test_account_ids_have_kp_rrif_prefix(self):
        """All account XML ids should start with 'kp_rrif'."""
        for acc in self.accounts:
            self.assertTrue(acc['id'].startswith('kp_rrif'),
                            f'Account id {acc["id"]} does not start with kp_rrif')

    def test_account_codes_are_4_digit(self):
        """RRIF chart uses 4-digit account codes (0000-9999)."""
        for acc in self.accounts:
            code = acc['code']
            self.assertEqual(len(code), 4,
                            f'Account {acc["id"]} code {code} is not 4 digits')
            self.assertTrue(code.isdigit(),
                           f'Account {acc["id"]} code {code} is not numeric')

    def test_account_types_are_valid(self):
        """account_type values should be in Odoo's allowed set."""
        valid_types = {
            'asset_current', 'asset_non_current', 'asset_cash', 'asset_receivable',
            'liability_current', 'liability_non_current', 'liability_credit_card',
            'liability_payable',
            'equity', 'equity_unaffected',
            'income', 'income_other',
            'expense', 'expense_depreciation', 'expense_direct_cost',
            'off_balance',
        }
        for acc in self.accounts:
            self.assertIn(acc['account_type'], valid_types,
                         f'Account {acc["id"]} has invalid type: {acc["account_type"]}')

    def test_account_codes_unique(self):
        """All account codes should be unique."""
        codes = [acc['code'] for acc in self.accounts]
        duplicates = [c for c in codes if codes.count(c) > 1]
        self.assertEqual(len(duplicates), 0,
                        f'Duplicate account codes found: {set(duplicates)}')

    def test_account_ids_unique(self):
        """All account XML ids should be unique."""
        ids = [acc['id'] for acc in self.accounts]
        duplicates = [i for i in ids if ids.count(i) > 1]
        self.assertEqual(len(duplicates), 0,
                        f'Duplicate account ids found: {set(duplicates)}')


@tagged('post_install', '-at_install')
class TestHrKunaTaxCSV(TransactionCase):
    """Tests for the account.tax-hr_kuna.csv file."""

    def setUp(self):
        super().setUp()
        self.taxes = _read_csv('l10n_hr_kuna', 'account.tax-hr_kuna.csv')

    def test_csv_has_taxes(self):
        """The RRIF chart should define multiple tax codes."""
        self.assertGreater(len(self.taxes), 10,
                          'Should have at least 10 tax codes')

    def test_csv_has_required_columns(self):
        """Tax CSV should have id, name, amount, tax_group_id columns."""
        first = self.taxes[0]
        self.assertIn('id', first)
        self.assertIn('name', first)
        # At least one of these should be present
        self.assertTrue('amount' in first or 'amount_type' in first)

    def test_all_taxes_have_id(self):
        """Every tax row should have an id."""
        for tax in self.taxes:
            self.assertTrue(tax['id'], f'Tax missing id: {tax}')

    def test_all_taxes_have_name(self):
        """Every tax row should have a name."""
        for tax in self.taxes:
            self.assertTrue(tax['name'], f'Tax {tax["id"]} missing name')

    def test_tax_ids_have_kp_prefix(self):
        """All tax XML ids should start with 'kp_'."""
        for tax in self.taxes:
            self.assertTrue(tax['id'].startswith('kp_'),
                           f'Tax id {tax["id"]} does not start with kp_')


@tagged('post_install', '-at_install')
class TestHrKunaFiscalPositionCSV(TransactionCase):
    """Tests for the account.fiscal.position-hr_kuna.csv file."""

    def setUp(self):
        super().setUp()
        self.positions = _read_csv('l10n_hr_kuna', 'account.fiscal.position-hr_kuna.csv')

    def test_csv_has_fiscal_positions(self):
        """Should define at least one fiscal position."""
        self.assertGreater(len(self.positions), 0,
                          'No fiscal positions defined')

    def test_csv_has_required_columns(self):
        """Fiscal position CSV should have id, name columns."""
        first = self.positions[0]
        self.assertIn('id', first)
        self.assertIn('name', first)

    def test_all_positions_have_id(self):
        """Every fiscal position row should have an id."""
        for pos in self.positions:
            self.assertTrue(pos['id'], f'Fiscal position missing id: {pos}')

    def test_all_positions_have_name(self):
        """Every fiscal position row should have a name."""
        for pos in self.positions:
            self.assertTrue(pos['name'], f'Fiscal position {pos["id"]} missing name')


@tagged('post_install', '-at_install')
class TestHrKunaTaxGroupCSV(TransactionCase):
    """Tests for the account.tax.group-hr_kuna.csv file."""

    def setUp(self):
        super().setUp()
        self.groups = _read_csv('l10n_hr_kuna', 'account.tax.group-hr_kuna.csv')

    def test_csv_has_tax_groups(self):
        """Should define at least one tax group."""
        self.assertGreater(len(self.groups), 0,
                          'No tax groups defined')

    def test_all_groups_have_id(self):
        """Every tax group row should have an id."""
        for g in self.groups:
            self.assertTrue(g['id'], f'Tax group missing id: {g}')

    def test_all_groups_have_name(self):
        """Every tax group row should have a name."""
        for g in self.groups:
            self.assertTrue(g['name'], f'Tax group {g["id"]} missing name')


@tagged('post_install', '-at_install')
class TestHrKunaTaxReportXML(TransactionCase):
    """Tests for the account_tax_report_data.xml file."""

    def test_tax_report_xml_well_formed(self):
        """The tax report XML should be well-formed."""
        import xml.etree.ElementTree as ET
        path = file_path('l10n_hr_kuna/data/account_tax_report_data.xml')
        tree = ET.parse(path)
        self.assertIsNotNone(tree)

    def test_tax_report_has_root_record(self):
        """The XML should define a tax_report record."""
        import xml.etree.ElementTree as ET
        path = file_path('l10n_hr_kuna/data/account_tax_report_data.xml')
        tree = ET.parse(path)
        root = tree.getroot()
        records = root.findall('.//record')
        # Should have at least the tax_report root record
        self.assertGreater(len(records), 0)

    def test_tax_report_country_is_hr(self):
        """The tax report should be for Croatia (base.hr)."""
        import xml.etree.ElementTree as ET
        path = file_path('l10n_hr_kuna/data/account_tax_report_data.xml')
        tree = ET.parse(path)
        root = tree.getroot()
        # Find the country_id field
        country_fields = root.findall('.//field[@name="country_id"]')
        self.assertGreater(len(country_fields), 0,
                          'No country_id field in tax report XML')
        self.assertEqual(country_fields[0].get('ref'), 'base.hr')

    def test_tax_report_name(self):
        """The tax report should be named 'Tax Report'."""
        import xml.etree.ElementTree as ET
        path = file_path('l10n_hr_kuna/data/account_tax_report_data.xml')
        tree = ET.parse(path)
        root = tree.getroot()
        name_fields = root.findall('.//field[@name="name"]')
        self.assertGreater(len(name_fields), 0)
        self.assertEqual(name_fields[0].text, 'Tax Report')


@tagged('post_install', '-at_install')
class TestHrKunaModuleMetadata(TransactionCase):
    """Tests for module-level metadata in __manifest__.py."""

    def setUp(self):
        super().setUp()
        from odoo.modules.module import get_module_info
        self.info = get_module_info('l10n_hr_kuna')

    def test_module_installable(self):
        """Module should be installable."""
        self.assertTrue(self.info.get('installable', False))

    def test_module_targets_croatia(self):
        """Module should target Croatia."""
        self.assertIn('hr', self.info.get('countries', []))

    def test_module_depends_on_account(self):
        """Module should depend on 'account'."""
        self.assertIn('account', self.info.get('depends', []))

    def test_module_license_is_lgpl(self):
        """Module should be LGPL-3 (open source)."""
        self.assertEqual(self.info.get('license'), 'LGPL-3')

    def test_module_category_is_accounting(self):
        """Module should be in Accounting/Localizations/Account Charts."""
        self.assertEqual(self.info.get('category'),
                        'Accounting/Localizations/Account Charts')
