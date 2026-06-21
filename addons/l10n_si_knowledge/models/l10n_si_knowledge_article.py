# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiKnowledgeArticle(models.Model):
    _name = 'l10n_si.knowledge.article'
    _description = 'Slovenian Knowledge Article'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    category = fields.Selection(
        selection=[('procedure', 'Postopek'),
                   ('template', 'Predloga'),
                   ('faq', 'FAQ'),
                   ('onboarding', 'Onboarding'),
                   ('technical', 'Tehnično'),
                   ('other', 'Drugo')],
        default='procedure',
        required=True,
    )
    parent_id = fields.Many2one(
        'l10n_si.knowledge.article', string='Parent Article',
        ondelete='restrict',
    )
    child_ids = fields.One2many('l10n_si.knowledge.article', 'parent_id', string='Sub-articles')

    body = fields.Html(required=True)
    summary = fields.Text(help='Short TL;DR for search results.')

    # Visibility
    visibility = fields.Selection(
        selection=[('internal', 'Samo interno'),
                   ('portal', 'Portal stranke'),
                   ('public', 'Javno')],
        default='internal',
        required=True,
    )
    tag_ids = fields.Many2many('l10n_si.knowledge.tag', string='Tags')

    # Metadata
    author_id = fields.Many2one(
        'res.users', string='Author',
        default=lambda self: self.env.user, readonly=True,
    )
    created_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    last_updated = fields.Datetime(default=fields.Datetime.now, readonly=True)
    last_updated_by = fields.Many2one(
        'res.users', default=lambda self: self.env.user, readonly=True,
    )
    view_count = fields.Integer(default=0)

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Version history
    version_ids = fields.One2many(
        'l10n_si.knowledge.version', 'article_id', string='Versions', readonly=True,
    )

    def write(self, vals):
        if 'body' in vals or 'name' in vals:
            for article in self:
                self.env['l10n_si.knowledge.version'].create({
                    'article_id': article.id,
                    'name': article.name,
                    'body': article.body,
                    'snapshot_by': self.env.user.id,
                    'snapshot_on': fields.Datetime.now(),
                })
            vals['last_updated'] = fields.Datetime.now()
            vals['last_updated_by'] = self.env.user.id
        return super().write(vals)

    def action_view_increment(self):
        self.ensure_one()
        self.view_count += 1


class L10nSiKnowledgeTag(models.Model):
    _name = 'l10n_si.knowledge.tag'
    _description = 'Slovenian Knowledge Tag'

    name = fields.Char(required=True, translate=True)
    color = fields.Integer()


class L10nSiKnowledgeVersion(models.Model):
    _name = 'l10n_si.knowledge.version'
    _description = 'Slovenian Knowledge Article Version'
    _order = 'snapshot_on DESC'

    article_id = fields.Many2one('l10n_si.knowledge.article', required=True, ondelete='cascade')
    name = fields.Char(readonly=True)
    body = fields.Html(readonly=True)
    snapshot_by = fields.Many2one('res.users', readonly=True)
    snapshot_on = fields.Datetime(readonly=True)

    def action_restore(self):
        self.ensure_one()
        self.article_id.write({'name': self.name, 'body': self.body})
