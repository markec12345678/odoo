# -*- coding: utf-8 -*-
"""Unit tests for AJPES eTurizem SOAP client.

Pure unit tests — no Odoo DB needed. Tests the client logic standalone.
"""
import sys
import unittest.mock
from unittest.mock import MagicMock, patch

# Mock odoo for standalone execution
sys.modules['odoo'] = unittest.mock.MagicMock()
sys.modules['odoo.exceptions'] = unittest.mock.MagicMock()
sys.modules['odoo.tests'] = unittest.mock.MagicMock()

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'l10n_si_etourism', 'models'))

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_si_etourism.models.ajpes_client import (
    AJPESClient,
    AJPESAuthError,
    AJPESValidationError,
    AJPESConnectionError,
    AJPESUnknownError,
    ENDPOINT_TEST,
    ENDPOINT_PRODUCTION,
)


@tagged('post_install', '-at_install')
class TestAJPESClientConfig(TransactionCase):

    def test_test_endpoint(self):
        client = AJPESClient('u', 'p', environment='test')
        self.assertEqual(client.endpoint, ENDPOINT_TEST)

    def test_prod_endpoint(self):
        client = AJPESClient('u', 'p', environment='prod')
        self.assertEqual(client.endpoint, ENDPOINT_PRODUCTION)

    def test_default_timeout(self):
        self.assertEqual(AJPESClient('u', 'p').timeout, 30)

    def test_custom_timeout(self):
        self.assertEqual(AJPESClient('u', 'p', timeout=60).timeout, 60)


@tagged('post_install', '-at_install')
class TestAJPESResultParsing(TransactionCase):

    def test_ok_with_receipt(self):
        receipt, raw = AJPESClient._parse_result('OK|12345')
        self.assertEqual(receipt, '12345')

    def test_ok_bare(self):
        receipt, raw = AJPESClient._parse_result('OK')
        self.assertEqual(receipt, '')

    def test_numeric_only(self):
        receipt, raw = AJPESClient._parse_result('9999')
        self.assertEqual(receipt, '9999')

    def test_err_raises_validation(self):
        with self.assertRaises(AJPESValidationError):
            AJPESClient._parse_result('ERR|001|Bad data')

    def test_slovenian_error_raises_validation(self):
        for msg in ['Napaka pri obdelavi', 'Neveljaven MID', 'napačen format']:
            with self.subTest(msg=msg):
                with self.assertRaises(AJPESValidationError):
                    AJPESClient._parse_result(msg)

    def test_empty_raises_unknown(self):
        with self.assertRaises(AJPESUnknownError):
            AJPESClient._parse_result('')


@tagged('post_install', '-at_install')
class TestAJPESResponseExtraction(TransactionCase):

    def test_extract_from_success(self):
        soap = '''<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <oddajPorociloResponse xmlns="http://www.ajpes.si/eturizem/">
      <oddajPorociloResult>OK|98765</oddajPorociloResult>
    </oddajPorociloResponse>
  </soap:Body>
</soap:Envelope>'''
        self.assertEqual(AJPESClient._extract_result(soap), 'OK|98765')

    def test_extract_fault_raises(self):
        soap = '''<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <soap:Fault>
      <faultcode>soap:Server</faultcode>
      <faultstring>Server error</faultstring>
    </soap:Fault>
  </soap:Body>
</soap:Envelope>'''
        with self.assertRaises(AJPESUnknownError):
            AJPESClient._extract_result(soap)


@tagged('post_install', '-at_install')
class TestAJPESHTTPErrorMapping(TransactionCase):

    def _mock_resp(self, code, text=''):
        m = MagicMock()
        m.status_code = code
        m.text = text
        return m

    @patch('odoo.addons.l10n_si_etourism.models.ajpes_client.requests.post')
    def test_http_401_raises_auth(self, mock_post):
        mock_post.return_value = self._mock_resp(401, 'Unauthorized')
        with self.assertRaises(AJPESAuthError):
            AJPESClient('u', 'p', environment='test').submit_guest_book('<x/>')

    @patch('odoo.addons.l10n_si_etourism.models.ajpes_client.requests.post')
    def test_http_500_raises_connection(self, mock_post):
        mock_post.return_value = self._mock_resp(500, 'Server error')
        with self.assertRaises(AJPESConnectionError):
            AJPESClient('u', 'p', environment='test').submit_guest_book('<x/>')

    @patch('odoo.addons.l10n_si_etourism.models.ajpes_client.requests.post')
    def test_timeout_raises_connection(self, mock_post):
        import requests
        mock_post.side_effect = requests.Timeout('t')
        with self.assertRaises(AJPESConnectionError):
            AJPESClient('u', 'p', environment='test', timeout=5).submit_guest_book('<x/>')

    @patch('odoo.addons.l10n_si_etourism.models.ajpes_client.requests.post')
    def test_http_200_returns_receipt(self, mock_post):
        soap = '''<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <oddajPorociloResponse xmlns="http://www.ajpes.si/eturizem/">
      <oddajPorociloResult>OK|abc-123</oddajPorociloResult>
    </oddajPorociloResponse>
  </soap:Body>
</soap:Envelope>'''
        mock_post.return_value = self._mock_resp(200, soap)
        receipt, raw = AJPESClient('u', 'p', environment='test').submit_guest_book('<GuestBook/>')
        self.assertEqual(receipt, 'abc-123')

    @patch('odoo.addons.l10n_si_etourism.models.ajpes_client.requests.post')
    def test_basic_auth_credentials_passed(self, mock_post):
        soap = '''<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <oddajPorociloResponse xmlns="http://www.ajpes.si/eturizem/">
      <oddajPorociloResult>OK|x</oddajPorociloResult>
    </oddajPorociloResponse>
  </soap:Body>
</soap:Envelope>'''
        mock_post.return_value = self._mock_resp(200, soap)
        AJPESClient('myuser', 'mypass', environment='test').submit_guest_book('<x/>')
        call_args = mock_post.call_args
        self.assertIn('myuser', str(call_args))
        self.assertIn('mypass', str(call_args))
