# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged


# The 14 mandatory EU allergens per Regulation (EU) No 1169/2011, Annex II.
EU_ALLERGEN_FIELDS = [
    'allergen_gluten',
    'allergen_crustaceans',
    'allergen_eggs',
    'allergen_fish',
    'allergen_peanuts',
    'allergen_soy',
    'allergen_milk',
    'allergen_nuts',
    'allergen_celery',
    'allergen_mustard',
    'allergen_sesame',
    'allergen_sulphites',
    'allergen_lupin',
    'allergen_molluscs',
]


@tagged('post_install', '-at_install')
class TestRestaurantWorkflow(TransactionCase):
    """Restaurant tables, state transitions, menu allergens and pricing."""

    def setUp(self):
        super().setUp()
        self.table = self.env['l10n_si.restaurant.table'].create({
            'number': 'T1',
            'floor': 'indoor',
            'capacity': 4,
        })

    # ------------------------------------------------------------------
    # Table state
    # ------------------------------------------------------------------

    def test_table_default_state_is_free(self):
        """A freshly created table is in the 'free' state."""
        self.assertEqual(self.table.state, 'free')

    def test_table_state_transitions(self):
        """Tables move through free → occupied → cleaning → reserved → free."""
        # free → occupied
        self.table.action_occupy()
        self.assertEqual(self.table.state, 'occupied')
        # occupied → cleaning
        self.table.action_cleaning()
        self.assertEqual(self.table.state, 'cleaning')
        # cleaning → reserved
        self.table.action_reserve()
        self.assertEqual(self.table.state, 'reserved')
        # reserved → free
        self.table.action_free()
        self.assertEqual(self.table.state, 'free')

    # ------------------------------------------------------------------
    # Menu allergens (EU 1169/2011 — 14 mandatory allergens)
    # ------------------------------------------------------------------

    def test_menu_item_has_all_14_eu_allergen_fields(self):
        """The menu model must declare all 14 EU-mandated allergen booleans."""
        fields = self.env['l10n_si.restaurant.menu']._fields
        for field_name in EU_ALLERGEN_FIELDS:
            self.assertIn(
                field_name, fields,
                f'Missing allergen field {field_name!r} on l10n_si.restaurant.menu.',
            )
        self.assertEqual(len(EU_ALLERGEN_FIELDS), 14)

    def test_menu_item_allergen_defaults_are_false(self):
        """Allergen flags default to False (no allergen declared)."""
        menu_fields = self.env['l10n_si.restaurant.menu']._fields
        for field_name in EU_ALLERGEN_FIELDS:
            self.assertFalse(
                menu_fields[field_name].default,
                f'{field_name} should default to False.',
            )

    # ------------------------------------------------------------------
    # Menu pricing
    # ------------------------------------------------------------------

    def test_menu_price_inherits_from_product_lst_price(self):
        """menu.price is a related field reading product_id.lst_price."""
        product = self.env['product.product'].create({
            'name': 'Kranjska klobasa',
            'lst_price': 12.50,
            'type': 'consu',
        })
        menu = self.env['l10n_si.restaurant.menu'].create({
            'name': 'Kranjska klobasa',
            'product_id': product.id,
        })
        self.assertEqual(menu.price, 12.50)
        # Changing the product price is reflected on the menu (related, non-stored).
        product.lst_price = 14.90
        self.assertEqual(menu.price, 14.90)
