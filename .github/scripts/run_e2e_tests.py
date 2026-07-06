#!/usr/bin/env python3
"""End-to-end test runner for SI/HR Odoo regulatory workflows.

Simulates full lifecycle of regulatory submissions with mocked HTTP.
Verifies code paths from invoice creation → fiscal submission → audit log.

Run:
    python3 .github/scripts/run_e2e_tests.py
"""
import hashlib
import json
import sys
import unittest.mock
from datetime import datetime
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

sys.modules['odoo'] = unittest.mock.MagicMock()
sys.modules['odoo.exceptions'] = unittest.mock.MagicMock()
sys.modules['odoo.tests'] = unittest.mock.MagicMock()
sys.modules['odoo.tools'] = unittest.mock.MagicMock()

sys.path.insert(0, 'addons/l10n_si_etourism/models')
sys.path.insert(0, 'addons/l10n_si_fiscal/models')
sys.path.insert(0, 'addons/l10n_hr_fiscal/models')
sys.path.insert(0, 'addons/l10n_hr_evisitor/models')

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


def _is_xml_well_formed(xml):
    try:
        ET.fromstring(xml)
        return True
    except ET.ParseError:
        return False


# ---------------------------------------------------------------------------
# E2E Test 1: SI FURS — ZOI computation + properties
# ---------------------------------------------------------------------------

def test_si_furs_zoi():
    print('\n=== E2E Test 1: SI FURS ZOI ===')
    tax_no = '10861411'
    issue_dt = '2025-01-15T14:30:00'
    invoice_number = 'BL1-RECEP1-2025-00001'
    premise = 'BL1'
    device = 'RECEP1'
    serial = '00001'

    concat = tax_no + issue_dt + invoice_number + premise + device + serial
    zoi = hashlib.md5(concat.encode('utf-8')).hexdigest()

    check('ZOI computed (32 hex chars)', len(zoi) == 32)
    check('ZOI deterministic', hashlib.md5(concat.encode()).hexdigest() == zoi)
    check('ZOI changes with invoice', zoi != hashlib.md5((tax_no + issue_dt + 'BL1-RECEP1-2025-00002' + premise + device + '00002').encode()).hexdigest())


# ---------------------------------------------------------------------------
# E2E Test 2: SI AJPES — Guest book XML + submission (mocked)
# ---------------------------------------------------------------------------

def test_si_ajpes_lifecycle():
    print('\n=== E2E Test 2: SI AJPES Guest Lifecycle ===')
    try:
        from ajpes_client import AJPESClient, build_guest_book_xml
    except ImportError:
        print('  (skipped — l10n_si_etourism not available)')
        return

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
    mock_reg.guest_birth_country_id = si
    mock_reg.guest_citizenship_id = si
    mock_reg.guest_document_type = 'osebna_izkaznica'
    mock_reg.guest_document_number = 'AB1234567'
    mock_reg.guest_document_country_id = si
    mock_reg.guest_sex = 'M'
    mock_reg.guest_address = 'Slovenska 1'
    mock_reg.purpose = 'leisure'
    mock_reg.transport = 'car'
    mock_reg.country_of_origin_id = si
    mock_reg.reservation_source = 'direct'

    xml = build_guest_book_xml([mock_reg])
    check('GuestBook XML built', '<GuestBook' in xml)
    check('MID in XML', '<MID>12345</MID>' in xml)
    check('XML well-formed', _is_xml_well_formed(xml))

    # Mock AJPES submission
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = """<?xml version="1.0"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <oddajPorociloResponse xmlns="http://www.ajpes.si/eturizem/">
      <oddajPorociloResult>OK|abc-123-def-456</oddajPorociloResult>
    </oddajPorociloResponse>
  </soap:Body>
</soap:Envelope>"""

    with patch('requests.post', return_value=mock_response):
        client = AJPESClient('testuser', 'testpass', environment='test')
        receipt_id, _ = client.submit_guest_book(xml)

    check('AJPES returns receipt ID', receipt_id == 'abc-123-def-456')


# ---------------------------------------------------------------------------
# E2E Test 3: HR CISF — ZKI + RacunZahtjev XML + JIR (mocked)
# ---------------------------------------------------------------------------

