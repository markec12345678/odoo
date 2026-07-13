# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    si_serial_number = fields.Char(string='Serijska številka')
    si_acquisition_date = fields.Date(string='Datum nabave')
    si_acquisition_value = fields.Float(string='Nabavna vrednost (€)')
    si_warranty_expiry = fields.Date(string='Garancija do')
    si_location = fields.Char(string='Lokacija')
    si_critical = fields.Boolean(
        string='Kritična oprema',
        help='Critical equipment — failure causes production stop.',
        default=False,
    )
    si_mtbf_hours = fields.Float(
        string='MTBF (ure)',
        compute='_compute_mtbf_mttr', store=False,
        help='Mean Time Between Failures.',
    )
    si_mttr_hours = fields.Float(
        string='MTTR (ure)',
        compute='_compute_mtbf_mttr', store=False,
        help='Mean Time To Repair.',
    )
    si_downtime_hours_year = fields.Float(
        string='Skupni izpadi (letno)',
        compute='_compute_mtbf_mttr', store=False,
    )
    si_schedule_ids = fields.One2many(
        'l10n_si.maintenance.schedule', 'equipment_id', string='Preventive Schedules',
    )
    si_total_maintenance_cost = fields.Float(
        compute='_compute_costs', store=False,
    )

    def _compute_mtbf_mttr(self):
        Request = self.env['maintenance.request']
        for eq in self:
            requests = Request.search([
                ('equipment_id', '=', eq.id),
                ('stage_id.done', '=', True),
            ])
            if not requests:
                eq.si_mtbf_hours = 0.0
                eq.si_mttr_hours = 0.0
                eq.si_downtime_hours_year = 0.0
                continue
            # MTTR: average duration
            durations = []
            for req in requests:
                if req.schedule_date and req.close_date:
                    d = (req.close_date - req.schedule_date).total_seconds() / 3600
                    if d > 0:
                        durations.append(d)
            eq.si_mttr_hours = sum(durations) / len(durations) if durations else 0
            # MTBF: average time between consecutive requests
            sorted_reqs = requests.sorted('schedule_date')
            gaps = []
            for i in range(1, len(sorted_reqs)):
                gap = (sorted_reqs[i].schedule_date - sorted_reqs[i - 1].close_date).total_seconds() / 3600
                if gap > 0:
                    gaps.append(gap)
            eq.si_mtbf_hours = sum(gaps) / len(gaps) if gaps else 0
            # Yearly downtime
            year_start = fields.Datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0)
            year_reqs = requests.filtered(lambda r: r.schedule_date >= year_start)
            eq.si_downtime_hours_year = sum(
                (r.close_date - r.schedule_date).total_seconds() / 3600
                for r in year_reqs if r.close_date and r.schedule_date
            )

    def _compute_costs(self):
        Request = self.env['maintenance.request']
        for eq in self:
            reqs = Request.search([('equipment_id', '=', eq.id)])
            eq.si_total_maintenance_cost = sum(reqs.mapped('si_cost'))


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    si_cost = fields.Float(string='Strošek (€)', default=0.0)
    si_parts_line_ids = fields.One2many(
        'l10n_si.maintenance.part.line', 'request_id', string='Potrošni material',
    )
    si_downtime_hours = fields.Float(
        string='Čas izpada (ure)', default=0.0,
        help='Production downtime caused by this failure.',
    )
    si_root_cause = fields.Text(string='Vzrok okvare')
    si_action_taken = fields.Text(string='Izvedeni ukrepi')


class L10nSiMaintenancePartLine(models.Model):
    _name = 'l10n_si.maintenance.part.line'
    _description = 'Slovenian Maintenance Parts Line'

    request_id = fields.Many2one('maintenance.request', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True)
    quantity = fields.Float(default=1.0, required=True)
    unit_price = fields.Float(required=True)
    subtotal = fields.Float(compute='_compute_subtotal', store=True)
    stock_move_id = fields.Many2one('stock.move', string='Stock Move', readonly=True, copy=False)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
