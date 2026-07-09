# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    chatbot_enabled = fields.Boolean(string='Chatbot na spletni strani', default=True)
    chatbot_color = fields.Char(string='Barva chatbot gumba', default='#1E40AF')
    chatbot_position = fields.Selection([
        ('bottom_right', 'Spodaj desno'),
        ('bottom_left', 'Spodaj levo'),
    ], default='bottom_right', string='Pozicija')