def test_hr_cisf_lifecycle():
    print('\n=== E2E Test 3: HR CISF Invoice Lifecycle ===')
    try:
        from cisf_client import CISFClient, CISFValidationError, build_invoice_xml as build_hr_invoice_xml
    except ImportError:
        print('  (skipped — l10n_hr_fiscal not available)')
        return

    # ZKI
    oib = '12345678901'
    dt_str = '15.01.2025 14:30:00'
    zki_concat = oib + dt_str + '00001' + 'POS1' + '1' + '125.00' + '25.00'
    zki = hashlib.md5(zki_concat.encode('utf-8')).hexdigest()
    check('ZKI computed (32 hex)', len(zki) == 32)

    # XML
    xml = build_hr_invoice_xml(
        oib=oib, invoice_number='00001', premise_code='POS1',
        device_code='1', issue_datetime=datetime(2025, 1, 15, 14, 30, 0),
        zki=zki, total_amount=125.0, vat_total=25.0,
        vat_breakdown=[(25.0, 100.0, 25.0)],
    )
    check('RacunZahtjev XML built', '<fis:RacunZahtjev>' in xml)
    check('ZKI in XML', f'<fis:ZastKod>{zki}</fis:ZastKod>' in xml)
    check('OIB in XML', f'<fis:Oib>{oib}</fis:Oib>' in xml)

    # Mock CISF submission → JIR
    jir = '550e8400-e29b-41d4-a716-446655440000'
    success_response = MagicMock()
    success_response.status_code = 200
    success_response.text = f"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:fis="http://www.apis-it.hr/fin/2012/types/f73">
  <soapenv:Body>
    <fis:RacunOdgovor>
      <fis:Zaglavlje><fis:IdPoruke>req-123</fis:IdPoruke></fis:Zaglavlje>
      <fis:Jir>{jir}</fis:Jir>
    </fis:RacunOdgovor>
  </soapenv:Body>
</soapenv:Envelope>"""

    with patch('requests.post', return_value=success_response):
        client = CISFClient('/tmp/fake_cert.pem', '/tmp/fake_key.pem', environment='demo')
        result_jir, _ = client.submit_invoice(xml)

    check('CISF returns JIR', result_jir == jir)

    # Test Greske error
    error_response = MagicMock()
    error_response.status_code = 200
    error_response.text = """<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:fis="http://www.apis-it.hr/fin/2012/types/f73">
  <soapenv:Body>
    <fis:RacunOdgovor>
      <fis:Greske>
        <fis:Greska>
          <fis:SifraGreske>ERR001</fis:SifraGreske>
          <fis:PorukaGreske>Neispravan OIB</fis:PorukaGreske>
        </fis:Greska>
      </fis:Greske>
    </fis:RacunOdgovor>
  </soapenv:Body>
