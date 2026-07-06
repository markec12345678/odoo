# -*- coding: utf-8 -*-
"""HTZ eVisitor REST API client (standalone — no Odoo imports).

Integrates with the Croatian National Tourist Board (Hrvatska turistička
zajednica, HTZ) **eVisitor** system for tourist guest registration and
tourist-tax calculation.

Endpoints (REST + JSON):
- PROD: https://www.evisitor.hr/eVisitorRhetos_API/Rest/
- TEST: https://www.evisitor.hr/eVisitorRhetos_API/Rest/_test/

Auth: HTTP Basic Auth (username + password issued by HTZ).

Operations:
- POST /CheckIn         — register a guest (prijava gosta)
- POST /CheckOut        — deregister a guest (odjava gosta)
- GET  /GetTouristTax   — calculate tourist tax for a stay (boravišna pristojba)
- GET  /ListCountries   — list of countries with codes (popis država)
- GET  /Ping            — connectivity test (provjera povezanosti)

Exception model (4 types):
- EVisitorAuthError         — 401 / invalid credentials (no retry)
- EVisitorValidationError   — 400 / business validation (no retry)
- EVisitorConnectionError   — network / 5xx / timeout (retry after 15 min)
- EVisitorUnknownError      — unexpected response (no retry)

References:
- HTZ eVisitor: https://www.evisitor.hr/
- Zakon o boravišnoj pristojbi (UR. l. RH š. 152/08, 59/09, 78/12, 56/16, 25/23)
- Zakon o pružanju usluga u turizmu (UR. l. RH š. 68/13, 85/15, 30/18, 62/20, 32/23)
"""
import json
import logging
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import requests

__all__ = [
    'EVisitorClient',
    'EVisitorError',
    'EVisitorAuthError',
    'EVisitorValidationError',
    'EVisitorConnectionError',
    'EVisitorUnknownError',
    'build_check_in_payload',
    'build_check_out_payload',
    'build_tourist_tax_payload',
    'BASE_URL_PROD',
    'BASE_URL_TEST',
]

_logger = logging.getLogger(__name__)

# Endpoint base URLs
BASE_URL_PROD = 'https://www.evisitor.hr/eVisitorRhetos_API/Rest/'
BASE_URL_TEST = 'https://www.evisitor.hr/eVisitorRhetos_API/Rest/_test/'

# Path suffixes for each operation (relative to the base URL)
PATH_CHECK_IN = 'CheckIn'
PATH_CHECK_OUT = 'CheckOut'
PATH_GET_TOURIST_TAX = 'GetTouristTax'
PATH_LIST_COUNTRIES = 'ListCountries'
PATH_PING = 'Ping'

DEFAULT_TIMEOUT = 30
USER_AGENT = 'Odoo-l10n_hr_evisitor/19.0'

# ISO 3166-1 alpha-2 → numeric (subset relevant for eVisitor country list).
# Used as a fallback when the API country list is unavailable.
_COUNTRY_CODE_FALLBACK = {
    'HR': 191, 'SI': 705, 'AT': 40, 'DE': 276, 'IT': 380,
    'HU': 348, 'RS': 688, 'BA': 70, 'CZ': 203, 'SK': 703,
    'PL': 616, 'FR': 250, 'GB': 826, 'NL': 528, 'BE': 56,
    'ES': 724, 'PT': 620, 'US': 840, 'RU': 643, 'UA': 804,
}


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class EVisitorError(Exception):
    """Base exception for eVisitor client errors."""


class EVisitorAuthError(EVisitorError):
    """Authentication failed — invalid username/password (HTTP 401).

    Recoverable only by reconfiguring credentials. **Never retry** — the
    outcome will not change without user intervention.
    """


class EVisitorValidationError(EVisitorError):
    """eVisitor rejected the payload — business validation error (HTTP 400).

    Example: invalid date range, missing mandatory field, unknown country.
    **Never retry** — the request itself is malformed.
    """


class EVisitorConnectionError(EVisitorError):
    """Network / server-side issue — eVisitor unreachable or 5xx.

    Examples: DNS failure, TCP timeout, HTTP 500/502/503/504.
    **Retry after a delay** — the issue is typically transient.
    """


