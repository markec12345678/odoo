# -*- coding: utf-8 -*-
"""SRS (Slovenski računovodski standardi) account reference.

Each Slovenian chart-of-accounts entry (account.account) can be linked to
an SRS 99 reference account. The reference catalog is shared by all
companies and used by the financial reports (bilanca, izid poslovanja).
"""
from odoo import _, api, fields, models


class L10nSiSrsAccount(models.Model):
    """SRS 99 reference account — the canonical Slovenian account catalog.

    Each record represents one SRS 99 account (3-digit code, e.g. 010 =
    'Osnovna sredstva v nabavni vrednosti'). The catalog is company-aware
    so each company can independently enable/disable individual accounts,
    but the code itself is unique per company.
    """
    _name = 'l10n_si.srs.account'
    _description = 'Slovenian SRS Reference Account'
    _order = 'code'

    code = fields.Char(
        string='SRS koda', required=True, size=3, index=True,
        help='3-mestna koda konta po SRS 99 (npr. 010, 110, 210 ...).',
    )
    name = fields.Char(string='Naziv', required=True, translate=True)
    display_name = fields.Char(
        string='Prikazno ime', compute='_compute_display_name',
        store=True, index=True,
    )
    user_type = fields.Selection(
        selection=[('asset', 'Sredstva'),
                   ('liability', 'Obveznosti'),
                   ('equity', 'Kapital'),
                   ('income', 'Prihodki'),
                   ('expense', 'Odhodki')],
        string='Vrsta konta',
        required=True,
    )
    srs_category = fields.Selection(
        selection=[('balance_sheet', 'Bilanca stanja'),
                   ('income_statement', 'Izid poslovanja'),
                   ('cash_flow', 'Denarni tokovi'),
                   ('year_end', 'Zaključni konti')],
        string='SRS kategorija',
        required=True,
        default='balance_sheet',
    )
    balance_sheet_position = fields.Char(
        string='Položaj v bilanci',
        size=16,
        help='Oznaka postavke v bilanci stanja po SRS 99, npr. "A.I.1", "B.II.3", "C.I".',
    )
    account_class = fields.Selection(
        selection=[(str(i), str(i)) for i in range(0, 10)],
        string='Razred konta',
        required=True,
        help='Prva številka kode (0-9): 0=osnovna sredstva, 1=zaloge ...',
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True, index=True,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'SRS account code must be unique per company.'),
    ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.code} — {rec.name}' if rec.code else rec.name

    # ------------------------------------------------------------------
    # Legacy name_get / name_search (Odoo 19 still supports them as
    # overrides; the ORM falls back to them when ``display_name`` is not
    # explicitly asked for in some places).
    # ------------------------------------------------------------------
    def name_get(self):
        return [(rec.id, f'{rec.code} — {rec.name}') for rec in self]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Search by code OR by name — code first for exact prefix matches."""
        if args is None:
            args = []
        if name:
            records = self.search(
                ['|', ('code', '=like', f'{name}%'), ('name', operator, name)] + args,
                limit=limit,
            )
            return records.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model
    def create(self, vals_list):
        """Auto-fill ``account_class`` from ``code`` if not specified."""
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        for vals in vals_list:
            if not vals.get('account_class') and vals.get('code'):
                vals['account_class'] = str(vals['code'])[:1]
        return super().create(vals_list)


class AccountAccount(models.Model):
    """Extend account.account with a link to the SRS 99 reference."""
    _inherit = 'account.account'

    l10n_si_srs_account_id = fields.Many2one(
        'l10n_si.srs.account', string='SRS konto',
        ondelete='restrict', index=True,
        help='Referenca na konto po slovenskem računovodskem standardu SRS 99.',
    )
