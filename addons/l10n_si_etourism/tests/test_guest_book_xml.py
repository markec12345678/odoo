# -*- coding: utf-8 -*-
"""Tests for AJPES guest book XML builder."""
from datetime import datetime
from unittest.mock import MagicMock

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_si_etourism.models.ajpes_client import (
    build_guest_book_xml,
    build_monthly_report_xml,
)


@tagged('post_install', '-at_install')
class TestGuestBookXML(TransactionCase):

    def setUp(self):
        super().setUp()
        self.slovenia = self.env.ref('base.si')
        self.germany = self.env.ref('base.de')

        self.mock_reg = MagicMock()
        self.mock_reg.establishment_id = MagicMock()
        self.mock_reg.establishment_id.mid = '12345'
        self.mock_reg.establishment_id.sifnas = '001'
        self.mock_reg.arrival_date = datetime(2025, 7, 6, 14, 30, 0)
        self.mock_reg.departure_date = datetime(2025, 7, 8, 10, 0, 0)
        self.mock_reg.guest_first_name = 'Janez'
        self.mock_reg.guest_last_name = 'Novak'
        self.mock_reg.guest_birth_date = MagicMock()
        self.mock_reg.guest_birth_date.isoformat.return_value = '1990-05-15'
        self.mock_reg.guest_birth_country_id = self.slovenia
        self.mock_reg.guest_citizenship_id = self.slovenia
        self.mock_reg.guest_document_type = 'osebna_izkaznica'
        self.mock_reg.guest_document_number = 'AB1234567'
        self.mock_reg.guest_document_country_id = self.slovenia
        self.mock_reg.guest_sex = 'M'
        self.mock_reg.guest_address = 'Slovenska 1, Ljubljana'
        self.mock_reg.purpose = 'leisure'
        self.mock_reg.transport = 'car'
        self.mock_reg.country_of_origin_id = self.germany
        self.mock_reg.reservation_source = 'direct'

    def test_xml_has_guestbook_root(self):
        xml = build_guest_book_xml([self.mock_reg])
        self.assertIn('<GuestBook xmlns="http://www.ajpes.si/eturizem/">', xml)
        self.assertIn('</GuestBook>', xml)

    def test_xml_includes_mid_and_sifnas(self):
        xml = build_guest_book_xml([self.mock_reg])
        self.assertIn('<MID>12345</MID>', xml)
        self.assertIn('<SIFNAS>001</SIFNAS>', xml)

    def test_xml_includes_arrival_date_iso(self):
        xml = build_guest_book_xml([self.mock_reg])
        self.assertIn('2025-07-06T14:30:00', xml)

    def test_xml_includes_guest_data(self):
        xml = build_guest_book_xml([self.mock_reg])
        self.assertIn('Janez', xml)
        self.assertIn('Novak', xml)
        self.assertIn('1990-05-15', xml)

    def test_xml_includes_country_codes(self):
        xml = build_guest_book_xml([self.mock_reg])
        self.assertIn('<BirthCountry>SI</BirthCountry>', xml)
        self.assertIn('<Citizenship>SI</Citizenship>', xml)
        self.assertIn('<CountryOfOrigin>DE</CountryOfOrigin>', xml)

    def test_xml_escapes_special_chars(self):
        self.mock_reg.guest_last_name = "O'Brien & Sons"
        xml = build_guest_book_xml([self.mock_reg])
        self.assertIn('O\'Brien &amp; Sons', xml)

    def test_xml_is_well_formed(self):
        import xml.etree.ElementTree as ET
        xml = build_guest_book_xml([self.mock_reg])
        ET.fromstring(xml)  # raises on parse error

    def test_multiple_registrations(self):
        xml = build_guest_book_xml([self.mock_reg, self.mock_reg, self.mock_reg])
        self.assertEqual(xml.count('<Guest>'), 3)

    def test_empty_registrations_list(self):
        xml = build_guest_book_xml([])
        self.assertIn('<GuestBook', xml)
        self.assertNotIn('<Guest>', xml)

    def test_missing_country_handled(self):
        """Missing country fields should produce empty strings, not crash."""
        self.mock_reg.guest_birth_country_id = False
        self.mock_reg.country_of_origin_id = False
        xml = build_guest_book_xml([self.mock_reg])
        self.assertIn('<BirthCountry></BirthCountry>', xml)
        self.assertIn('<CountryOfOrigin></CountryOfOrigin>', xml)


@tagged('post_install', '-at_install')
class TestMonthlyReportXML(TransactionCase):

    def setUp(self):
        super().setUp()
        self.mock_report = MagicMock()
        self.mock_report.establishment_id = MagicMock()
        self.mock_report.establishment_id.mid = '12345'
        self.mock_report.establishment_id.sifnas = '001'
        self.mock_report.year = 2025
        self.mock_report.month = 6
        self.mock_report.total_arrivals = 150
        self.mock_report.total_nights = 420
        self.mock_report.by_country_json = '{"SI": 80, "DE": 30}'
        self.mock_report.by_purpose_json = '{"leisure": 100}'

    def test_xml_has_guestbookmr_root(self):
        xml = build_monthly_report_xml(self.mock_report)
        self.assertIn('<GuestBookMR xmlns="http://www.ajpes.si/eturizem/">', xml)

    def test_xml_includes_header(self):
        xml = build_monthly_report_xml(self.mock_report)
        self.assertIn('<Year>2025</Year>', xml)
        self.assertIn('<Month>06</Month>', xml)
        self.assertIn('<TotalArrivals>150</TotalArrivals>', xml)

    def test_xml_includes_country_breakdown(self):
        xml = build_monthly_report_xml(self.mock_report)
        self.assertIn('<Country code="SI">80</Country>', xml)
        self.assertIn('<Country code="DE">30</Country>', xml)

    def test_xml_well_formed(self):
        import xml.etree.ElementTree as ET
        xml = build_monthly_report_xml(self.mock_report)
        ET.fromstring(xml)

    def test_malformed_json_handled(self):
        self.mock_report.by_country_json = 'not valid json'
        xml = build_monthly_report_xml(self.mock_report)
        self.assertIn('<ByCountry>', xml)  # should not crash