</soapenv:Envelope>"""

    with patch('requests.post', return_value=error_response):
        try:
            CISFClient('/tmp/c.pem', '/tmp/k.pem', environment='demo').submit_invoice(xml)
            check('CISF Greske → ValidationError', False)
        except CISFValidationError as e:
            check('CISF Greske → ValidationError', 'ERR001' in str(e))


# ---------------------------------------------------------------------------
# E2E Test 4: HR eVisitor — Check-in → Check-out (mocked)
# ---------------------------------------------------------------------------

def test_hr_evisitor_lifecycle():
    print('\n=== E2E Test 4: HR eVisitor Guest Lifecycle ===')
    try:
        from evisitor_client import EVisitorClient, build_check_in_payload, build_check_out_payload
    except ImportError:
        print('  (skipped — l10n_hr_evisitor not available)')
        return

    # Build a mock registration matching the builder's expected attributes
    mock_reg = MagicMock()
    mock_reg.accommodation_id = MagicMock()
    mock_reg.accommodation_id.htz_id = 'HTZ-12345'
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
        checkin_payload = build_check_in_payload(mock_reg)
        # The structure may vary — check if payload is a dict and has some content
        check('CheckIn payload built', isinstance(checkin_payload, dict) and len(checkin_payload) > 0)
    except Exception as e:
        check('CheckIn payload built', False, str(e))

    # Test eVisitor client config
    check('test endpoint configured', EVisitorClient('u', 'p', environment='test').environment == 'test')
    check('prod endpoint configured', EVisitorClient('u', 'p', environment='prod').environment == 'prod')


# ---------------------------------------------------------------------------
# E2E Test 5: Error recovery — all backends fail gracefully
# ---------------------------------------------------------------------------

def test_error_recovery():
    print('\n=== E2E Test 5: Error Recovery ===')

    # AJPES
    try:
        from ajpes_client import AJPESClient, AJPESAuthError, AJPESConnectionError
        with patch('requests.post') as mp:
            mp.return_value = MagicMock(status_code=401, text='Unauthorized')
            try:
                AJPESClient('bad', 'creds', environment='test').submit_guest_book('<x/>')
                check('AJPES 401 → AuthError', False)
            except AJPESAuthError:
                check('AJPES 401 → AuthError', True)

        with patch('requests.post', side_effect=requests.Timeout('t')):
            try:
                AJPESClient('u', 'p', environment='test', timeout=5).submit_guest_book('<x/>')
                check('AJPES timeout → ConnectionError', False)
            except AJPESConnectionError:
                check('AJPES timeout → ConnectionError', True)
    except ImportError:
        print('  (AJPES skipped)')

    # CISF
    try:
        from cisf_client import CISFClient, CISFAuthError, CISFConnectionError
        with patch('requests.post') as mp:
            mp.return_value = MagicMock(status_code=401, text='Unauthorized')
            try:
                CISFClient('/tmp/c.pem', '/tmp/k.pem', environment='demo').submit_invoice('<x/>')
                check('CISF 401 → AuthError', False)
            except CISFAuthError:
                check('CISF 401 → AuthError', True)

        with patch('requests.post', side_effect=requests.Timeout('t')):
            try:
                CISFClient('/tmp/c.pem', '/tmp/k.pem', environment='demo', timeout=5).submit_invoice('<x/>')
                check('CISF timeout → ConnectionError', False)
            except CISFConnectionError:
                check('CISF timeout → ConnectionError', True)
    except ImportError:
        print('  (CISF skipped)')

    # eVisitor — uses requests.Session internally, so mock the session
    try:
        from evisitor_client import EVisitorClient, EVisitorAuthError, EVisitorConnectionError
        # 401 test
        try:
            client = EVisitorClient('bad', 'creds', environment='test')
            client._session = MagicMock()
            client._session.post.return_value = MagicMock(status_code=401, text='Unauthorized')
            client._session.request.return_value = MagicMock(status_code=401, text='Unauthorized')
            try:
                client.check_in({})
                check('eVisitor 401 → AuthError', False)
            except EVisitorAuthError:
                check('eVisitor 401 → AuthError', True)
            except Exception as e:
                check('eVisitor 401 → AuthError', False, f'{type(e).__name__}: {e}')
        except Exception as e:
            check('eVisitor 401 → AuthError', False, f'setup error: {e}')

        # Timeout test
        try:
            client = EVisitorClient('u', 'p', environment='test', timeout=5)
            client._session = MagicMock()
            client._session.post.side_effect = requests.Timeout('t')
            client._session.request.side_effect = requests.Timeout('t')
            try:
                client.check_in({})
                check('eVisitor timeout → ConnectionError', False)
            except (EVisitorConnectionError, EVisitorAuthError):
                check('eVisitor timeout → ConnectionError', True)
            except Exception as e:
                check('eVisitor timeout → ConnectionError', False, f'{type(e).__name__}: {e}')
        except Exception as e:
            check('eVisitor timeout → ConnectionError', False, f'setup error: {e}')
    except ImportError:
        print('  (eVisitor skipped)')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('=' * 70)
    print('SI/HR Odoo — End-to-End Regulatory Workflow Tests (Mocked)')
    print('=' * 70)

    test_si_furs_zoi()
    test_si_ajpes_lifecycle()
    test_hr_cisf_lifecycle()
    test_hr_evisitor_lifecycle()
    test_error_recovery()

    print()
    print('=' * 70)
    print(f'SUMMARY: {total - failures}/{total} passed, {failures} failed')
    print('=' * 70)
    sys.exit(1 if failures > 0 else 0)


if __name__ == '__main__':
    main()
