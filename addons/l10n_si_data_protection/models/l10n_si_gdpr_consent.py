# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiGdprConsent(models.Model):
    _name = 'l10n_si.gdpr.consent'
    _description = 'Slovenian GDPR Consent'
    _order = 'create_date DESC'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    consent_type = fields.Selection(
        selection=[('marketing_email', 'Marketing e-pošta'),
                   ('marketing_sms', 'Marketing SMS'),
                   ('marketing_whatsapp', 'Marketing WhatsApp'),
                   ('profiling', 'Profiliranje'),
                   ('third_party_sharing', 'Delitev s tretjimi osebami'),
                   ('photo_use', 'Uporaba fotografij'),
                   ('cookies_analytics', 'Analitični piškotki')],
        required=True, default='marketing_email')

    state = fields.Selection(
        selection=[('granted', 'Dano'), ('withdrawn', 'Umaknjeno'), ('expired', 'Poteklo')],
        default='granted', tracking=True)

    granted_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    withdrawn_on = fields.Datetime(readonly=True, copy=False)
    valid_until = fields.Datetime(string='Veljavnost do')

    source = fields.Selection(
        selection=[('website', 'Spletna stran'),
                   ('checkin', 'Ob prijavi'),
                   ('paper', 'Pisno soglasje'),
                   ('phone', 'Telefonsko'),
                   ('import', 'Uvoz')],
        default='checkin', required=True)

    ip_address = fields.Char(readonly=True)
    notes = fields.Text()

    _sql_constraints = [
        ('partner_type_company_uniq', 'unique(partner_id, consent_type, company_id)',
         'Consent already exists for this partner/type/company.'),
    ]

    def action_withdraw(self):
        for c in self:
            c.write({
                'state': 'withdrawn',
                'withdrawn_on': fields.Datetime.now(),
            })
