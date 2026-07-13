# -*- coding: utf-8 -*-
"""CISF (Croatian Income Server for Fiscalization) SOAP client.

Endpoints:
- DEMO: https://cistest.apis-it.hr:8449/FiskalizacijaServiceTest
- PROD: https://cis.porezna-uprava.gov.hr:8449/FiskalizacijaService

Auth: Mutual TLS with FINA-issued client certificate (.pfx → PEM).

Operations:
- racuni (RacunZahtjev → RacunOdgovor) — submit invoice, returns JIR
- poslovniProstor (PoslovniProstorZahtjev → PoslovniProstorOdgovor) — register premise
- echo — connectivity test

ZKI Algorithm (per CISF spec v1.8):
    ZKI = MD5(oib + datum_vrijeme + broj_racuna + oznaka_pp + oznaka_nu +
              ukupni_iznos + ukupni_porez)
    Format: 32-char lowercase hex MD5
    Date format: dd.MM.yyyyHH:mm:ss (Croatian)
"""
import logging
import os
import tempfile
import time
import uuid
from datetime import datetime
from typing import Tuple
from xml.sax.saxutils import escape

import requests

_logger = logging.getLogger(__name__)

# CISF endpoints
CISF_DEMO = 'https://cistest.apis-it.hr:8449/FiskalizacijaServiceTest'
CISF_PROD = 'https://cis.porezna-uprava.gov.hr:8449/FiskalizacijaService'

# CISF namespaces
NS_FIS = 'http://www.apis-it.hr/fin/2012/types/f73'
NS_SOAP = 'http://schemas.xmlsoap.org/soap/envelope/'

# SOAP actions
SOAP_ACTION_RACUNI = 'http://e-porezna.porezna-uprava.hr/fiskalizacija/2012/services/FiskalizacijaService/racuni'
SOAP_ACTION_POSLOVNI_PROSTOR = 'http://e-porezna.porezna-uprava.hr/fiskalizacija/2012/services/FiskalizacijaService/poslovniProstor'
SOAP_ACTION_ECHO = 'http://e-porezna.porezna-uprava.hr/fiskalizacija/2012/services/FiskalizacijaService/echo'

DEFAULT_TIMEOUT = 30


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CISFClientError(Exception):
    """Base exception for CISF client errors."""


class CISFAuthError(CISFClientError):
    """Authentication failed — invalid FINA certificate."""


class CISFValidationError(CISFClientError):
    """CISF rejected the payload — business validation error (Greske)."""


class CISFConnectionError(CISFClientError):
    """Network connectivity issue — CISF unreachable."""


class CISFUnknownError(CISFClientError):
    """Unexpected response from CISF."""


# ---------------------------------------------------------------------------
# SOAP envelope template
# ---------------------------------------------------------------------------

SOAP_ENVELOPE_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="{soap_ns}" xmlns:fis="{fis_ns}">
  <soapenv:Body>
{body}
  </soapenv:Body>
