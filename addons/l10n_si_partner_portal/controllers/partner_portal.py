# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class L10nSiPartnerPortal(http.Controller):
    @http.route('/my/stays', type='http', auth='user', website=True)
    def my_stays(self, **kw):
        folios = request.env['l10n_si.hotel.folio'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
        return request.render('l10n_si_partner_portal.portal_stays', {'folios': folios})

    @http.route('/my/loyalty', type='http', auth='user', website=True)
    def my_loyalty(self, **kw):
        member = request.env['l10n_si.loyalty.member'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)], limit=1)
        return request.render('l10n_si_partner_portal.portal_loyalty', {'member': member})
