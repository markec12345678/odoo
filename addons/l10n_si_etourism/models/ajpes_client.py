# -*- coding: utf-8 -*-
"""AJPES eTurizem SOAP client.

Endpoint: https://www.ajpes.si/wsrno/eTurizem/wsETurizemPorocanje.asmx
Operation: oddajPorocilo(uName, pwd, data, format)

The `data` parameter contains XML payload conforming to AJPES XSD schema
(guestBookSchema for daily reports, GuestBookMRschema for monthly reports).
"""
import logging
import time
from xml.sax.saxutils import escape

import requests

_logger = logging.getLogger(__name__)

ENDPOINT_PRODUCTION = 'https://www.ajpes.si/wsrno/eTurizem/wsETurizemPorocanje.asmx'
ENDPOINT_TEST = 'https://ajpestest.ajpes.si/wsrno/eTurizem/wsETurizemPorocanje.asmx'

DEFAULT_TIMEOUT = 30

SOAP_HEADERS = {
    'Content-Type': 'text/xml; charset=utf-8',
    'SOAPAction': 'http://www.ajpes.si/eturizem/oddajPorocilo',
    'User-Agent': 'Odoo-l10n_si_etourism/19.0',
}

SOAP_ENVELOPE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:etur="http://www.ajpes.si/eturizem/">
  <soapenv:Header/>
  <soapenv:Body>
    <etur:oddajPorocilo>
      <etur:uName>{username}</etur:uName>
      <etur:pwd>{password}</etur:pwd>
      <etur:data>{data_xml}</etur:data>
      <etur:format>1</etur:format>
    </etur:oddajPorocilo>
  </soapenv:Body>
</soapenv:Envelope>"""


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class AJPESClientError(Exception):
    """Base exception for AJPES client errors."""


class AJPESAuthError(AJPESClientError):
    """Authentication failed — invalid credentials."""


class AJPESValidationError(AJPESClientError):
    """AJPES rejected the payload."""


class AJPESConnectionError(AJPESClientError):
    """Network connectivity issue."""


class AJPESUnknownError(AJPESClientError):
    """Unexpected response from AJPES."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class AJPESClient:
    """SOAP client for AJPES eTurizem service."""

    def __init__(self, username, password, environment='test', timeout=DEFAULT_TIMEOUT):
        self.username = username
        self.password = password
        self.environment = environment
        self.timeout = timeout
        self.endpoint = ENDPOINT_PRODUCTION if environment == 'prod' else ENDPOINT_TEST

    def submit_guest_book(self, guest_book_xml):
        """Submit daily guest book report to AJPES."""
        envelope = SOAP_ENVELOPE_TEMPLATE.format(
            username=escape(self.username or ''),
            password=escape(self.password or ''),
            data_xml=escape(guest_book_xml),
        )
        start = time.time()
        try:
            response = requests.post(
                self.endpoint,
                data=envelope.encode('utf-8'),
                headers=SOAP_HEADERS,
                timeout=self.timeout,
                verify=True,
            )
        except requests.Timeout as e:
            raise AJPESConnectionError(f'Timeout: {e}') from e
        except requests.RequestException as e:
            raise AJPESConnectionError(f'Network error: {e}') from e

        duration_ms = int((time.time() - start) * 1000)
        _logger.info('AJPES %s responded %d in %dms', self.endpoint, response.status_code, duration_ms)

        if response.status_code == 401:
            raise AJPESAuthError('Authentication failed')
        if response.status_code >= 500:
            raise AJPESConnectionError(f'AJPES server error {response.status_code}')
        if response.status_code != 200:
            raise AJPESUnknownError(f'Unexpected HTTP {response.status_code}')

        result_text = self._extract_result(response.text)
        return self._parse_result(result_text)

    @staticmethod
    def _extract_result(soap_response_xml):
        """Extract oddajPorociloResult text from SOAP response."""
        import re
        match = re.search(r'<oddajPorociloResult[^>]*>(.*?)</oddajPorociloResult>', soap_response_xml, re.DOTALL)
        if not match:
            fault_match = re.search(r'<faultstring[^>]*>(.*?)</faultstring>', soap_response_xml, re.DOTALL)
            if fault_match:
                raise AJPESUnknownError(f'SOAP fault: {fault_match.group(1).strip()}')
            raise AJPESUnknownError(f'Cannot parse AJPES response: {soap_response_xml[:500]}')
        return match.group(1).strip()

    @staticmethod
    def _parse_result(result_text):
        """Parse the AJPES result text into (receipt_id, raw_text)."""
        if not result_text:
            raise AJPESUnknownError('Empty result from AJPES')
        if result_text.startswith('OK|'):
            return result_text[3:].strip(), result_text
        if result_text.startswith('OK'):
            return '', result_text
        if result_text.startswith('ERR|'):
            parts = result_text.split('|', 2)
            error_code = parts[1] if len(parts) > 1 else 'UNKNOWN'
            error_desc = parts[2] if len(parts) > 2 else result_text
            raise AJPESValidationError(f'AJPES {error_code}: {error_desc}')
        error_indicators = ('napaka', 'neveljaven', 'napačen', 'error', 'invalid', 'failed', 'rejected')
        lower = result_text.lower()
        if any(ind in lower for ind in error_indicators):
            raise AJPESValidationError(f'AJPES validation error: {result_text}')
        if result_text.isdigit():
            return result_text, result_text
        _logger.warning('Unrecognized AJPES result: %s', result_text[:200])
        return '', result_text