</soapenv:Envelope>"""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class CISFClient:
    """Low-level SOAP client for Croatian CISF fiscalization service.

    Requires a FINA-issued client certificate for mTLS authentication.
    The .pfx file must be split into PEM cert + key by the caller.
    """

    def __init__(
        self,
        cert_pem_path: str,
        key_pem_path: str,
        environment: str = 'demo',
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.cert_pem_path = cert_pem_path
        self.key_pem_path = key_pem_path
        self.environment = environment
        self.timeout = timeout
        self.endpoint = CISF_PROD if environment == 'prod' else CISF_DEMO

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def submit_invoice(self, invoice_xml: str) -> Tuple[str, str]:
        """Submit a RacunZahtjev (invoice) to CISF.

        Args:
            invoice_xml: The `<fis:RacunZahtjev>...</fis:RacunZahtjev>` body XML.

        Returns:
            tuple: (jir, raw_response_text)

        Raises:
            CISFAuthError, CISFValidationError, CISFConnectionError, CISFUnknownError
        """
        return self._call_cisf(SOAP_ACTION_RACUNI, invoice_xml, expect='Jir')

    def register_premise(self, premise_xml: str) -> Tuple[str, str]:
        """Submit a PoslovniProstorZahtjev (premise registration) to CISF."""
        return self._call_cisf(SOAP_ACTION_POSLOVNI_PROSTOR, premise_xml, expect=None)

    def echo(self, message: str = 'echoRequest') -> str:
        """Test connectivity to CISF."""
        import re
        body = f'    <fis:EchoRequest>{escape(message)}</fis:EchoRequest>'
        envelope = SOAP_ENVELOPE_TEMPLATE.format(
            soap_ns=NS_SOAP, fis_ns=NS_FIS, body=body,
        )
        response = self._post(envelope, SOAP_ACTION_ECHO)
        match = re.search(r'<EchoResponse[^>]*>(.*?)</EchoResponse>', response, re.DOTALL)
        return match.group(1).strip() if match else response

    # -------------------------------------------------------------------------
    # Internal — HTTP call
    # -------------------------------------------------------------------------

    def _call_cisf(self, soap_action, body_xml, expect=None):
        """Make a SOAP call to CISF."""
        envelope = SOAP_ENVELOPE_TEMPLATE.format(
            soap_ns=NS_SOAP, fis_ns=NS_FIS, body=body_xml,
        )
        raw_response = self._post(envelope, soap_action)
        self._check_for_fault(raw_response)
        self._check_for_errors(raw_response)
        if expect:
            extracted = self._extract_element(raw_response, expect)
            return extracted, raw_response
        return '', raw_response

    def _post(self, envelope, soap_action):
        """Send SOAP envelope to CISF endpoint."""
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': soap_action,
            'User-Agent': 'Odoo-l10n_hr_fiscal/19.0',
        }
        start = time.time()
        try:
            response = requests.post(
                self.endpoint,
                data=envelope.encode('utf-8'),
                headers=headers,
                timeout=self.timeout,
                cert=(self.cert_pem_path, self.key_pem_path),
                verify=True,
            )
        except requests.Timeout as e:
            raise CISFConnectionError(f'Timeout after {self.timeout}s: {e}') from e
        except requests.RequestException as e:
            msg = str(e).lower()
            if 'ssl' in msg or 'certificate' in msg:
                raise CISFAuthError(f'TLS/cert error: {e}') from e
            raise CISFConnectionError(f'Network error: {e}') from e

        duration_ms = int((time.time() - start) * 1000)
        _logger.info('CISF %s responded %d in %dms', self.endpoint, response.status_code, duration_ms)

        if response.status_code == 401:
            raise CISFAuthError('Authentication failed — check FINA certificate')
        if response.status_code >= 500:
            raise CISFConnectionError(f'CISF server error {response.status_code}: {response.text[:500]}')
        if response.status_code != 200:
            raise CISFUnknownError(f'Unexpected HTTP {response.status_code}: {response.text[:500]}')
        return response.text

    # -------------------------------------------------------------------------
    # Response parsing
    # -------------------------------------------------------------------------

    @staticmethod
    def _check_for_fault(soap_response):
        """Check for SOAP Fault. Raises CISFUnknownError if found."""
        import re
        fault_match = re.search(r'<faultstring[^>]*>(.*?)</faultstring>', soap_response, re.DOTALL)
        if fault_match:
            raise CISFUnknownError(f'SOAP fault: {fault_match.group(1).strip()}')

    @staticmethod
    def _check_for_errors(soap_response):
        """Check for CISF <Greske> element. Raises CISFValidationError if found."""
        import re
        greske_match = re.search(
            r'<[a-zA-Z0-9_]*:?Greske[^>]*>(.*?)</[a-zA-Z0-9_]*:?Greske>',
            soap_response, re.DOTALL,
        )
        if not greske_match:
            return
        errors = []
        for greska_match in re.finditer(
            r'<[a-zA-Z0-9_]*:?Greska[^>]*>.*?<[a-zA-Z0-9_]*:?SifraGreske[^>]*>(.*?)</[a-zA-Z0-9_]*:?SifraGreske>.*?<[a-zA-Z0-9_]*:?PorukaGreske[^>]*>(.*?)</[a-zA-Z0-9_]*:?PorukaGreske>.*?</[a-zA-Z0-9_]*:?Greska>',
            greske_match.group(1), re.DOTALL,
        ):
            code = greska_match.group(1).strip()
            message = greska_match.group(2).strip()
            errors.append(f'{code}: {message}')
        if errors:
            raise CISFValidationError('CISF errors: ' + ' | '.join(errors))

    @staticmethod
    def _extract_element(soap_response, element_name):
        """Extract text content of an element (handles namespace prefix)."""
        import re
        pattern = rf'<[a-zA-Z0-9_]*:?{element_name}\b[^>]*>(.*?)</[a-zA-Z0-9_]*:?{element_name}>'
        match = re.search(pattern, soap_response, re.DOTALL)
        if not match:
            raise CISFUnknownError(f'Cannot find <{element_name}> in CISF response: {soap_response[:500]}')
        return match.group(1).strip()


# ---------------------------------------------------------------------------
# PFX helpers
# ---------------------------------------------------------------------------

def extract_pfx_to_pem(pfx_path, pfx_password, output_dir=None):
    """Extract certificate and private key from FINA .pfx file.

    Uses `cryptography` library if available, otherwise falls back to openssl CLI.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix='cisf_pfx_')
    cert_path = os.path.join(output_dir, 'cert.pem')
    key_path = os.path.join(output_dir, 'key.pem')

    try:
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, NoEncryption, PrivateFormat
        with open(pfx_path, 'rb') as f:
            pfx_data = f.read()
        private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
            pfx_data, pfx_password.encode() if pfx_password else None,
        )
        if not private_key or not cert:
            raise CISFClientError('Could not extract key/cert from PFX')
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(Encoding.PEM))
            for ac in additional_certs:
                f.write(ac.public_bytes(Encoding.PEM))
        with open(key_path, 'wb') as f:
            f.write(private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()))
        return cert_path, key_path
    except ImportError:
        pass

    import subprocess
    try:
        subprocess.run(['openssl', 'pkcs12', '-in', pfx_path, '-out', cert_path,
                        '-clcerts', '-nokeys', '-passin', f'pass:{pfx_password}'],
                       check=True, capture_output=True)
        subprocess.run(['openssl', 'pkcs12', '-in', pfx_path, '-out', key_path,
                        '-nocerts', '-nodes', '-passin', f'pass:{pfx_password}'],
                       check=True, capture_output=True)
        return cert_path, key_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise CISFClientError(f'Cannot extract PFX: {e}') from e


