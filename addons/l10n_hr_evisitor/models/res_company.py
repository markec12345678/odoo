# -*- coding: utf-8 -*-
"""Croatian company extensions for eVisitor configuration."""
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_hr_evisitor_environment = fields.Selection(
        selection=[('test', 'TEST (eVisitorRhetos_API/Rest/_test/)'),
                   ('prod', 'PROD (eVisitorRhetos_API/Rest/)')],
        string='eVisitor okolina', default='test',
        help='Odabir okoline za HTZ eVisitor API. Test okolina koristi '
             'iste endpointove ali pod „_test/” putanjom.',
    )
    auto_register = fields.Boolean(
        string='Automatska prijava gosta', default=True,
        help='Ako je omogućeno, prijave gosta u statusu „Nacrt” automatski '
             'se šalju u eViewer cron-om svakih 15 minuta.',
    )
    auto_deregister = fields.Boolean(
        string='Automatska odjava gosta', default=True,
        help='Ako je omogućeno, gosti se automatski odjavljuju nakon '
             'planiranog datuma odlaska.',
    )
    notify_on_error = fields.Boolean(
        string='Obavijest pri grešci', default=True,
        help='Slanje obavijesti korisnicima kada prijava/odjava ne uspije '
             'i ne može se automatski ponoviti.',
    )
    notify_user_ids = fields.Many2many(
        'res.users', string='Primatelji obavijesti',
        help='Korisnici koji primaju obavijesti o greškama u integraciji s '
             'eVisitor sustavom.',
    )
