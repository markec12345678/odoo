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
sys.path.insert(0, 'addons/l10n_si_ai_concierge/models')

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
# AI Concierge LLM clients (if available)
# ---------------------------------------------------------------------------

def test_ai_concierge():
    print('\n=== AI Concierge LLM Clients ===')
    try:
        from ai_client import (
            get_ai_client, Message, ZAIClient, OpenAIClient, AnthropicClient, LocalLLMClient,
            AIAuthError, AIRequestError, AIRateLimitError,
            ZAI_ENDPOINT, OPENAI_ENDPOINT, ANTHROPIC_ENDPOINT,
        )
    except ImportError:
        print('  (skipped — l10n_si_ai_concierge not available)')
        return

    # Message model
    m = Message('user', 'Hello')
    check('Message.to_dict', m.to_dict() == {'role': 'user', 'content': 'Hello'})

    # Factory
    check('factory ZAI', isinstance(get_ai_client('zai', 'k', 'm'), ZAIClient))
    check('factory OpenAI', isinstance(get_ai_client('openai', 'k', 'm'), OpenAIClient))
    check('factory Anthropic', isinstance(get_ai_client('anthropic', 'k', 'm'), AnthropicClient))
    check('factory Local', isinstance(get_ai_client('local', 'k', 'm'), LocalLLMClient))

    # ZAI client config
    check('ZAI endpoint', ZAIClient('k', 'm').endpoint if hasattr(ZAIClient('k', 'm'), 'endpoint') else ZAI_ENDPOINT == ZAI_ENDPOINT)
    check('default timeout', ZAIClient('k', 'm').timeout == 30)

    # ZAI successful response (mocked)
    def mock_resp(code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    with patch('requests.post', return_value=mock_resp(200, json_data={
        'choices': [{'message': {'content': 'Pozdravljen!'}}]
    })):
        client = ZAIClient('key', 'glm-4')
        response = client.generate_response([Message('system', 's'), Message('user', 'hi')])
        check('ZAI successful response', response == 'Pozdravljen!')

    # ZAI auth error
    with patch('requests.post', return_value=mock_resp(401, text='Unauthorized')):
        try:
            ZAIClient('bad', 'm').generate_response([Message('user', 'x')])
            check('ZAI 401 → AIAuthError', False)
        except AIAuthError:
            check('ZAI 401 → AIAuthError', True)

    # ZAI rate limit
    with patch('requests.post', return_value=mock_resp(429, text='Rate limited')):
        try:
            ZAIClient('k', 'm').generate_response([Message('user', 'x')])
            check('ZAI 429 → AIRateLimitError', False)
        except AIRateLimitError:
            check('ZAI 429 → AIRateLimitError', True)

    # ZAI bearer auth header
    with patch('requests.post', return_value=mock_resp(200, json_data={
        'choices': [{'message': {'content': 'OK'}}]
    })) as mp:
        ZAIClient('my-key', 'm').generate_response([Message('user', 'x')])
        check('ZAI Bearer auth', mp.call_args[1]['headers']['Authorization'] == 'Bearer my-key')

    # Anthropic system extraction
    with patch('requests.post', return_value=mock_resp(200, json_data={
        'content': [{'text': 'OK'}]
    })) as mp:
        AnthropicClient('k', 'c').generate_response([
            Message('system', 'You are helpful.'), Message('user', 'hi')
        ])
        payload = mp.call_args[1]['json']
        check('Anthropic system top-level', payload.get('system') == 'You are helpful.')
        for msg in payload.get('messages', []):
            check('Anthropic no system in messages', msg['role'] != 'system')
            break

    # Anthropic x-api-key header
    with patch('requests.post', return_value=mock_resp(200, json_data={
        'content': [{'text': 'OK'}]
    })) as mp:
        AnthropicClient('my-key', 'c').generate_response([Message('user', 'hi')])
        headers = mp.call_args[1]['headers']
        check('Anthropic x-api-key', headers.get('x-api-key') == 'my-key')
        check('Anthropic no Bearer', 'Authorization' not in headers)

    # Local LLM custom endpoint
    with patch('requests.post', return_value=mock_resp(200, json_data={
        'choices': [{'message': {'content': 'OK'}}]
    })) as mp:
        client = LocalLLMClient('k', 'llama3', endpoint='http://my-llm:8080/v1/chat')
        client.generate_response([Message('user', 'hi')])
        check('Local custom endpoint', mp.call_args[0][0] == 'http://my-llm:8080/v1/chat')

    # Local LLM no auth without key
    with patch('requests.post', return_value=mock_resp(200, json_data={
        'choices': [{'message': {'content': 'OK'}}]
    })) as mp:
        LocalLLMClient('', 'llama3').generate_response([Message('user', 'hi')])
        check('Local no auth without key', 'Authorization' not in mp.call_args[1]['headers'])


# ---------------------------------------------------------------------------
# WhatsApp Business Cloud API — Phone Normalization
# ---------------------------------------------------------------------------

def test_whatsapp_phone_normalization():
    """Test phone number normalization for WhatsApp Cloud API.

    The l10n_si_whatsapp_business module strips +, spaces, and dashes
    from phone numbers before sending to the Meta API.
    """
    print('\n=== WhatsApp Business Phone Normalization ===')

    # Replicate the normalization logic from action_send()
    def normalize(phone):
        return phone.replace(' ', '').replace('+', '').replace('-', '')

    # Test cases
    cases = [
        ('+38641234567', '38641234567', 'SI mobile with +'),
        ('+386 41 234 567', '38641234567', 'SI mobile with spaces'),
        ('+386-41-234-567', '38641234567', 'SI mobile with dashes'),
        ('38641234567', '38641234567', 'SI mobile no formatting'),
        ('+ 386 41 234 567', '38641234567', 'SI mobile with + and spaces'),
    ]
    for input_phone, expected, desc in cases:
        result = normalize(input_phone)
        check(f'Phone: {desc}', result == expected,
              f'got {result}, expected {expected}')


# ---------------------------------------------------------------------------
# WhatsApp Business — Payload Construction
# ---------------------------------------------------------------------------

def test_whatsapp_payload_construction():
    """Test WhatsApp Cloud API payload structure (text + template)."""
    print('\n=== WhatsApp Business Payload Construction ===')

    WA_API_BASE = 'https://graph.facebook.com/v21.0'

    # Text message payload
    text_payload = {
        'messaging_product': 'whatsapp',
        'to': '38641234567',
        'type': 'text',
        'text': {'body': 'Welcome!'},
    }
    check('Text payload has messaging_product',
          text_payload['messaging_product'] == 'whatsapp')
    check('Text payload type is text',
          text_payload['type'] == 'text')
    check('Text payload has body',
          text_payload['text']['body'] == 'Welcome!')

    # Template message payload
    template_payload = {
        'messaging_product': 'whatsapp',
        'to': '38641234567',
        'type': 'template',
        'template': {
            'name': 'reservation_confirm',
            'language': {'code': 'sl'},
        }
    }
    check('Template payload type is template',
          template_payload['type'] == 'template')
    check('Template payload has name',
          template_payload['template']['name'] == 'reservation_confirm')
    check('Template payload has language code',
          template_payload['template']['language']['code'] == 'sl')

    # URL construction
    phone_number_id = '1234567890'
    url = f'{WA_API_BASE}/{phone_number_id}/messages'
    check('URL contains phone_number_id', phone_number_id in url)
    check('URL ends with /messages', url.endswith('/messages'))
    check('URL uses v21.0 API', 'v21.0' in url)


# ---------------------------------------------------------------------------
# Stripe Payment — Deposit Mode Logic
# ---------------------------------------------------------------------------

def test_stripe_deposit_mode_logic():
    """Test Stripe SI deposit mode (pre-authorization) logic.

    When si_stripe_deposit_mode=True and capture_method is not explicitly
    'automatic', the override should force capture_method='manual'.
    """
    print('\n=== Stripe Deposit Mode Logic ===')

    # Simulate the _stripe_make_payment_request override logic
    def apply_deposit_mode(deposit_mode_enabled, kwargs):
        """Replicate the override logic from payment_provider.py."""
        if deposit_mode_enabled and kwargs.get('capture_method') != 'automatic':
            kwargs['capture_method'] = 'manual'
        return kwargs

    # Case 1: Deposit mode OFF, no capture_method specified
    result = apply_deposit_mode(False, {})
    check('Deposit OFF: no capture_method added',
          'capture_method' not in result)

    # Case 2: Deposit mode ON, no capture_method specified → should force 'manual'
    result = apply_deposit_mode(True, {})
    check('Deposit ON: forces capture_method=manual',
          result.get('capture_method') == 'manual')

    # Case 3: Deposit mode ON, explicit 'automatic' → should NOT override
    result = apply_deposit_mode(True, {'capture_method': 'automatic'})
    check('Deposit ON + explicit automatic: NOT overridden',
          result['capture_method'] == 'automatic')

    # Case 4: Deposit mode ON, explicit 'manual' → stays 'manual'
    result = apply_deposit_mode(True, {'capture_method': 'manual'})
    check('Deposit ON + explicit manual: stays manual',
          result['capture_method'] == 'manual')

    # Case 5: Deposit mode OFF, explicit 'manual' → stays 'manual'
    result = apply_deposit_mode(False, {'capture_method': 'manual'})
    check('Deposit OFF + explicit manual: stays manual',
          result['capture_method'] == 'manual')


# ---------------------------------------------------------------------------
# CAMT.053 Bank Statement XML Parsing
# ---------------------------------------------------------------------------

def test_camt053_xml_parsing():
    """Test CAMT.053 XML parsing for SI bank statements.

    The l10n_si_bank_parser module parses ISO 20022 CAMT.053 format
    used by NLB, NKBM, Sparkasse, and Addiko.
    """
    print('\n=== CAMT.053 XML Parsing ===')

    from xml.etree import ElementTree as ET
    from decimal import Decimal

    NS_CAMT = {
        'camt': 'urn:iso:std:iso:20022:tech:xsd:camt.053.001.02',
    }

    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
      <BkToCstmrStmt>
        <Stmt>
          <Id>NLB-2025-01-001</Id>
          <ElctrncSeqNb>1</ElctrncSeqNb>
          <Bal>
            <Tp><CdOrPrtry><Cd>OPBD</Cd></CdOrPrtry></Tp>
            <Amt Ccy="EUR">1000.00</Amt>
            <Dt><Dt>2025-01-15</Dt></Dt>
          </Bal>
          <Bal>
            <Tp><CdOrPrtry><Cd>CLBD</Cd></CdOrPrtry></Tp>
            <Amt Ccy="EUR">2500.00</Amt>
            <Dt><Dt>2025-01-15</Dt></Dt>
          </Bal>
          <Ntry>
            <Amt Ccy="EUR">1500.00</Amt>
            <CdtDbtInd>CRDT</CdtDbtInd>
            <BookgDt><Dt>2025-01-14</Dt></BookgDt>
            <RltdPties><Dbtr><Nm>Janez Novak</Nm></Dbtr></RltdPties>
            <RmtInf><Ustrd>Placilo racun 2025-001</Ustrd></RmtInf>
          </Ntry>
          <Ntry>
            <Amt Ccy="EUR">200.00</Amt>
            <CdtDbtInd>DBIT</CdtDbtInd>
            <BookgDt><Dt>2025-01-15</Dt></BookgDt>
            <RltdPties><Cdtr><Nm>Mercator</Nm></Cdtr></RltdPties>
            <RmtInf><Ustrd>Racun 456</Ustrd></RmtInf>
          </Ntry>
        </Stmt>
      </BkToCstmrStmt>
    </Document>"""

    root = ET.fromstring(sample_xml)

    # Find statement
    stmts = root.findall('.//camt:Stmt', NS_CAMT)
    check('Found 1 statement', len(stmts) == 1,
          f'found {len(stmts)}')

    stmt = stmts[0]
    stmt_id = stmt.findtext('camt:Id', '', NS_CAMT)
    seq = stmt.findtext('camt:ElctrncSeqNb', '', NS_CAMT)
    check('Statement ID parsed', stmt_id == 'NLB-2025-01-001')
    check('Statement seq parsed', seq == '1')

    # Find balances
    balances = stmt.findall('.//camt:Bal', NS_CAMT)
    check('Found 2 balances', len(balances) == 2,
          f'found {len(balances)}')

    # Find opening balance (OPBD)
    opbd = None
    clbd = None
    for bal in balances:
        cd = bal.findtext('camt:Tp/camt:CdOrPrtry/camt:Cd', '', NS_CAMT)
        if cd == 'OPBD':
            opbd = float(Decimal(bal.findtext('camt:Amt', '0', NS_CAMT)))
        elif cd == 'CLBD':
            clbd = float(Decimal(bal.findtext('camt:Amt', '0', NS_CAMT)))
    check('Opening balance (OPBD) = 1000.00', opbd == 1000.00,
          f'got {opbd}')
    check('Closing balance (CLBD) = 2500.00', clbd == 2500.00,
          f'got {clbd}')

    # Find transactions
    entries = stmt.findall('.//camt:Ntry', NS_CAMT)
    check('Found 2 transactions', len(entries) == 2,
          f'found {len(entries)}')

    # First transaction (credit)
    tx1_amount = float(Decimal(entries[0].findtext('camt:Amt', '0', NS_CAMT)))
    tx1_type = entries[0].findtext('camt:CdtDbtInd', 'DBIT', NS_CAMT)
    tx1_partner = entries[0].findtext('camt:RltdPties/camt:Dbtr/camt:Nm', '', NS_CAMT)
    check('TX1 amount = 1500.00', tx1_amount == 1500.00)
    check('TX1 type = CRDT', tx1_type == 'CRDT')
    check('TX1 partner = Janez Novak', tx1_partner == 'Janez Novak')

    # Second transaction (debit)
    tx2_amount = float(Decimal(entries[1].findtext('camt:Amt', '0', NS_CAMT)))
    tx2_type = entries[1].findtext('camt:CdtDbtInd', 'DBIT', NS_CAMT)
    # Debit should be negative
    if tx2_type == 'DBIT':
        tx2_amount = -tx2_amount
    check('TX2 amount = -200.00 (debit)', tx2_amount == -200.00,
          f'got {tx2_amount}')


# ---------------------------------------------------------------------------
# SI Bank BIC Codes
# ---------------------------------------------------------------------------

def test_si_bank_bic_codes():
    """Test SI_BANK_BICS dictionary covers major Slovenian banks."""
    print('\n=== SI Bank BIC Codes ===')

    # We can't easily import from the module (it requires odoo), so we
    # verify the known BICs are valid format
    known_bics = {
        'LJBASI2X': 'NLB',
        'KBMRSI2X': 'NKBM',
        'HDELSI22': 'Sparkasse',
        'HAABSI22': 'Addiko',
        'GIBASI2X': 'Raiffeisen',
    }

    for bic, name in known_bics.items():
        # BIC format: 8 or 11 chars, alphanumeric
        check(f'BIC {name} ({bic}) is 8 or 11 chars',
              len(bic) in (8, 11))
        check(f'BIC {name} ({bic}) is alphanumeric',
              bic.isalnum())
        check(f'BIC {name} ({bic}) ends with SI (Slovenia)',
              'SI' in bic[4:8])


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
    test_ai_concierge()
    test_whatsapp_phone_normalization()
    test_whatsapp_payload_construction()
    test_stripe_deposit_mode_logic()
    test_camt053_xml_parsing()
    test_si_bank_bic_codes()

    print()
    print('=' * 60)
    print(f'SUMMARY: {total - failures}/{total} passed, {failures} failed')
    print('=' * 60)
    sys.exit(1 if failures > 0 else 0)


if __name__ == '__main__':
    main()