# ---------------------------------------------------------------------------
# XML payload builders
# ---------------------------------------------------------------------------

def _format_hr_datetime(dt):
    """Format datetime per CISF spec: 'dd.MM.yyyyHH:mm:ss'."""
    return dt.strftime('%d.%m.%Y%H:%M:%S')


def build_invoice_xml(oib, invoice_number, premise_code, device_code,
                      issue_datetime, zki, total_amount, vat_total,
                      vat_breakdown, payment_method='G',
                      in_vat_system=True, sequence_type='P'):
    """Build the RacunZahtjev XML body."""
    message_id = str(uuid.uuid4())
    issue_dt_str = _format_hr_datetime(issue_datetime)

    tax_rows = []
    for rate, base, tax_amount in vat_breakdown:
        tax_rows.append(
            f'        <fis:Pdv>\n'
            f'          <fis:Stopa>{rate:.2f}</fis:Stopa>\n'
            f'          <fis:Osnovica>{base:.2f}</fis:Osnovica>\n'
            f'          <fis:Pdv>{tax_amount:.2f}</fis:Pdv>\n'
            f'        </fis:Pdv>'
        )
    pdv_section = '\n'.join(tax_rows) if tax_rows else ''

    return f"""    <fis:RacunZahtjev>
      <fis:Zaglavlje>
        <fis:IdPoruke>{message_id}</fis:IdPoruke>
        <fis:DatumVrijeme>{_format_hr_datetime(datetime.now())}</fis:DatumVrijeme>
      </fis:Zaglavlje>
      <fis:Racun>
        <fis:Oib>{escape(oib)}</fis:Oib>
        <fis:USustPdv>{"true" if in_vat_system else "false"}</fis:USustPdv>
        <fis:DatVrijeme>{issue_dt_str}</fis:DatVrijeme>
        <fis:OznSlijed>{sequence_type}</fis:OznSlijed>
        <fis:BrojRacuna>
          <fis:BrOznRac>{escape(invoice_number)}</fis:BrOznRac>
          <fis:OznPosPr>{escape(premise_code)}</fis:OznPosPr>
          <fis:OznNapUr>{escape(device_code)}</fis:OznNapUr>
        </fis:BrojRacuna>
        <fis:IznosUkupno>{total_amount:.2f}</fis:IznosUkupno>
        <fis:IznosPdv>{vat_total:.2f}</fis:IznosPdv>
{pdv_section}
        <fis:ZastKod>{zki}</fis:ZastKod>
        <fis:NacinPlac>{payment_method}</fis:NacinPlac>
      </fis:Racun>
    </fis:RacunZahtjev>"""


