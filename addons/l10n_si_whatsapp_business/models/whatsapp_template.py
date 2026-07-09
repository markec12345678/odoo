from odoo import fields, models


class WhatsAppTemplate(models.Model):
    _name = 'wa.template'
    _description = 'WhatsApp Message Template'

    name = fields.Char(string='Template Name', required=True, help='Must match the name in Meta Business Suite')
    language = fields.Selection([
        ('sl', 'Slovenian'),
        ('hr', 'Croatian'),
        ('en', 'English'),
        ('de', 'German'),
        ('it', 'Italian'),
    ], default='sl', required=True)
    body = fields.Text(string='Template Body', help='Template text with {{1}}, {{2}} placeholders')
    category = fields.Selection([
        ('marketing', 'Marketing'),
        ('utility', 'Utility'),
        ('authentication', 'Authentication'),
    ], default='utility')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
