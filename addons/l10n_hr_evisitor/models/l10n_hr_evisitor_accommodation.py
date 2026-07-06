# -*- coding: utf-8 -*-
"""Croatian eVisitor accommodation (smještajni objekt).

Represents a single accommodation object (hotel, apartment, room, camp,
villa, house, boat, …) registered with the Croatian National Tourist
Board (HTZ) — each with its own HTZ id, address, capacity and tourist-tax
rates.
"""
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class L10nHrEvisitorAccommodation(models.Model):
    _name = 'l10n_hr.evisitor.accommodation'
    _description = 'Croatian eVisitor Accommodation (Smještajni objekt)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Naziv', required=True, tracking=True,
        help='Naziv smještajnog objekta.',
    )
    htz_id = fields.Char(
        string='HTZ oznaka', required=True, tracking=True, copy=False,
        help='Jedinstvena oznaka smještaja u sustavu HTZ eVisitor.',
    )
    code = fields.Char(
        string='Šifra', copy=False,
        help='Interni šifra objekta (ne obavezna).',
    )
    tourism_board_id = fields.Many2one(
        'res.partner', string='Turistička zajednica',
        help='Lokalna turistička zajedica kojoj objekt pripada.',
    )
    street = fields.Char(string='Ulica i broj', tracking=True)
    zip = fields.Char(string='Poštanski broj')
    city = fields.Char(string='Naselje')
    municipality = fields.Char(string='Općina/Grad')
    country_id = fields.Many2one(
        'res.country', string='Država',
        default=lambda self: self.env.ref('base.hr').id, required=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Tvrtka',
        default=lambda self: self.env.company, required=True,
    )
    active = fields.Boolean(default=True)

    accommodation_type = fields.Selection(
        selection=[('hotel', 'Hotel'),
                   ('apartment', 'Apartman'),
                   ('room', 'Soba'),
                   ('camp', 'Kamp'),
                   ('villa', 'Vila'),
                   ('house', 'Kuća'),
                   ('boat', 'Brod'),
                   ('other', 'Ostalo')],
        string='Tip objekta', required=True, default='apartment', tracking=True,
    )
    category = fields.Selection(
        selection=[('0', 'Bez kategorije'),
                   ('1', '★'),
                   ('2', '★★'),
                   ('3', '★★★'),
                   ('4', '★★★★'),
                   ('5', '★★★★★')],
        string='Kategorija (zvjezdice)', default='3', tracking=True,
    )
    capacity_rooms = fields.Integer(string='Broj soba', default=1)
    capacity_beds = fields.Integer(string='Broj ležajeva', default=2)
    capacity_extra_beds = fields.Integer(string='Broj pomoćnih ležajeva', default=0)

    # Tourist tax defaults (boravišna pristojba) per person per night, in EUR.
    # Statutory ceilings per Zakon o boravišnoj pristojbi (UR. l. RH š. 25/23).
    tourist_tax_adult = fields.Float(
        string='Boravišna pristojba — odrasli (EUR)', default=2.50,
        digits=(10, 2), tracking=True,
        help='Iznos boravišne pristojbe po odrasloj osobi po noćenju (EUR).',
    )
    tourist_tax_youth = fields.Float(
        string='Boravišna pristojba — mladi (EUR)', default=1.25,
        digits=(10, 2), tracking=True,
        help='Iznos boravišne pristojbe za mlade (12–17,99 g.) po noćenju (EUR).',
    )
    tourist_tax_child = fields.Float(
        string='Boravišna pristojba — djeca (EUR)', default=0.00,
        digits=(10, 2), tracking=True,
        help='Iznos boravišne pristojbe za djecu (0–11,99 g.) po noćenju (EUR). '
             'Djeca do 12 g. su oslobođena u većini općina.',
    )

    # HTZ eVisitor credentials — per-accommodation, since HTZ issues one
    # username/password per registered object.
    evisitor_username = fields.Char(
        string='eVisitor korisničko ime', copy=False,
        help='Korisničko ime za HTZ eVisitor API (izdano od strane TZ/HTZ).',
    )
    evisitor_password = fields.Char(
        string='eVisitor lozinka', copy=False,
        help='Lozinka za HTZ eVisitor API.',
    )
    environment = fields.Selection(
        selection=[('test', 'TEST (eVisitorRhetos_API/Rest/_test/)'),
                   ('prod', 'PROD (eVisitorRhetos_API/Rest/)')],
        string='Okolina', default='test', required=True, tracking=True,
    )

    registration_ids = fields.One2many(
        'l10n_hr.evisitor.guest.registration', 'accommodation_id',
        string='Prijave gosta', readonly=True,
    )
    registration_count = fields.Integer(
        string='Broj prijava', compute='_compute_registration_count',
    )

    _sql_constraints = [
        ('htz_id_company_uniq', 'unique(htz_id, company_id)',
         'HTZ oznaka mora biti jedinstvena po tvrtki.'),
    ]

    @api.depends('registration_ids')
    def _compute_registration_count(self):
        rg_data = self.env['l10n_hr.evisitor.guest.registration'].read_group(
            [('accommodation_id', 'in', self.ids)],
            ['accommodation_id'], ['accommodation_id'],
        )
        mapped = {r['accommodation_id'][0]: r['accommodation_id_count']
                  for r in rg_data}
        for acc in self:
            acc.registration_count = mapped.get(acc.id, 0)

    @api.constrains('htz_id')
    def _check_htz_id(self):
        for acc in self:
            if not acc.htz_id or not acc.htz_id.strip():
                raise ValidationError(_('HTZ oznaka ne može biti prazna.'))

    @api.constrains('tourist_tax_adult', 'tourist_tax_youth', 'tourist_tax_child')
    def _check_tourist_tax(self):
        for acc in self:
            for field_name in ('tourist_tax_adult', 'tourist_tax_youth',
                               'tourist_tax_child'):
                if getattr(acc, field_name) < 0:
                    raise ValidationError(_(
                        'Boravišna pristojba ne može biti negativna '
                        '(polje: %s).', field_name))

    # ---------------------------------------------------------------------
    # Actions
    # ---------------------------------------------------------------------

    def action_test_connection(self):
        """Poziv /Ping za provjeru povezanosti i vjerodajnica."""
        from .evisitor_client import (
            EVisitorClient, EVisitorAuthError, EVisitorValidationError,
            EVisitorConnectionError, EVisitorUnknownError,
        )
        for acc in self:
            if not acc.evisitor_username or not acc.evisitor_password:
                acc.message_post(body=_(
                    'Nije moguće testirati vezu: korisničko ime ili lozinka '
                    'nije konfigurirana.'))
                continue
            client = EVisitorClient(
                username=acc.evisitor_username,
                password=acc.evisitor_password,
                environment=acc.environment,
            )
            try:
                result = client.ping()
                acc.message_post(body=_(
                    'Veza uspješna (okolina: %s). Odgovor: %s',
                    acc.environment, result))
            except EVisitorAuthError as e:
                acc.message_post(body=_(
                    'Greška autentikacije: %s', str(e)))
            except EVisitorConnectionError as e:
                acc.message_post(body=_(
                    'Greška veze: %s', str(e)))
            except (EVisitorValidationError, EVisitorUnknownError) as e:
                acc.message_post(body=_(
                    'Neočekivana greška: %s', str(e)))

    def action_view_registrations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Prijave gosta'),
            'res_model': 'l10n_hr.evisitor.guest.registration',
            'view_mode': 'tree,form',
            'domain': [('accommodation_id', '=', self.id)],
            'context': {'default_accommodation_id': self.id},
        }
