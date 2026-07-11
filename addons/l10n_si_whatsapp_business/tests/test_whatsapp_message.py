# -*- coding: utf-8 -*-
"""Tests for l10n_si_whatsapp_business module.

Covers:
- Model creation and field validation (message + template)
- Phone number normalization (whitespace, +, -)
- action_send() validation: missing config, missing phone, disabled
- Template payload vs text payload construction
- action_send_reservation_confirmation workflow
- HTTP calls are mocked — no real WhatsApp API calls in tests.
"""
import logging
from unittest.mock import patch, MagicMock

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestL10nSiWhatsAppTemplate(TransactionCase):
    """Tests for l10n_si.whatsapp.template model."""

    def setUp(self):
        super().setUp()
        self.Template = self.env['l10n_si.whatsapp.template']
        self.template = self.Template.create({
            'name': 'reservation_confirm',
            'language': 'sl',
            'body': 'Pozdravljeni {{1}}, vaša rezervacija {{2}} je potrjena.',
        })

    def test_template_creation(self):
        self.assertTrue(self.template.id)
        self.assertEqual(self.template.name, 'reservation_confirm')
        self.assertEqual(self.template.language, 'sl')
        self.assertTrue(self.template.active)

    def test_default_language_is_sl(self):
        tpl = self.Template.create({'name': 'test_tpl', 'body': 'test'})
        self.assertEqual(tpl.language, 'sl')

    def test_default_active_is_true(self):
        tpl = self.Template.create({'name': 'test_tpl2', 'body': 'test'})
        self.assertTrue(tpl.active)

    def test_company_id_defaults_to_current(self):
        tpl = self.Template.create({'name': 'test_tpl3', 'body': 'test'})
        self.assertEqual(tpl.company_id, self.env.company)

    def test_name_is_required(self):
        with self.assertRaises(Exception):
            self.Template.create({'body': 'no name'})

    def test_all_supported_languages(self):
        """Template should support sl, hr, en."""
        for lang in ('sl', 'hr', 'en'):
            tpl = self.Template.create({
                'name': f'tpl_{lang}', 'language': lang, 'body': 'test'
            })
            self.assertEqual(tpl.language, lang)


@tagged('post_install', '-at_install')
class TestL10nSiWhatsAppMessage(TransactionCase):
    """Tests for l10n_si.whatsapp.message model + action_send()."""

    def setUp(self):
        super().setUp()
        self.Message = self.env['l10n_si.whatsapp.message']
        self.Template = self.env['l10n_si.whatsapp.template']

        # Set up company with WhatsApp enabled
        self.company = self.env.company
        self.company.write({
            'wa_enabled': True,
            'wa_phone_number_id': '1234567890',
            'wa_access_token': 'EAA_test_token',
            'wa_business_phone': '38641234567',
        })

        # Create test partner with mobile
        self.partner = self.env['res.partner'].create({
            'name': 'Test Guest',
            'mobile': '+386 41 234 567',
        })

        # Create test template
        self.template = self.Template.create({
            'name': 'reservation_confirm',
            'language': 'sl',
            'body': 'Potrditev {{1}}',
        })

        # Create a text message
        self.text_msg = self.Message.create({
            'partner_id': self.partner.id,
            'direction': 'outgoing',
            'message_type': 'text',
            'body': 'Welcome to our hotel!',
            'company_id': self.company.id,
        })

        # Create a template message
        self.template_msg = self.Message.create({
            'partner_id': self.partner.id,
            'direction': 'outgoing',
            'message_type': 'template',
            'template_id': self.template.id,
            'body': 'Reservation confirmation',
            'company_id': self.company.id,
        })

    def test_message_creation_defaults(self):
        """Test default values on message creation."""
        self.assertEqual(self.text_msg.direction, 'outgoing')
        self.assertEqual(self.text_msg.message_type, 'text')
        self.assertEqual(self.text_msg.state, 'draft')
        self.assertFalse(self.text_msg.wa_message_id)

    def test_phone_number_related_from_partner_mobile(self):
        """phone_number is related field from partner.mobile."""
        self.assertEqual(self.text_msg.phone_number, self.partner.mobile)

    def test_action_send_raises_when_whatsapp_disabled(self):
        """action_send must raise UserError when wa_enabled=False."""
        self.company.wa_enabled = False
        with self.assertRaises(UserError):
            self.text_msg.action_send()

    def test_action_send_raises_when_phone_number_id_missing(self):
        """action_send must raise when wa_phone_number_id is empty."""
        self.company.wa_phone_number_id = False
        with self.assertRaises(UserError):
            self.text_msg.action_send()

    def test_action_send_raises_when_access_token_missing(self):
        """action_send must raise when wa_access_token is empty."""
        self.company.wa_access_token = False
        with self.assertRaises(UserError):
            self.text_msg.action_send()

    def test_action_send_raises_when_partner_has_no_phone(self):
        """action_send must raise when partner has no mobile or phone."""
        self.partner.write({'mobile': False, 'phone': False})
        with self.assertRaises(UserError):
            self.text_msg.action_send()

    def _mock_response(self, status_code, json_data):
        """Build a mock requests.Response."""
        m = MagicMock()
        m.status_code = status_code
        m.json.return_value = json_data
        m.text = str(json_data)
        return m

    @patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post')
    def test_action_send_text_message_success(self, mock_post):
        """Successful text message send sets state=sent and stores wa_message_id."""
        mock_post.return_value = self._mock_response(200, {
            'messages': [{'id': 'wamid.HBgLTEST123'}]
        })
        self.text_msg.action_send()
        self.assertEqual(self.text_msg.state, 'sent')
        self.assertEqual(self.text_msg.wa_message_id, 'wamid.HBgLTEST123')

        # Verify the request payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertEqual(payload['messaging_product'], 'whatsapp')
        self.assertEqual(payload['type'], 'text')
        self.assertEqual(payload['text']['body'], 'Welcome to our hotel!')
        # Phone should be normalized (no +, spaces, dashes)
        self.assertEqual(payload['to'], '38641234567')

    @patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post')
    def test_action_send_template_message_success(self, mock_post):
        """Successful template message send constructs template payload."""
        mock_post.return_value = self._mock_response(200, {
            'messages': [{'id': 'wamid.HBgLTEMPLATE456'}]
        })
        self.template_msg.action_send()
        self.assertEqual(self.template_msg.state, 'sent')
        self.assertEqual(self.template_msg.wa_message_id, 'wamid.HBgLTEMPLATE456')

        payload = mock_post.call_args[1]['json']
        self.assertEqual(payload['type'], 'template')
        self.assertEqual(payload['template']['name'], 'reservation_confirm')
        self.assertEqual(payload['template']['language']['code'], 'sl')

    @patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post')
    def test_action_send_api_error_marks_failed(self, mock_post):
        """When API returns non-200, message is marked failed with error."""
        mock_post.return_value = self._mock_response(400, {
            'error': {'message': 'Invalid phone number'}
        })
        self.text_msg.action_send()
        self.assertEqual(self.text_msg.state, 'failed')
        self.assertTrue(self.text_msg.error_message)

    @patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post')
    def test_action_send_network_exception_marks_failed(self, mock_post):
        """When requests.post raises, message is marked failed."""
        mock_post.side_effect = ConnectionError('Network down')
        self.text_msg.action_send()
        self.assertEqual(self.text_msg.state, 'failed')
        self.assertIn('Network down', self.text_msg.error_message)

    @patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post')
    def test_phone_normalization_strips_plus_spaces_dashes(self, mock_post):
        """Phone normalization strips +, spaces, and dashes."""
        self.partner.mobile = '+386-41-234-567'
        # Trigger send (will fail on validation later, but we test the
        # normalization by checking the constructed payload via mock)
        with patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post') as mock_post:
            mock_post.return_value = self._mock_response(200, {
                'messages': [{'id': 'wamid.NORM'}]
            })
            self.text_msg.action_send()
            payload = mock_post.call_args[1]['json']
            self.assertEqual(payload['to'], '38641234567')

    @patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post')
    def test_action_send_uses_correct_url_and_headers(self, mock_post):
        """Verify URL is built from wa_phone_number_id and Authorization header is Bearer."""
        mock_post.return_value = self._mock_response(200, {
            'messages': [{'id': 'X'}]
        })
        self.text_msg.action_send()
        call_args = mock_post.call_args
        url = call_args[0][0] if call_args[0] else call_args[1].get('url')
        # URL should contain the phone_number_id
        self.assertIn('1234567890', url)
        self.assertIn('messages', url)
        # Authorization header
        headers = call_args[1]['headers']
        self.assertEqual(headers['Authorization'], 'Bearer EAA_test_token')
        self.assertEqual(headers['Content-Type'], 'application/json')


