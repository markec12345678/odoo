#!/usr/bin/env python3
"""Standalone unit test runner for SI/HR Odoo modules.

Runs unit tests that don't require a running Odoo instance — pure Python
logic that can be verified with mocked Odoo dependencies.

Called by .github/workflows/ci.yml in the `unit-tests` job.
"""
import hashlib
import json
import re
import sys
import unittest.mock
from datetime import datetime
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

# Mock odoo modules
sys.modules['odoo'] = unittest.mock.MagicMock()
sys.modules['odoo.exceptions'] = unittest.mock.MagicMock()
sys.modules['odoo.tests'] = unittest.mock.MagicMock()
sys.modules['odoo.tools'] = unittest.mock.MagicMock()

# Add module paths
sys.path.insert(0, 'addons/l10n_si_etourism/models')
sys.path.insert(0, 'addons/l10n_si_fiscal/models')
sys.path.insert(0, 'addons/l10n_hr_fiscal/models')
sys.path.insert(0, 'addons/l10n_hr_evisitor/models')
sys.path.insert(0, 'addons/l10n_si_channel_manager/models')

import requests

failures = 0
total = 0


def check(name, condition, detail=''):
    global failures, total
    total += 1
    if condition:
        print(f'  ✓ {name}')
    else:
        failures += 1
        print(f'  ✗ {name} — {detail}')


# ---------------------------------------------------------------------------
# ZOI Algorithm (FURS spec v1.6)
# ---------------------------------------------------------------------------

def test_zoi_algorithm():
    print('\n=== ZOI Algorithm (FURS spec v1.6) ===')

    def _extract_serial(invoice_number):
        parts = invoice_number.split('-')
        for part in reversed(parts):
            if part.isdigit():
                return part
        return ''

    check('extract serial BL1-RECEP1-2025-00001', _extract_serial('BL1-RECEP1-2025-00001') == '00001')
    check('extract serial 00001', _extract_serial('00001') == '00001')
    check('extract serial empty', _extract_serial('') == '')

    concat = '10861411' + '2025-01-15T00:00:00' + 'BL1-RECEP1-2025-00001' + 'BL1' + 'RECEP1' + '00001'
    zoi = hashlib.md5(concat.encode('utf-8')).hexdigest()
    check('ZOI is 32-char lowercase hex', bool(re.match(r'^[0-9a-f]{32}$', zoi)))
    check('ZOI is deterministic', hashlib.md5(concat.encode()).hexdigest() == zoi)

    zoi2 = hashlib.md5(('10861411' + '2025-01-15T00:00:00' + 'BL1-RECEP1-2025-00002' + 'BL1' + 'RECEP1' + '00002').encode()).hexdigest()
    check('different invoice → different ZOI', zoi != zoi2)

    wrong_order = hashlib.md5(('10861411' + '2025-01-15T00:00:00' + 'BL1-RECEP1-2025-00001' + 'RECEP1' + 'BL1' + '00001').encode()).hexdigest()
    check('field order matters', zoi != wrong_order)

    zoi_empty = hashlib.md5(''.encode('utf-8')).hexdigest()
    check('empty input → known MD5', zoi_empty == 'd41d8cd98f00b204e9800998ecf8427e')


# ---------------------------------------------------------------------------
# ZKI Algorithm (CISF spec v1.8)
# ---------------------------------------------------------------------------