# ---------------------------------------------------------------------------
# XML payload builders
# ---------------------------------------------------------------------------

def build_guest_book_xml(registrations):
    """Build the AJPES guest book XML from a list of registration records."""
    lines = ['<?xml version="1.0" encoding="utf-8"?>']
    lines.append('<GuestBook xmlns="http://www.ajpes.si/eturizem/">')
    for reg in registrations:
        lines.append(_build_guest_element(reg))
    lines.append('</GuestBook>')
    return '\n'.join(lines)


def _build_guest_element(reg):
    """Build a single <Guest> XML element from a registration record."""
    est = reg.establishment_id
    arrival_iso = reg.arrival_date.strftime('%Y-%m-%dT%H:%M:%S') if reg.arrival_date else ''
    departure_iso = reg.departure_date.strftime('%Y-%m-%dT%H:%M:%S') if reg.departure_date else ''
    birth_iso = reg.guest_birth_date.isoformat() if reg.guest_birth_date else ''

    def _country_code(country_field):
        if not country_field:
            return ''
        try:
            return country_field.code or ''
        except AttributeError:
            return ''

    return (
        f'  <Guest>\n'
        f'    <MID>{escape(est.mid or "")}</MID>\n'
        f'    <SIFNAS>{escape(est.sifnas or "")}</SIFNAS>\n'
        f'    <ArrivalDate>{arrival_iso}</ArrivalDate>\n'
        f'    <DepartureDate>{departure_iso}</DepartureDate>\n'
        f'    <GuestFirstName>{escape(reg.guest_first_name or "")}</GuestFirstName>\n'
        f'    <GuestLastName>{escape(reg.guest_last_name or "")}</GuestLastName>\n'
        f'    <BirthDate>{birth_iso}</BirthDate>\n'
        f'    <BirthCountry>{escape(_country_code(reg.guest_birth_country_id))}</BirthCountry>\n'
        f'    <Citizenship>{escape(_country_code(reg.guest_citizenship_id))}</Citizenship>\n'
        f'    <DocumentType>{escape(reg.guest_document_type or "")}</DocumentType>\n'
        f'    <DocumentNumber>{escape(reg.guest_document_number or "")}</DocumentNumber>\n'
        f'    <DocumentCountry>{escape(_country_code(reg.guest_document_country_id))}</DocumentCountry>\n'
        f'    <Sex>{escape(reg.guest_sex or "")}</Sex>\n'
        f'    <Address>{escape(reg.guest_address or "")}</Address>\n'
        f'    <Purpose>{escape(reg.purpose or "")}</Purpose>\n'
        f'    <Transport>{escape(reg.transport or "")}</Transport>\n'
        f'    <CountryOfOrigin>{escape(_country_code(reg.country_of_origin_id))}</CountryOfOrigin>\n'
        f'    <ReservationSource>{escape(reg.reservation_source or "")}</ReservationSource>\n'
        f'  </Guest>'
    )


def build_monthly_report_xml(report):
    """Build the AJPES monthly report XML."""
    import json as _json
    est = report.establishment_id
    try:
        by_country = _json.loads(report.by_country_json or '{}')
    except (ValueError, TypeError):
        by_country = {}
    # by_purpose data not yet used in XML generation
    # try:
    #     by_purpose = _json.loads(report.by_purpose_json or '{}')
    # except (ValueError, TypeError):
    #     by_purpose = {}

    lines = ['<?xml version="1.0" encoding="utf-8"?>']
    lines.append('<GuestBookMR xmlns="http://www.ajpes.si/eturizem/">')
    lines.append('  <Header>')
    lines.append(f'    <MID>{escape(est.mid or "")}</MID>')
    lines.append(f'    <SIFNAS>{escape(est.sifnas or "")}</SIFNAS>')
    lines.append(f'    <Year>{report.year}</Year>')
    lines.append(f'    <Month>{report.month:02d}</Month>')
    lines.append(f'    <TotalArrivals>{report.total_arrivals}</TotalArrivals>')
    lines.append(f'    <TotalNights>{report.total_nights}</TotalNights>')
    lines.append('  </Header>')
    lines.append('  <ByCountry>')
    for country_code, count in sorted(by_country.items()):
        lines.append(f'    <Country code="{escape(country_code)}">{count}</Country>')
    lines.append('  </ByCountry>')
    lines.append('</GuestBookMR>')
    return '\n'.join(lines)