class EVisitorUnknownError(EVisitorError):
    """Unexpected response from eVisitor — unmapped HTTP status / payload.

    Treat as a programming error or API contract drift. **Never retry**
    blindly — investigate before re-sending.
    """


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class EVisitorClient:
    """Low-level REST client for the HTZ eVisitor API.

    Construct with HTZ-issued credentials and an environment flag
    (``test`` / ``prod``). All methods accept ready-to-send Python payloads
    (use the ``build_*`` helpers to construct them) and return parsed JSON
    dictionaries, raising one of the four eVisitor exceptions on failure.

    The class deliberately avoids any Odoo imports so that it can be unit
    tested in isolation (see ``tests/test_evisitor_client.py``).
    """

    def __init__(
        self,
        username: str,
        password: str,
        environment: str = 'test',
        timeout: int = DEFAULT_TIMEOUT,
        base_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ):
        if not username or not password:
            raise EVisitorAuthError(
                'eVisitor username and password are required.')
        if environment not in ('test', 'prod'):
            raise EVisitorError(
                f"Invalid environment '{environment}' (expected 'test' or 'prod').")
        self.username = username
        self.password = password
        self.environment = environment
        self.timeout = timeout
        self.base_url = base_url or (
            BASE_URL_PROD if environment == 'prod' else BASE_URL_TEST)
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        # Reuse a caller-supplied session (handy for mocking in tests).
        self._session = session or requests.Session()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def ping(self) -> str:
        """Connectivity test — returns the raw response text from /Ping."""
        return self._get_text(PATH_PING)

    def list_countries(self) -> List[Dict[str, Any]]:
        """Fetch the list of supported countries from /ListCountries.

        Returns a list of dicts, each containing at least ``code`` (ISO
        alpha-2) and ``name``. Falls back to a hardcoded subset only if the
        caller explicitly requests it — by default the API response is
        returned verbatim.
        """
        return self._get_json(PATH_LIST_COUNTRIES)

    def check_in(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a CheckIn (guest registration) request.

        Args:
            payload: Dict produced by :func:`build_check_in_payload`.

        Returns:
            Dict with at least ``checkInId`` (the eVisitor submission id).

        Raises:
            EVisitorAuthError, EVisitorValidationError,
            EVisitorConnectionError, EVisitorUnknownError
        """
        return self._post_json(PATH_CHECK_IN, payload)

    def check_out(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a CheckOut (guest deregistration) request.

        Args:
            payload: Dict produced by :func:`build_check_out_payload`.

        Returns:
            Dict confirming deregistration (typically empty or with a
            ``status`` field).

        Raises:
            EVisitorAuthError, EVisitorValidationError,
            EVisitorConnectionError, EVisitorUnknownError
        """
        return self._post_json(PATH_CHECK_OUT, payload)

    def get_tourist_tax(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate tourist tax (boravišna pristojba) via /GetTouristTax.

        Args:
            params: Dict produced by :func:`build_tourist_tax_payload`.

        Returns:
            Dict with the computed tax (e.g. ``totalAmount``,
            ``perPersonBreakdown``).

        Raises:
            EVisitorAuthError, EVisitorValidationError,
            EVisitorConnectionError, EVisitorUnknownError
        """
        return self._get_json(PATH_GET_TOURIST_TAX, params=params)

    # -------------------------------------------------------------------------
    # Internal — HTTP transport
    # -------------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return self.base_url + path

    def _auth(self) -> Tuple[str, str]:
        return (self.username, self.password)

    def _headers(self) -> Dict[str, str]:
        return {
            'Accept': 'application/json',
            'User-Agent': USER_AGENT,
        }

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Perform an HTTP request, mapping transport errors to eVisitor
        exceptions.

        Network timeouts and connection errors raise
        :class:`EVisitorConnectionError`. SSL/cert errors are treated as
        auth errors (a TLS misconfiguration is almost always a deployment
        issue, not a transient one).
        """
        url = self._url(path)
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('auth', self._auth())
        headers = self._headers()
        headers.update(kwargs.pop('headers', {}) or {})
        kwargs['headers'] = headers
        start = time.time()
        try:
            response = self._session.request(method, url, **kwargs)
        except requests.Timeout as exc:
            raise EVisitorConnectionError(
                f'Timeout after {self.timeout}s calling {path}: {exc}') from exc
        except requests.ConnectionError as exc:
            msg = str(exc).lower()
            if 'ssl' in msg or 'certificate' in msg:
                raise EVisitorAuthError(
                    f'TLS/cert error calling {path}: {exc}') from exc
            raise EVisitorConnectionError(
                f'Network error calling {path}: {exc}') from exc
        except requests.RequestException as exc:
            raise EVisitorConnectionError(
                f'Request error calling {path}: {exc}') from exc

        duration_ms = int((time.time() - start) * 1000)
        _logger.info(
            'eVisitor %s %s responded HTTP %d in %dms',
            method, path, response.status_code, duration_ms,
        )
        return response

    def _map_status(self, response: requests.Response, path: str) -> None:
        """Map non-2xx HTTP status codes to eVisitor exceptions.

        Mapping:
        - 401 / 403 → AuthError
        - 400 / 409 / 422 → ValidationError
        - 5xx / 408 → ConnectionError (retryable)
        - everything else → UnknownError
        """
        status = response.status_code
        if 200 <= status < 300:
            return
        body = ''
        try:
            body = response.text[:1000]
        except Exception:  # noqa: BLE001 — body extraction is best-effort
            pass
        if status in (401, 403):
            raise EVisitorAuthError(
                f'Authentication failed (HTTP {status}) calling {path}: {body}')
        if status in (400, 409, 422):
            raise EVisitorValidationError(
                f'Validation error (HTTP {status}) calling {path}: {body}')
        if status == 408 or 500 <= status < 600:
            raise EVisitorConnectionError(
                f'Server error (HTTP {status}) calling {path}: {body}')
        raise EVisitorUnknownError(
            f'Unexpected HTTP {status} calling {path}: {body}')

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST a JSON body and return the parsed JSON response."""
        data = json.dumps(payload, default=_json_default)
        response = self._request(
            'POST', path,
            data=data.encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=utf-8'},
        )
        self._map_status(response, path)
        return _parse_json_response(response, path)

    def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET a JSON response, optionally with query params."""
        response = self._request('GET', path, params=params or {})
        self._map_status(response, path)
        return _parse_json_response(response, path)

    def _get_text(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        """GET a plain-text response (used for /Ping)."""
        response = self._request('GET', path, params=params or {})
        self._map_status(response, path)
        return response.text


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _json_default(obj: Any) -> Any:
    """Fallback JSON serializer for date / datetime objects."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')


def _parse_json_response(response: requests.Response, path: str) -> Any:
    """Parse a JSON response body, raising UnknownError on parse failure."""
    text = response.text or ''
    if not text.strip():
        return {}
    try:
        return response.json()
    except ValueError as exc:
        raise EVisitorUnknownError(
            f'Non-JSON response from {path}: {text[:500]}') from exc


# ---------------------------------------------------------------------------
# Payload builders
# ---------------------------------------------------------------------------

# Allowed values for accommodation type, mirroring the
# ``accommodation_type`` selection on the Odoo model. eVisitor uses
# its own short codes internally.
_ACCOMMODATION_TYPE_CODES = {
    'hotel': 'HOT',
    'apartment': 'APA',
    'room': 'ROOM',
    'camp': 'CAMP',
    'villa': 'VIL',
    'house': 'HAU',
    'boat': 'BOAT',
    'other': 'OTH',
}

# Allowed document types. `` Passport `` / ``ID`` are the most common.
_DOCUMENT_TYPE_CODES = {
    'passport': 'P',
    'id_card': 'I',
    'drivers_license': 'D',
    'other': 'O',
}

# Allowed sex values. eVisitor expects 'M' / 'F' / 'O'.
_SEX_CODES = {
    'male': 'M',
    'female': 'F',
    'other': 'O',
}


def _fmt_date(d: Any) -> Optional[str]:
    """Format a date/datetime/string as ISO ``YYYY-MM-DD``."""
    if not d:
        return None
    if isinstance(d, (datetime, date)):
        return d.strftime('%Y-%m-%d')
    if isinstance(d, str):
        # Accept 'YYYY-MM-DD' or Odoo's default datetime string.
        try:
            return datetime.fromisoformat(d.split(' ')[0]).strftime('%Y-%m-%d')
        except ValueError:
            return d
    return str(d)


def _accommodation_code(accommodation_type: Optional[str]) -> str:
    """Map the Odoo accommodation_type selection to the eVisitor short code."""
    if not accommodation_type:
        return _ACCOMMODATION_TYPE_CODES['other']
    return _ACCOMMODATION_TYPE_CODES.get(
        accommodation_type, _ACCOMMODATION_TYPE_CODES['other'])


def _document_code(document_type: Optional[str]) -> str:
    if not document_type:
        return _DOCUMENT_TYPE_CODES['other']
    return _DOCUMENT_TYPE_CODES.get(
        document_type, _DOCUMENT_TYPE_CODES['other'])


def _sex_code(sex: Optional[str]) -> Optional[str]:
    if not sex:
        return None
    return _SEX_CODES.get(sex, _SEX_CODES['other'])


def build_check_in_payload(registration: Any) -> Dict[str, Any]:
    """Build the JSON payload for a CheckIn (guest registration) request.

    The ``registration`` argument is duck-typed: it can be an Odoo
    ``l10n_hr.evisitor.guest.registration`` recordset or any object exposing
    the same attribute names. This keeps the builder usable both inside Odoo
    and in standalone unit tests.

    Required attributes on ``registration``:
        - accommodation_htz_id      (str)  HTZ accommodation id
        - first_name, last_name     (str)  guest name
        - birth_date                (date) date of birth
        - sex                       (str)  'male' / 'female' / 'other'
        - citizenship_code          (str)  ISO alpha-2 country code
        - document_type             (str)  one of _DOCUMENT_TYPE_CODES keys
        - document_number           (str)  travel document number
        - document_country_code     (str)  issuing country (ISO alpha-2)
        - arrival_date              (date) check-in date
        - departure_date            (date) planned check-out date
        - adults / children / youth (int)  headcount per age group
        - country_of_origin_code    (str)  country of origin (ISO alpha-2)

    Returns a dict ready to be POSTed as JSON to /CheckIn.
    """
    def _get(name, default=None):
        val = getattr(registration, name, default)
        return val if val is not None else default

    accommodation = _get('accommodation_id')
    htz_id = (
        _get('accommodation_htz_id')
        or (getattr(accommodation, 'htz_id', None) if accommodation else None)
    )
    accommodation_type = (
        _get('accommodation_type')
        or (getattr(accommodation, 'accommodation_type', None) if accommodation else None)
    )

    return {
        'accommodation': {
            'htzId': htz_id,
            'type': _accommodation_code(accommodation_type),
        },
        'guest': {
            'firstName': _get('first_name', ''),
            'lastName': _get('last_name', ''),
            'dateOfBirth': _fmt_date(_get('birth_date')),
            'sex': _sex_code(_get('sex')),
            'citizenship': _get('citizenship_code') or _get('citizenship'),
            'document': {
                'type': _document_code(_get('document_type')),
                'number': _get('document_number', ''),
                'issuingCountry': (
                    _get('document_country_code')
                    or _get('document_country')
                ),
            },
            'address': {
                'street': _get('address_street', ''),
                'zip': _get('address_zip', ''),
                'city': _get('address_city', ''),
                'country': _get('address_country_code') or _get('address_country'),
            },
        },
        'stay': {
            'arrivalDate': _fmt_date(_get('arrival_date')),
            'departureDate': _fmt_date(_get('departure_date')),
            'purpose': _get('purpose', 'tourist'),
            'transport': _get('transport', 'other'),
            'countryOfOrigin': _get('country_of_origin_code') or _get('country_of_origin'),
            'reservationSource': _get('reservation_source', 'direct'),
        },
        'occupancy': {
            'adults': int(_get('adults', 1) or 1),
            'children': int(_get('children', 0) or 0),
            'youth': int(_get('youth', 0) or 0),
        },
    }


def build_check_out_payload(registration: Any) -> Dict[str, Any]:
    """Build the JSON payload for a CheckOut (guest deregistration) request.

    Requires the eVisitor ``checkInId`` previously returned by CheckIn,
    accessible via ``registration.evisitor_submission_id``.
    """
    check_in_id = getattr(registration, 'evisitor_submission_id', None)
    if not check_in_id:
        raise EVisitorValidationError(
            'Cannot build CheckOut payload: registration has no '
            'evisitor_submission_id (checkInId) — guest has not been '
            'successfully registered yet.')

    actual_departure = getattr(registration, 'actual_departure_date', None)
    if actual_departure is None:
        actual_departure = getattr(registration, 'departure_date', None)

    return {
        'checkInId': check_in_id,
        'actualDepartureDate': _fmt_date(actual_departure),
    }


def build_tourist_tax_payload(
    htz_id: str,
    nights: int,
    adults: int,
    children: int,
    youth: int,
) -> Dict[str, Any]:
    """Build the query-param dict for a /GetTouristTax request.

    The tourist tax (boravišna pristojba) is calculated per person per night,
    with separate rates for adults, youth (12–17.99) and children (under 12).
    Children under 12 are exempt in most municipalities — the API applies the
    statutory rules.

    Args:
        htz_id:    HTZ accommodation id (str, required)
        nights:    number of nights (int, ≥ 0)
        adults:    number of adult guests (int, ≥ 0)
        children:  number of children under 12 (int, ≥ 0)
        youth:     number of youth aged 12–17.99 (int, ≥ 0)

    Returns a dict of query parameters suitable for ``EVisitorClient.get_tourist_tax``.
    """
    if not htz_id:
        raise EVisitorValidationError(
            'Cannot build tourist-tax payload: htz_id is required.')
    nights_i = int(nights or 0)
    adults_i = int(adults or 0)
    children_i = int(children or 0)
    youth_i = int(youth or 0)
    if nights_i < 0:
        raise EVisitorValidationError(
            f'Cannot build tourist-tax payload: nights must be ≥ 0 (got {nights}).')
    for label, value in (('adults', adults_i),
                         ('children', children_i),
                         ('youth', youth_i)):
        if value < 0:
            raise EVisitorValidationError(
                f'Cannot build tourist-tax payload: {label} must be ≥ 0 '
                f'(got {value}).')

    return {
        'htzId': htz_id,
        'nights': nights_i,
        'adults': adults_i,
        'children': children_i,
        'youth': youth_i,
    }
