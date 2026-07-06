# -*- coding: utf-8 -*-
"""Tests for Channel Manager API clients (Booking.com + Airbnb).

Tests use mocked HTTP — no real API calls are made.
"""
import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_si_channel_manager.models.channel_clients import (
    BookingComClient,
    AirbnbClient,
    ChannelAuthError,
    ChannelSyncError,
    ChannelValidationError,
    BOOKING_COM_API_ENDPOINT,
    AIRBNB_API_ENDPOINT,
    verify_airbnb_webhook_signature,
    map_booking_com_reservation,
    map_airbnb_reservation,
)


@tagged('post_install', '-at_install')
class TestBookingComClient(TransactionCase):

    def test_endpoint(self):
        self.assertEqual(BookingComClient('u', 'p').endpoint, BOOKING_COM_API_ENDPOINT)

    def test_default_timeout(self):
        self.assertEqual(BookingComClient('u', 'p').timeout, 30)

    def test_api_key_stored(self):
        client = BookingComClient('u', 'p', api_key='key-123')
        self.assertEqual(client.api_key, 'key-123')

    def _mock_resp(self, code, json_data=None, text=''):
        m = MagicMock()
        m.status_code = code
        if json_data is not None:
            m.json.return_value = json_data
            m.text = json.dumps(json_data)
        else:
            m.text = text
        return m

    @patch('odoo.addons.l10n_si_channel_manager.models.channel_clients.requests.request')
    def test_ping_returns_true_on_success(self, mock_req):
        mock_req.return_value = self._mock_resp(200, json_data={})
        self.assertTrue(BookingComClient('u', 'p').ping())

    @patch('odoo.addons.l10n_si_channel_manager.models.channel_clients.requests.request')
    def test_ping_returns_false_on_401(self, mock_req):
        mock_req.return_value = self._mock_resp(401, text='Unauthorized')
        self.assertFalse(BookingComClient('bad', 'creds').ping())

    @patch('odoo.addons.l10n_si_channel_manager.models.channel_clients.requests.request')
    def test_pull_reservations_returns_list(self, mock_req):
        mock_req.return_value = self._mock_resp(200, json_data={
            'data': [{'id': 'r1'}, {'id': 'r2'}]
        })
        reservations = BookingComClient('u', 'p').pull_reservations(datetime.now())
        self.assertEqual(len(reservations), 2)

    @patch('odoo.addons.l10n_si_channel_manager.models.channel_clients.requests.request')
    def test_basic_auth_used(self, mock_req):
        mock_req.return_value = self._mock_resp(200, json_data={'data': []})
        BookingComClient('myuser', 'mypass').pull_reservations(datetime.now())
        call_args = mock_req.call_args
        self.assertEqual(call_args[1]['auth'], ('myuser', 'mypass'))

    @patch('odoo.addons.l10n_si_channel_manager.models.channel_clients.requests.request')
    def test_api_key_in_headers(self, mock_req):
        mock_req.return_value = self._mock_resp(200, json_data={'data': []})
        BookingComClient('u', 'p', api_key='secret').pull_reservations(datetime.now())
        call_args = mock_req.call_args
        self.assertEqual(call_args[1]['headers']['X-Booking-SDK-API-Key'], 'secret')


@tagged('post_install', '-at_install')
class TestAirbnbClient(TransactionCase):

    def test_endpoint(self):
        self.assertEqual(AirbnbClient('t').endpoint, AIRBNB_API_ENDPOINT)

    def test_bearer_token_used(self, mock_req=None):
        client = AirbnbClient('my-token')
        self.assertEqual(client.access_token, 'my-token')


@tagged('post_install', '-at_install')
class TestWebhookSignature(TransactionCase):

    def test_valid_signature(self):
        body = b'{"test": "payload"}'
        secret = 'webhook-secret'
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_airbnb_webhook_signature(body, sig, secret))

    def test_invalid_signature(self):
        self.assertFalse(verify_airbnb_webhook_signature(b'body', 'wrong', 'secret'))

    def test_missing_signature(self):
        self.assertFalse(verify_airbnb_webhook_signature(b'body', '', 'secret'))

    def test_missing_secret(self):
        self.assertFalse(verify_airbnb_webhook_signature(b'body', 'sig', ''))


@tagged('post_install', '-at_install')
class TestReservationMappers(TransactionCase):

    def test_booking_com_mapper(self):
        data = {
            'room_type_id': 'rt-123', 'check_in': '2025-08-01',
            'check_out': '2025-08-05', 'rate': 120.0,
            'adults': 2, 'status': 'confirmed',
        }
        vals = map_booking_com_reservation(data, {'rt-123': 42})
        self.assertEqual(vals['room_id'], 42)
        self.assertEqual(vals['source'], 'booking_com')
        self.assertEqual(vals['state'], 'confirmed')

    def test_booking_com_unmapped_raises(self):
        with self.assertRaises(ChannelValidationError):
            map_booking_com_reservation({'room_type_id': 'unknown'}, {})

    def test_airbnb_mapper(self):
        data = {
            'listing_id': 99999, 'start_date': '2025-09-01',
            'end_date': '2025-09-04', 'listing_price': 90.0,
            'guests': 3, 'status': 'confirmed',
        }
        vals = map_airbnb_reservation(data, {'99999': 15})
        self.assertEqual(vals['room_id'], 15)
        self.assertEqual(vals['source'], 'airbnb')

    def test_airbnb_unmapped_raises(self):
        with self.assertRaises(ChannelValidationError):
            map_airbnb_reservation({'listing_id': 99999}, {})

    def test_airbnb_int_listing_id_matched_as_string(self):
        data = {'listing_id': 12345, 'status': 'confirmed'}
        vals = map_airbnb_reservation(data, {'12345': 99})
        self.assertEqual(vals['room_id'], 99)
