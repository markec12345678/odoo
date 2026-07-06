# -*- coding: utf-8 -*-
"""Channel Manager API clients — Booking.com + Airbnb."""
import hashlib
import hmac
import json
import logging
import time
from typing import Optional, Tuple

import requests

_logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT = 30
WEBHOOK_VERIFY_TOLERANCE = 300
BOOKING_COM_API_ENDPOINT = 'https://supply-xml.booking.com/2.0/json'
AIRBNB_API_ENDPOINT = 'https://api.airbnb.com/v2'


class ChannelError(Exception): pass
class ChannelAuthError(ChannelError): pass
class ChannelSyncError(ChannelError): pass
class ChannelValidationError(ChannelError): pass


class BookingComClient:
    def __init__(self, username, password, api_key=None, hotel_id=None, timeout=DEFAULT_TIMEOUT):
        self.username = username; self.password = password; self.api_key = api_key
        self.hotel_id = hotel_id; self.timeout = timeout; self.endpoint = BOOKING_COM_API_ENDPOINT

    def _get_headers(self):
        headers = {'Accept': 'application/json', 'User-Agent': 'Odoo-l10n_si_channel_manager/19.0'}
        if self.api_key: headers['X-Booking-SDK-API-Key'] = self.api_key
        return headers

    def _call(self, method, path, payload=None):
        url = f'{self.endpoint}/{path.lstrip("/")}'
        try:
            response = requests.request(method, url, auth=(self.username, self.password),
                                        headers=self._get_headers(), json=payload, timeout=self.timeout)
        except requests.Timeout as e: raise ChannelSyncError(f'Timeout: {e}') from e
        except requests.RequestException as e: raise ChannelSyncError(f'Network error: {e}') from e
        if response.status_code == 401: raise ChannelAuthError('Invalid Booking.com credentials')
        if response.status_code == 400: raise ChannelValidationError(f'Booking.com: {response.text[:300]}')
        if response.status_code >= 500: raise ChannelSyncError(f'Booking.com server error {response.status_code}')
        if response.status_code != 200: raise ChannelSyncError(f'Unexpected HTTP {response.status_code}')
        try: return response.json()
        except ValueError as e: raise ChannelSyncError(f'Invalid JSON: {e}') from e

    def push_availability(self, room_type_id, dates): return self._call('PUT', 'availability', {'hotel_id': self.hotel_id, 'room_type_id': room_type_id, 'availability': dates})
    def push_rates(self, room_type_id, rates): return self._call('PUT', 'rates', {'hotel_id': self.hotel_id, 'room_type_id': room_type_id, 'rates': rates})
    def pull_reservations(self, since):
        response = self._call('GET', 'reservations', {'hotel_id': self.hotel_id, 'modified_since': since.strftime('%Y-%m-%dT%H:%M:%S')})
        return response.get('data', []) if isinstance(response, dict) else []
    def ping(self):
        try: self._call('GET', 'hotels'); return True
        except (ChannelAuthError, ChannelSyncError): return False


class AirbnbClient:
    def __init__(self, access_token, listing_id=None, timeout=DEFAULT_TIMEOUT):
        self.access_token = access_token; self.listing_id = listing_id
        self.timeout = timeout; self.endpoint = AIRBNB_API_ENDPOINT

    def _get_headers(self):
        return {'Authorization': f'Bearer {self.access_token}', 'Accept': 'application/json',
                'User-Agent': 'Odoo-l10n_si_channel_manager/19.0'}

    def _call(self, method, path, payload=None):
        url = f'{self.endpoint}/{path.lstrip("/")}'
        try:
            response = requests.request(method, url, headers=self._get_headers(), json=payload, timeout=self.timeout)
        except requests.Timeout as e: raise ChannelSyncError(f'Timeout: {e}') from e
        except requests.RequestException as e: raise ChannelSyncError(f'Network error: {e}') from e
        if response.status_code == 401: raise ChannelAuthError('Invalid Airbnb token')
        if response.status_code == 400: raise ChannelValidationError(f'Airbnb: {response.text[:300]}')
        if response.status_code >= 500: raise ChannelSyncError(f'Airbnb server error {response.status_code}')
        if response.status_code != 200: raise ChannelSyncError(f'Unexpected HTTP {response.status_code}')
        try: return response.json()
        except ValueError as e: raise ChannelSyncError(f'Invalid JSON: {e}') from e

    def push_calendar(self, listing_id, dates): return self._call('PUT', 'calendars', {'listing_id': listing_id, 'calendar': dates})
    def pull_reservations(self, since):
        response = self._call('GET', 'reservations', {'_limit': 100, '_offset': 0, 'modified_since': since.strftime('%Y-%m-%dT%H:%M:%S')})
        return response.get('reservations', []) if isinstance(response, dict) else []
    def ping(self):
        try: self._call('GET', 'me'); return True
        except (ChannelAuthError, ChannelSyncError): return False


def verify_airbnb_webhook_signature(payload_body, signature_header, secret, tolerance=WEBHOOK_VERIFY_TOLERANCE):
    if not signature_header or not secret: return False
    expected = hmac.new(secret.encode('utf-8'), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def map_booking_com_reservation(booking_data, mapping):
    room_id = mapping.get(booking_data.get('room_type_id'))
    if not room_id: raise ChannelValidationError(f'No Odoo room mapping for room_type_id {booking_data.get("room_type_id")}')
    return {'partner_id': False, 'room_id': room_id, 'check_in': booking_data.get('check_in'),
            'check_out': booking_data.get('check_out'), 'daily_rate': float(booking_data.get('rate', 0)),
            'adults': int(booking_data.get('adults', 2)), 'children': int(booking_data.get('children', 0)),
            'source': 'booking_com', 'special_requests': booking_data.get('guest_remarks', ''),
            'state': 'confirmed' if booking_data.get('status') == 'confirmed' else 'draft'}


def map_airbnb_reservation(airbnb_data, mapping):
    room_id = mapping.get(str(airbnb_data.get('listing_id')))
    if not room_id: raise ChannelValidationError(f'No Odoo room mapping for listing_id {airbnb_data.get("listing_id")}')
    return {'partner_id': False, 'room_id': room_id, 'check_in': airbnb_data.get('start_date'),
            'check_out': airbnb_data.get('end_date'), 'daily_rate': float(airbnb_data.get('listing_price', 0) or 0),
            'adults': int(airbnb_data.get('guests', 2)), 'children': 0, 'source': 'airbnb',
            'special_requests': airbnb_data.get('guest_message', ''),
            'state': 'confirmed' if airbnb_data.get('status') == 'confirmed' else 'draft'}