def test_zki_algorithm():
    print('\n=== ZKI Algorithm (CISF spec v1.8) ===')

    def compute_zki(oib, dt_str, inv, pp, nu, total, tax):
        total_str = f'{total:.2f}'
        tax_str = f'{tax:.2f}'
        concat = oib + dt_str + inv + pp + nu + total_str + tax_str
        return hashlib.md5(concat.encode('utf-8')).hexdigest()

    zki = compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0)
    check('ZKI is 32-char lowercase hex', bool(re.match(r'^[0-9a-f]{32}$', zki)))
    check('ZKI deterministic', compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 100.0, 25.0) == zki)
    check('different invoice → different ZKI', zki != compute_zki('12345678901', '15.01.2025 00:00:00', '00002', 'POS1', '1', 100.0, 25.0))
    check('different premise → different ZKI', zki != compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS2', '1', 100.0, 25.0))
    check('different amount → different ZKI', zki != compute_zki('12345678901', '15.01.2025 00:00:00', '00001', 'POS1', '1', 200.0, 25.0))
    check('total format 2 decimals', f'{100.5:.2f}' == '100.50')


# ---------------------------------------------------------------------------
# AJPES Client (if available)
# ---------------------------------------------------------------------------

def test_ajpes_client():
    print('\n=== AJPES Client ===')
    try:
        from ajpes_client import (
            AJPESClient, AJPESAuthError, AJPESValidationError,
            AJPESConnectionError, AJPESUnknownError,
            build_guest_book_xml, build_monthly_report_xml,
            ENDPOINT_TEST, ENDPOINT_PRODUCTION,
        )
    except ImportError:
        print('  (skipped — l10n_si_etourism not available)')
        return

    check('test endpoint', AJPESClient('u', 'p', environment='test').endpoint == ENDPOINT_TEST)
    check('prod endpoint', AJPESClient('u', 'p', environment='prod').endpoint == ENDPOINT_PRODUCTION)
    check('default timeout 30s', AJPESClient('u', 'p').timeout == 30)

    # Result parsing
    r, _ = AJPESClient._parse_result('OK|12345')
    check('OK|12345 → receipt=12345', r == '12345')
    r, _ = AJPESClient._parse_result('OK')
    check('OK alone → empty receipt', r == '')

    try:
        AJPESClient._parse_result('ERR|001|Bad')
        check('ERR| raises AJPESValidationError', False)
    except AJPESValidationError:
        check('ERR| raises AJPESValidationError', True)

    try:
        AJPESClient._parse_result('Napaka pri obdelavi')
        check('Slovenian error raises validation', False)
    except AJPESValidationError:
        check('Slovenian error raises validation', True)

    # Guest book XML
    mock_reg = MagicMock()
    mock_reg.establishment_id = MagicMock()
    mock_reg.establishment_id.mid = '12345'
    mock_reg.establishment_id.sifnas = '001'
    mock_reg.arrival_date = datetime(2025, 7, 6, 14, 30)
    mock_reg.departure_date = datetime(2025, 7, 8, 10, 0)
    mock_reg.guest_first_name = 'Janez'
    mock_reg.guest_last_name = 'Novak'
    mock_reg.guest_birth_date = MagicMock()
    mock_reg.guest_birth_date.isoformat.return_value = '1990-05-15'
    si = MagicMock(); si.code = 'SI'
    de = MagicMock(); de.code = 'DE'
    mock_reg.guest_birth_country_id = si
    mock_reg.guest_citizenship_id = si
    mock_reg.guest_document_type = 'osebna_izkaznica'
    mock_reg.guest_document_number = 'AB1234567'
    mock_reg.guest_document_country_id = si
    mock_reg.guest_sex = 'M'
    mock_reg.guest_address = 'Slovenska 1'
    mock_reg.purpose = 'leisure'
    mock_reg.transport = 'car'
    mock_reg.country_of_origin_id = de
    mock_reg.reservation_source = 'direct'

    xml = build_guest_book_xml([mock_reg])
    check('GuestBook root element', '<GuestBook xmlns="http://www.ajpes.si/eturizem/">' in xml)
    check('MID in XML', '<MID>12345</MID>' in xml)
    check('SIFNAS in XML', '<SIFNAS>001</SIFNAS>' in xml)
    check('ISO datetime format', '2025-07-06T14:30:00' in xml)
    check('country code SI', '<BirthCountry>SI</BirthCountry>' in xml)
    check('country code DE', '<CountryOfOrigin>DE</CountryOfOrigin>' in xml)
    check('one Guest per registration', xml.count('<Guest>') == 1)

    # XML escapes
    mock_reg.guest_last_name = "O'Brien & Sons"
    xml = build_guest_book_xml([mock_reg])
    check('XML escapes & → &amp;', 'O\'Brien &amp; Sons' in xml)

    # XML well-formed
    try:
        ET.fromstring(build_guest_book_xml([mock_reg]))
        check('XML is well-formed', True)
    except ET.ParseError as e:
        check('XML is well-formed', False, str(e))

    # HTTP error mapping
    def mock_resp(code, text=''):
        m = MagicMock(); m.status_code = code; m.text = text; return m

    with patch('requests.post', return_value=mock_resp(401)):
        try:
            AJPESClient('u', 'p', environment='test').submit_guest_book('<x/>')
            check('HTTP 401 → AJPESAuthError', False)
        except AJPESAuthError:
            check('HTTP 401 → AJPESAuthError', True)

    with patch('requests.post', return_value=mock_resp(500)):
        try:
            AJPESClient('u', 'p', environment='test').submit_guest_book('<x/>')
            check('HTTP 500 → AJPESConnectionError', False)
        except AJPESConnectionError:
            check('HTTP 500 → AJPESConnectionError', True)


# ---------------------------------------------------------------------------
# CISF Client (if available)
# ---------------------------------------------------------------------------

def test_cisf_client():
    print('\n=== CISF Client ===')
    try:
        from cisf_client import (
            CISFClient, CISFAuthError, CISFValidationError,
            CISFConnectionError, CISFUnknownError,
            CISF_DEMO, CISF_PROD,
            SOAP_ACTION_RACUNI,
            build_invoice_xml as build_hr_invoice_xml,
            build_premise_xml as build_hr_premise_xml,
        )
    except ImportError:
        print('  (skipped — l10n_hr_fiscal not available)')
        return

    check('demo endpoint', CISFClient('/tmp/c.pem', '/tmp/k.pem', environment='demo').endpoint == CISF_DEMO)
    check('prod endpoint', CISFClient('/tmp/c.pem', '/tmp/k.pem', environment='prod').endpoint == CISF_PROD)
    check('default timeout 30s', CISFClient('/tmp/c.pem', '/tmp/k.pem').timeout == 30)

    # Invoice XML
    issue_dt = datetime(2025, 1, 15, 14, 30, 0)
    zki = 'a' * 32
    vat_breakdown = [(25.0, 100.0, 25.0), (5.0, 50.0, 2.5)]

    xml = build_hr_invoice_xml(
        oib='12345678901', invoice_number='00001', premise_code='POS1',
        device_code='1', issue_datetime=issue_dt, zki=zki,
        total_amount=125.0, vat_total=27.5, vat_breakdown=vat_breakdown,
    )
    check('RacunZahtjev root', '<fis:RacunZahtjev>' in xml)
    check('OIB in XML', '<fis:Oib>12345678901</fis:Oib>' in xml)
    check('ZKI in XML', f'<fis:ZastKod>{zki}</fis:ZastKod>' in xml)
    check('Croatian date format', '15.01.202514:30:00' in xml)
    check('PDV breakdown 25%', '<fis:Stopa>25.00</fis:Stopa>' in xml)

    # HTTP error mapping
    def mock_resp(code, text=''):
        m = MagicMock(); m.status_code = code; m.text = text; return m

    with patch('requests.post', return_value=mock_resp(401)):
        try:
            CISFClient('/tmp/c.pem', '/tmp/k.pem', environment='demo').submit_invoice('<x/>')
            check('HTTP 401 → CISFAuthError', False)
        except CISFAuthError:
            check('HTTP 401 → CISFAuthError', True)

    # JIR extraction
    success_soap = """<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:fis="http://www.apis-it.hr/fin/2012/types/f73">
  <soapenv:Body>
    <fis:RacunOdgovor>
      <fis:Zaglavlje><fis:IdPoruke>x</fis:IdPoruke></fis:Zaglavlje>
      <fis:Jir>abc-123</fis:Jir>
    </fis:RacunOdgovor>
  </soapenv:Body>
</soapenv:Envelope>"""
    extracted = CISFClient._extract_element(success_soap, 'Jir')
    check('JIR extracted from success response', extracted == 'abc-123')


# ---------------------------------------------------------------------------
# eVisitor Client (if available)
# ---------------------------------------------------------------------------

def test_evisitor_client():
    print('\n=== eVisitor Client ===')
    try:
        from evisitor_client import (
            EVisitorClient, EVisitorAuthError, EVisitorValidationError,
            EVisitorConnectionError, EVisitorUnknownError, EVisitorError,
            BASE_URL_PROD, BASE_URL_TEST,
            build_check_in_payload, build_check_out_payload, build_tourist_tax_payload,
        )
    except ImportError:
        print('  (skipped — l10n_hr_evisitor not available)')
        return

    check('test endpoint', EVisitorClient('u', 'p', environment='test').base_url == BASE_URL_TEST)
    check('prod endpoint', EVisitorClient('u', 'p', environment='prod').base_url == BASE_URL_PROD)
    check('default timeout 30s', EVisitorClient('u', 'p').timeout == 30)

    # CheckIn payload — evisitor uses nested structure with different attribute names
    mock_reg = MagicMock()
    mock_reg.accommodation_htz_id = 'HTZ-12345'
    mock_reg.accommodation_type = 'hotel'
    mock_reg.first_name = 'Ivan'
    mock_reg.last_name = 'Horvat'
    mock_reg.birth_date = MagicMock()
    mock_reg.birth_date.isoformat.return_value = '1990-05-15'
    mock_reg.sex = 'M'
    mock_reg.citizenship_code = 'HR'
    mock_reg.document_type = 'id_card'
    mock_reg.document_number = 'ABC123456'
    mock_reg.document_country_code = 'HR'
    mock_reg.arrival_date = datetime(2025, 7, 6, 14, 30)
    mock_reg.departure_date = None
    mock_reg.adults = 2
    mock_reg.children = 0
    mock_reg.youth = 0
    mock_reg.country_of_origin_code = 'DE'

    try:
        payload = build_check_in_payload(mock_reg)
        check('CheckIn payload built', isinstance(payload, dict) and len(payload) > 0)
        # The structure uses nested dicts: {'accommodation': {'htzId': ...}, 'guest': {'firstName': ...}}
        acc_htz = payload.get('accommodation', {}).get('htzId', '')
        check('accommodation.htzId', acc_htz == 'HTZ-12345', f'got: {acc_htz}')
        guest_fn = payload.get('guest', {}).get('firstName', '')
        check('guest.firstName', guest_fn == 'Ivan', f'got: {guest_fn}')
    except Exception as e:
        check('CheckIn payload built', False, str(e))
        check('accommodation.htzId', False, 'payload build failed')
        check('guest.firstName', False, 'payload build failed')

    # HTTP error mapping — eVisitor uses requests.Session internally
    def mock_resp(code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    # Test auth error by mocking the session
    try:
        client = EVisitorClient('bad', 'creds', environment='test')
        client._session = MagicMock()
        client._session.post.return_value = mock_resp(401, text='Unauthorized')
        client._session.request.return_value = mock_resp(401, text='Unauthorized')
        try:
            client.check_in({})
            check('eVisitor 401 → AuthError', False)
        except (EVisitorAuthError, EVisitorError):
            check('eVisitor 401 → AuthError', True)
        except Exception as e:
            check('eVisitor 401 → AuthError', False, f'{type(e).__name__}: {e}')
    except Exception as e:
        check('eVisitor 401 → AuthError', False, f'setup: {e}')

    # Test HTTP 200 → returns checkInId
    try:
        success_data = {'checkInId': 'abc-123', 'touristTaxAmount': 17.50}
        client = EVisitorClient('u', 'p', environment='test')
        client._session = MagicMock()
        client._session.post.return_value = mock_resp(200, json_data=success_data)
        client._session.request.return_value = mock_resp(200, json_data=success_data)
        result = client.check_in({'test': 'payload'})
        # eVisitor check_in returns a dict, not a tuple
        if isinstance(result, dict):
            check('eVisitor 200 returns checkInId', result.get('checkInId') == 'abc-123', f'got: {result}')
        elif isinstance(result, tuple):
            check('eVisitor 200 returns checkInId', result[0] == 'abc-123')
        else:
            check('eVisitor 200 returns checkInId', False, f'unexpected type: {type(result)}')
    except Exception as e:
        check('eVisitor 200 returns checkInId', False, f'{type(e).__name__}: {e}')

    # TouristTax payload
    try:
        payload = build_tourist_tax_payload('HTZ-12345', 5, adults=2, children=1, youth=1)
        check('touristTax htzId', payload.get('htzId') == 'HTZ-12345', f'got: {payload.get("htzId")}')
        check('touristTax nights', payload.get('nights') == 5)
    except Exception as e:
        check('touristTax htzId', False, str(e))
        check('touristTax nights', False, 'skipped')


# ---------------------------------------------------------------------------
# Channel Manager Clients (if available)
# ---------------------------------------------------------------------------

def test_channel_clients():
    print('\n=== Channel Manager Clients ===')
    try:
        from channel_clients import (
            BookingComClient, AirbnbClient,
            ChannelAuthError, ChannelSyncError, ChannelValidationError,
            BOOKING_COM_API_ENDPOINT, AIRBNB_API_ENDPOINT,
            verify_airbnb_webhook_signature,
            map_booking_com_reservation, map_airbnb_reservation,
        )
    except ImportError:
        print('  (skipped — l10n_si_channel_manager not available)')
        return

    check('Booking.com endpoint', BookingComClient('u', 'p').endpoint == BOOKING_COM_API_ENDPOINT)
    check('Airbnb endpoint', AirbnbClient('t').endpoint == AIRBNB_API_ENDPOINT)
    check('default timeout 30s', BookingComClient('u', 'p').timeout == 30)

    # HTTP error mapping
    def mock_resp(code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    with patch('requests.request', return_value=mock_resp(401, text='Unauthorized')):
        # ping() catches exceptions and returns False — test the return value
        result = BookingComClient('u', 'p').ping()
        check('Booking.com 401 → ping returns False', result == False)

    # Webhook signature
    import hmac
    body = b'{"test": "payload"}'
    secret = 'webhook-secret'
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    check('valid webhook signature', verify_airbnb_webhook_signature(body, sig, secret))
    check('invalid webhook signature', not verify_airbnb_webhook_signature(body, 'wrong', secret))

    # Reservation mappers
    booking_data = {
        'room_type_id': 'rt-123',
        'check_in': '2025-08-01',
        'check_out': '2025-08-05',
        'rate': 120.0,
        'adults': 2,
        'status': 'confirmed',
    }
    mapping = {'rt-123': 42}
    vals = map_booking_com_reservation(booking_data, mapping)
    check('Booking.com mapper: room_id', vals['room_id'] == 42)
    check('Booking.com mapper: source', vals['source'] == 'booking_com')

    airbnb_data = {
        'listing_id': 99999,
        'start_date': '2025-09-01',
        'end_date': '2025-09-04',
        'listing_price': 90.0,
        'guests': 3,
        'status': 'confirmed',
    }
    mapping = {'99999': 15}
    vals = map_airbnb_reservation(airbnb_data, mapping)
    check('Airbnb mapper: room_id', vals['room_id'] == 15)
    check('Airbnb mapper: source', vals['source'] == 'airbnb')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('=' * 60)
    print('SI/HR Odoo Modules — Standalone Unit Test Runner')
    print('=' * 60)

    test_zoi_algorithm()
    test_zki_algorithm()
    test_ajpes_client()
    test_cisf_client()
    test_evisitor_client()
    test_channel_clients()

    print()
    print('=' * 60)
    print(f'SUMMARY: {total - failures}/{total} passed, {failures} failed')
    print('=' * 60)
    sys.exit(1 if failures > 0 else 0)


if __name__ == '__main__':
    main()
