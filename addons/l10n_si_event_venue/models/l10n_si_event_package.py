# -*- coding: utf-8 -*-
"""Package = paket storitev (poročni paket, konferenca, obletnica)."""
from odoo import api, fields, models


class L10nSiEventPackage(models.Model):
    """Paketi za različne tipe dogodkov.

    Primeri:
    - "Premium poročni paket": dvorana + catering za 100 oseb + DJ + fotograf
    - "Konferenčni paket ZA DAN": dvorana + zajtrk + kosilo + oprema
    - "Obletnica": manjša dvorana + catering za 50 oseb
    """
    _name = 'l10n_si.event.package'
    _description = 'Slovenian Event Package'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, size=16)
    active = fields.Boolean(default=True)
    category = fields.Selection(
        selection=[('wedding', 'Poroka'),
                   ('conference', 'Konferenca'),
                   ('business_meeting', 'Poslovni sestanek'),
                   ('birthday', 'Rojsni dan'),
                   ('anniversary', 'Obletnica'),
                   ('gala', 'Gala večer'),
                   ('other', 'Drugo')],
        default='wedding',
        required=True,
    )

    # Opis in kapaciteta
    description = fields.Html()
    min_guests = fields.Integer(string='Min. gostov', default=20)
    max_guests = fields.Integer(string='Max. gostov', default=200)
    image = fields.Binary()

    # Cena
    base_price = fields.Float(string='Osnovna cena (EUR)', required=True,
                               help='Osnovna cena paketa (brez dodatnih storitev).')
    price_per_extra_guest = fields.Float(string='Dodatni gost (EUR)', default=0.0)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id, required=True,
    )

    # Kaj je vključeno
    includes_hall = fields.Boolean(string='Dvorana vključena', default=True)
    includes_catering = fields.Boolean(string='Catering vključen', default=True)
    includes_equipment = fields.Boolean(string='Oprema vključena', default=True)
    includes_service_staff = fields.Boolean(string='Osebje vključeno', default=True)
    includes_decorations = fields.Boolean(string='Dekoracije vključene', default=False)
    includes_photographer = fields.Boolean(string='Fotograf vključen', default=False)
    includes_music = fields.Boolean(string='Glasba/DJ vključena', default=False)
    includes_valet = fields.Boolean(string='Valet parking vključen', default=False)

    # Trajanje
    duration_hours = fields.Float(string='Trajanje (ure)', default=8.0,
                                    help='Koliko ur traja paket (vpliva na ceno dvorane).')

    # Pogoji
    deposit_percent = fields.Float(string='Avans (%)', default=30.0)
    cancellation_days = fields.Integer(string='Brezplačna odpoved (dni)', default=14)
    free_changes_days = fields.Integer(string='Brezplačne spremembe (dni)', default=30)

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Package code must be unique per company.'),
    ]