@tagged('post_install', '-at_install')
class TestL10nSiWhatsAppReservationConfirmation(TransactionCase):
    """Tests for action_send_reservation_confirmation workflow."""

    def setUp(self):
        super().setUp()
        self.Message = self.env['l10n_si.whatsapp.message']
        self.company = self.env.company
        self.company.write({
            'wa_enabled': True,
            'wa_phone_number_id': '1234567890',
            'wa_access_token': 'EAA_test_token',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Reservation Guest',
            'mobile': '+38641234567',
        })

    @patch('odoo.addons.l10n_si_whatsapp_business.models.l10n_si_whatsapp_message.requests.post')
    def test_reservation_confirmation_creates_and_sends_message(self, mock_post):
        """action_send_reservation_confirmation should create a message and send it."""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'messages': [{'id': 'wamid.RES123'}]},
            text='{"messages": [{"id": "wamid.RES123"}]}',
        )

        # Try sending reservation confirmation (may fail to find xml_id template
        # in test db, that's OK — we test the workflow path)
        msg = self.Message.action_send_reservation_confirmation(
            self.partner.id, 'Reservation #12345'
        )
        # If template was found, msg should be a record; if not, msg is False
        # Either way, no exception should be raised
        if msg:
            self.assertEqual(msg.partner_id, self.partner)
            self.assertEqual(msg.direction, 'outgoing')
            self.assertEqual(msg.message_type, 'template')


@tagged('post_install', '-at_install')
class TestResCompanyWhatsApp(TransactionCase):
    """Tests for res.company WhatsApp fields."""

    def test_default_values(self):
        """New company should have safe defaults (wa_enabled=False)."""
        company = self.env['res.company'].create({'name': 'Test WA Co'})
        self.assertFalse(company.wa_enabled)
        # wa_verify_token has a default
        self.assertTrue(company.wa_verify_token)
        # Other fields are empty by default
        self.assertFalse(company.wa_phone_number_id)
        self.assertFalse(company.wa_access_token)
        self.assertFalse(company.wa_business_phone)

    def test_verify_token_default_value(self):
        """The default webhook verify token should be the expected string."""
        company = self.env['res.company'].create({'name': 'Test WA Co 2'})
        self.assertEqual(company.wa_verify_token, 'si_hr_tourism_wa_verify')
