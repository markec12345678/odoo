# -*- coding: utf-8 -*-
"""Mobile PWA controller."""
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiMobileApp(http.Controller):
    """PWA za osebje in goste."""

    @http.route('/mobile', type='http', auth='user', website=True)
    def index(self, **kwargs):
        """Glavni meni PWA."""
        return request.render('l10n_si_mobile_app.mobile_index', {
            'user': request.env.user,
        })

    @http.route('/mobile/housekeeping', type='http', auth='user', website=True)
    def housekeeping(self, **kwargs):
        """Hišništvo - seznam nalog za trenutnega hišnika."""
        employee = request.env.user.employee_id
        tasks = []
        if employee and employee.si_is_housekeeper:
            tasks = request.env['l10n_si.housekeeping.task'].search([
                ('housekeeper_id', '=', employee.id),
                ('state', 'in', ['assigned', 'in_progress']),
            ])
        else:
            # Manager: vse naloge
            tasks = request.env['l10n_si.housekeeping.task'].search([
                ('state', 'in', ['pending', 'assigned', 'in_progress']),
            ])
        return request.render('l10n_si_mobile_app.mobile_housekeeping', {
            'tasks': tasks,
            'is_manager': not (employee and employee.si_is_housekeeper),
        })

    @http.route('/mobile/housekeeping/<int:task_id>/start', type='json', auth='user')
    def hk_start(self, task_id):
        task = request.env['l10n_si.housekeeping.task'].browse(task_id)
        if task.exists():
            task.action_start()
            return json.dumps({'ok': True})
        return json.dumps({'error': 'Task not found'})

    @http.route('/mobile/housekeeping/<int:task_id>/complete', type='json', auth='user', methods=['POST'])
    def hk_complete(self, task_id, **kwargs):
        task = request.env['l10n_si.housekeeping.task'].browse(task_id)
        if task.exists():
            if kwargs.get('notes'):
                task.notes = kwargs['notes']
            task.action_complete()
            return json.dumps({'ok': True})
        return json.dumps({'error': 'Task not found'})

    @http.route('/mobile/maintenance', type='http', auth='user', website=True)
    def maintenance(self, **kwargs):
        """Tehnik - seznam odprtih zahtevkov."""
        requests = request.env['l10n_si.maintenance.request'].search([
            ('state', 'in', ['reported', 'assigned', 'in_progress', 'waiting_parts']),
        ])
        return request.render('l10n_si_mobile_app.mobile_maintenance', {
            'requests': requests,
        })

    @http.route('/mobile/maintenance/<int:req_id>/start', type='json', auth='user')
    def mt_start(self, req_id):
        req = request.env['l10n_si.maintenance.request'].browse(req_id)
        if req.exists():
            req.action_start()
            return json.dumps({'ok': True})
        return json.dumps({'error': 'Not found'})

    @http.route('/mobile/maintenance/<int:req_id>/resolve', type='json', auth='user', methods=['POST'])
    def mt_resolve(self, req_id, **kwargs):
        req = request.env['l10n_si.maintenance.request'].browse(req_id)
        if req.exists():
            if kwargs.get('resolution'):
                req.resolution_description = kwargs['resolution']
            req.action_resolve()
            return json.dumps({'ok': True})
        return json.dumps({'error': 'Not found'})

    @http.route('/mobile/reception', type='http', auth='user', website=True)
    def reception(self, **kwargs):
        """Recepcija - prihajajoče in odhajajoče za danes."""
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d')
        arrivals = request.env['l10n_si.hotel.reservation'].search([
            ('check_in', '>=', today + ' 00:00:00'),
            ('check_in', '<=', today + ' 23:59:59'),
            ('state', 'in', ['confirmed', 'checked_in']),
        ])
        departures = request.env['l10n_si.hotel.reservation'].search([
            ('check_out', '>=', today + ' 00:00:00'),
            ('check_out', '<=', today + ' 23:59:59'),
            ('state', 'in', ['checked_in']),
        ])
        return request.render('l10n_si_mobile_app.mobile_reception', {
            'arrivals': arrivals,
            'departures': departures,
        })

    @http.route('/mobile/reception/<int:res_id>/checkin', type='json', auth='user')
    def reception_checkin(self, res_id):
        res = request.env['l10n_si.hotel.reservation'].browse(res_id)
        if res.exists():
            res.action_check_in()
            return json.dumps({'ok': True})
        return json.dumps({'error': 'Not found'})

    @http.route('/mobile/reception/<int:res_id>/checkout', type='json', auth='user')
    def reception_checkout(self, res_id):
        res = request.env['l10n_si.hotel.reservation'].browse(res_id)
        if res.exists():
            res.action_check_out()
            return json.dumps({'ok': True})
        return json.dumps({'error': 'Not found'})

    @http.route('/mobile/manifest.json', type='http', auth='public')
    def manifest(self):
        """PWA manifest for installation."""
        manifest_data = {
            'name': 'SI Tourism Suite',
            'short_name': 'SI Suite',
            'description': 'Mobile app for hotel, restaurant, and event staff',
            'start_url': '/mobile',
            'display': 'standalone',
            'background_color': '#ffffff',
            'theme_color': '#875A7B',
            'orientation': 'portrait',
            'icons': [
                {'src': '/l10n_si_mobile_app/static/description/icon.png', 'sizes': '192x192', 'type': 'image/png'},
                {'src': '/l10n_si_mobile_app/static/description/icon.png', 'sizes': '512x512', 'type': 'image/png'},
            ],
        }
        return http.Response(
            json.dumps(manifest_data),
            content_type='application/json',
        )
