# -*- coding: utf-8 -*-
"""Slovenian fleet vehicle — extends standard fleet.vehicle."""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    si_plate_number = fields.Char(string='Registrska tablica', size=11)
    si_vin = fields.Char(string='Številka šasije (VIN)', size=17)
    si_engine_number = fields.Char(string='Številka motorja')
    si_year_of_production = fields.Integer(string='Leto proizvodnje')
    si_fuel_type = fields.Selection(
        selection=[('bencin', 'Bencin'),
                   ('dizel', 'Dizel'),
                   ('hibrid', 'Hibrid'),
                   ('elektricni', 'Električni'),
                   ('plin', 'Plin (LPG/CNG)'),
                   ('hibrid_plugin', 'Plug-in hibrid')],
        string='Tip goriva',
    )
    si_fuel_consumption = fields.Float(
        string='Poraba (l/100km ali kWh/100km)',
        help='Standardna poraba za primerjavo.',
    )
    si_insurance_company = fields.Char(string='Zavarovalnica')
    si_insurance_policy = fields.Char(string='Polica št.')
    si_insurance_expiry = fields.Date(string='Zavarovanje velja do')
    si_registration_expiry = fields.Date(string='Registracija velja do')
    si_technical_inspection_expiry = fields.Date(string='Tehnični pregled do')
    si_owner = fields.Char(string='Lastnik')
    si_acquisition_date = fields.Date(string='Datum nabave')
    si_acquisition_value = fields.Float(string='Nabavna vrednost (€)')
    si_current_value = fields.Float(string='Trenutna vrednost (€)')
    si_assigned_driver_id = fields.Many2one(
        'hr.employee', string='Trenutni voznik',
    )

    # Computed stats
    si_total_fuel_cost = fields.Float(
        compute='_compute_si_costs', store=False,
    )
    si_total_maintenance_cost = fields.Float(
        compute='_compute_si_costs', store=False,
    )
    si_total_cost = fields.Float(compute='_compute_si_costs', store=False)

    @api.depends('id')
    def _compute_si_costs(self):
        FuelLog = self.env['l10n_si.fleet.fuel']
        MaintLog = self.env['l10n_si.fleet.maintenance']
        for vehicle in self:
            fuel = FuelLog.search([('vehicle_id', '=', vehicle.id)])
            maint = MaintLog.search([('vehicle_id', '=', vehicle.id)])
            vehicle.si_total_fuel_cost = sum(fuel.mapped('total_cost'))
            vehicle.si_total_maintenance_cost = sum(maint.mapped('cost'))
            vehicle.si_total_cost = (
                vehicle.si_total_fuel_cost +
                vehicle.si_total_maintenance_cost
            )

    def action_view_trips(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vozni listi',
            'res_model': 'l10n_si.fleet.trip',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
        }

    def action_view_fuel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gorivo',
            'res_model': 'l10n_si.fleet.fuel',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
        }

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Servisi',
            'res_model': 'l10n_si.fleet.maintenance',
            'view_mode': 'tree,form',
            'domain': [('vehicle_id', '=', self.id)],
        }

    @api.model
    def _cron_check_expirations(self):
        """Daily check for vehicles with soon-to-expire documents.

        Sends email to fleet manager when:
        - Insurance expires in 30 or 7 days
        - Registration expires in 30 or 7 days
        - Technical inspection expires in 30 or 7 days
        """
        from datetime import date, timedelta
        today = date.today()
        soon = today + timedelta(days=30)
        very_soon = today + timedelta(days=7)

        for vehicle in self.search([]):
            for field_name, label in [
                ('si_insurance_expiry', 'zavarovanje'),
                ('si_registration_expiry', 'registracija'),
                ('si_technical_inspection_expiry', 'tehnični pregled'),
            ]:
                expiry = getattr(vehicle, field_name, None)
                if not expiry:
                    continue
                if expiry <= very_soon:
                    vehicle.message_post(
                        body=f'⚠️ {label.upper()} poteče čez {abs((expiry - today).days)} dni!',
                        subject=f'NUJNO: {label} vozila {vehicle.name}',
                    )
                elif expiry <= soon:
                    vehicle.message_post(
                        body=f'{label.capitalize()} poteče {expiry} ({(expiry - today).days} dni).',
                        subject=f'Opomnik: {label} vozila {vehicle.name}',
                    )
        return True
