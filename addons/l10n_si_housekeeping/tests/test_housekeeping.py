# -*- coding: utf-8 -*-
"""Tests for l10n_si_housekeeping — task lifecycle and lost & found."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHousekeepingTask(TransactionCase):

    def test_task_model_exists(self):
        self.assertTrue(self.env['l10n_si.housekeeping.task'])

    def test_task_has_required_fields(self):
        fields = self.env['l10n_si.housekeeping.task']._fields
        self.assertIn('name', fields)
        self.assertIn('state', fields)

    def test_task_state_selection(self):
        field = self.env['l10n_si.housekeeping.task']._fields['state']
        keys = [s[0] for s in field.selection]
        # Should have at least pending/in_progress/done
        self.assertTrue(len(keys) > 0)

    def test_task_creation(self):
        task = self.env['l10n_si.housekeeping.task'].create({
            'name': 'Čiščenje sobe 101',
        })
        self.assertEqual(task.name, 'Čiščenje sobe 101')


@tagged('post_install', '-at_install')
class TestLostFound(TransactionCase):

    def test_lost_found_model_exists(self):
        self.assertTrue(self.env['l10n_si.housekeeping.lost.found'])

    def test_lost_found_has_fields(self):
        fields = self.env['l10n_si.housekeeping.lost.found']._fields
        self.assertIn('name', fields)
        self.assertIn('state', fields)

    def test_lost_found_creation(self):
        item = self.env['l10n_si.housekeeping.lost.found'].create({
            'name': 'Phone found in room 201',
        })
        self.assertEqual(item.name, 'Phone found in room 201')