def build_premise_xml(oib, premise_code, address, working_hours,
                      premise_type='permanentni', note=''):
    """Build the PoslovniProstorZahtjev XML body."""
    message_id = str(uuid.uuid4())
    wh_xml_parts = []
    day_map = {
        'mon': 'Ponedjeljak', 'tue': 'Utorak', 'wed': 'Srijeda',
        'thu': 'Cetvrtak', 'fri': 'Petak', 'sat': 'Subota', 'sun': 'Nedjelja',
    }
    for day_key, day_name in day_map.items():
        if day_key in working_hours:
            start, end = working_hours[day_key]
            wh_xml_parts.append(
                f'          <fis:{day_name}><fis:Pocetak>{start}</fis:Pocetak><fis:Kraj>{end}</fis:Kraj></fis:{day_name}>'
            )
    wh_xml = '\n'.join(wh_xml_parts)

    return f"""    <fis:PoslovniProstorZahtjev>
      <fis:Zaglavlje>
        <fis:IdPoruke>{message_id}</fis:IdPoruke>
        <fis:DatumVrijeme>{_format_hr_datetime(datetime.now())}</fis:DatumVrijeme>
      </fis:Zaglavlje>
      <fis:PoslovniProstor>
        <fis:Oib>{escape(oib)}</fis:Oib>
        <fis:OznPoslProstora>{escape(premise_code)}</fis:OznPoslProstora>
        <fis:AdresniPodatak>
          <fis:Adresa>
            <fis:Ulica>{escape(address.get('street', ''))}</fis:Ulica>
            <fis:KucniBroj>{escape(address.get('house_number', ''))}</fis:KucniBroj>
            <fis:KucniBrojDodatak>{escape(address.get('house_suffix', ''))}</fis:KucniBrojDodatak>
            <fis:PostanskiBroj>{escape(address.get('zip', ''))}</fis:PostanskiBroj>
            <fis:Naselje>{escape(address.get('city', ''))}</fis:Naselje>
            <fis:Općina>{escape(address.get('municipality', ''))}</fis:Općina>
          </fis:Adresa>
        </fis:AdresniPodatak>
        <fis:RadnoVrijeme>
{wh_xml}
        </fis:RadnoVrijeme>
        <fis:TipPoslovnogProstora>{premise_type}</fis:TipPoslovnogProstora>
        <fis:OstaliTipoviPP>{escape(note)}</fis:OstaliTipoviPP>
      </fis:PoslovniProstor>
    </fis:PoslovniProstorZahtjev>"""
