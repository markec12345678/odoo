# -*- coding: utf-8 -*-
"""Tests for l10n_si_stripe_payment module.

Covers:
- res.company fields: si_stripe_deposit_mode, si_stripe_deposit_percentage
- Default values (deposit_mode=False, percentage=30.0)
- payment.provider inherit: _stripe_make_payment_request override behavior
  (when SI deposit mode is enabled, capture_method should be 'manual')
"""
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResCompanyStripe(TransactionCase):
    """Tests for res.company SI Stripe fields."""

    def test_default_values(self):
        """New company should have safe defaults (deposit_mode=False)."""
        company = self.env['res.company'].create({'name': 'Test Stripe Co'})
        self.assertFalse(company.si_stripe_deposit_mode)
        self.assertEqual(company.si_stripe_deposit_percentage, 30.0)

    def test_can_enable_deposit_mode(self):
        """Company should allow enabling deposit mode."""
        company = self.env['res.company'].create({'name': 'Test Stripe Co 2'})
        company.si_stripe_deposit_mode = True
        self.assertTrue(company.si_stripe_deposit_mode)

    def test_can_set_custom_deposit_percentage(self):
        """Company should allow setting a custom deposit percentage."""
        company = self.env['res.company'].create({
            'name': 'Test Stripe Co 3',
            'si_stripe_deposit_percentage': 50.0,
        })
        self.assertEqual(company.si_stripe_deposit_percentage, 50.0)

    def test_deposit_percentage_zero_allowed(self):
        """Deposit percentage of 0 should be allowed (no deposit)."""
        company = self.env['res.company'].create({
            'name': 'Test Stripe Co 4',
            'si_stripe_deposit_percentage': 0.0,
        })
        self.assertEqual(company.si_stripe_deposit_percentage, 0.0)

    def test_deposit_percentage_100_allowed(self):
        """Deposit percentage of 100 should be allowed (full charge)."""
        company = self.env['res.company'].create({
            'name': 'Test Stripe Co 5',
            'si_stripe_deposit_percentage': 100.0,
        })
        self.assertEqual(company.si_stripe_deposit_percentage, 100.0)


@tagged('post_install', '-at_install')
class TestPaymentProviderInherit(TransactionCase):
    """Tests for payment.provider SI deposit mode override."""

    def setUp(self):
        super().setUp()
        # Find or create a Stripe payment provider
        Provider = self.env['payment.provider']
        self.provider = Provider.search([('code', '=', 'stripe')], limit=1)
        if not self.provider:
            # Create one if it doesn't exist (test environment)
            self.provider = Provider.create({
                'name': 'Stripe Test',
                'code': 'stripe',
                'state': 'test',
            })

    def test_provider_model_has_stripe_make_payment_request(self):
        """payment.provider should have _stripe_make_payment_request method."""
        self.assertTrue(hasattr(self.provider, '_stripe_make_payment_request'))

    def test_deposit_mode_disabled_passes_through(self):
        """When deposit mode is OFF, capture_method should not be forced to manual."""
        self.env.company.si_stripe_deposit_mode = False

        # Mock the parent method to capture kwargs
        with patch.object(
            type(self.env['payment.provider']),
            '_stripe_make_payment_request',
            autospec=True,
            return_value={'id': 'pi_test_123'},
        ) as mock_parent:
            # Re-fetch provider to get the patched class
            self.provider._stripe_make_payment_request(
                amount=100.0, currency_id=1, partner_id=1,
                capture_method='automatic',
            )
            # Parent should have been called
            mock_parent.assert_called_once()
            # The capture_method should remain 'automatic' (not overridden)
            call_kwargs = mock_parent.call_args
            # In Odoo 19, kwargs may be positional or keyword
            self.assertEqual(call_kwargs[1].get('capture_method'), 'automatic')

    def test_deposit_mode_enabled_forces_manual_capture(self):
        """When deposit mode is ON and capture_method != 'automatic',
        should force capture_method='manual'."""
        self.env.company.si_stripe_deposit_mode = True

        with patch.object(
            type(self.env['payment.provider']),
            '_stripe_make_payment_request',
            autospec=True,
            return_value={'id': 'pi_test_456'},
        ) as mock_parent:
            self.provider._stripe_make_payment_request(
                amount=100.0, currency_id=1, partner_id=1,
                # No capture_method specified — should default to 'manual'
            )
            mock_parent.assert_called_once()
            call_kwargs = mock_parent.call_args
            self.assertEqual(call_kwargs[1].get('capture_method'), 'manual')

    def test_deposit_mode_enabled_but_explicit_automatic_not_overridden(self):
        """When deposit mode is ON BUT caller explicitly passes
        capture_method='automatic', should NOT override."""
        self.env.company.si_stripe_deposit_mode = True

        with patch.object(
            type(self.env['payment.provider']),
            '_stripe_make_payment_request',
            autospec=True,
            return_value={'id': 'pi_test_789'},
        ) as mock_parent:
            self.provider._stripe_make_payment_request(
                amount=100.0, currency_id=1, partner_id=1,
                capture_method='automatic',
            )
            mock_parent.assert_called_once()
            call_kwargs = mock_parent.call_args
            # Should remain 'automatic' — explicit user intent wins
            self.assertEqual(call_kwargs[1].get('capture_method'), 'automatic')

    def test_non_stripe_provider_passes_through(self):
        """For non-stripe providers, the SI override should not apply."""
        # Find or create a non-stripe provider
        Provider = self.env['payment.provider']
        other_provider = Provider.search([('code', '!=', 'stripe')], limit=1)
        if not other_provider:
            # Skip this test if no other provider exists
            self.skipTest('No non-stripe provider available in test env')
            return

        self.env.company.si_stripe_deposit_mode = True

        with patch.object(
            type(Provider),
            '_stripe_make_payment_request',
            autospec=True,
            return_value={'id': 'pi_test'},
        ) as mock_parent:
            other_provider._stripe_make_payment_request(
                amount=100.0, currency_id=1, partner_id=1,
            )
            mock_parent.assert_called_once()
            # Should NOT have capture_method overridden for non-stripe
            call_kwargs = mock_parent.call_args
            self.assertNotIn('capture_method', call_kwargs[1])
