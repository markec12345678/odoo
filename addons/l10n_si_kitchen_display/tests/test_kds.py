# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestKitchenDisplay(TransactionCase):
    """Basic CRUD and defaults for l10n_si.kitchen.display."""

    def setUp(self):
        super().setUp()
        self.kds = self.env['l10n_si.kitchen.display'].create({
            'name': 'Glavna kuhinja',
        })

    def test_creation_with_name(self):
        """A KDS can be created with just a name."""
        self.assertTrue(self.kds.id)
        self.assertEqual(self.kds.name, 'Glavna kuhinja')

    def test_auto_numbering_on_creation(self):
        """The ``number`` field is auto-assigned from the ir.sequence on create."""
        self.assertTrue(self.kds.number)
        self.assertNotEqual(self.kds.number, '/')
        # A second KDS gets a different (incremented) number.
        kds2 = self.env['l10n_si.kitchen.display'].create({
            'name': 'Skladisce',
        })
        self.assertNotEqual(self.kds.number, kds2.number)

    def test_default_active_is_true(self):
        """New KDS records are active by default."""
        self.assertTrue(self.kds.active)

    def test_company_assigned(self):
        """A new KDS is assigned to the current company."""
        self.assertTrue(self.kds.company_id.id)
        self.assertEqual(self.kds.company_id, self.env.company)
