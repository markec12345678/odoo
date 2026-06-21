# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    si_tax_number = fields.Char(
        string='Davčna številka',
        size=8,
        help='8-digit SI tax number (without SI prefix).',
    )
    si_birth_date = fields.Date(string='Datum rojstva')
    si_is_disabled = fields.Boolean(string='Invalid (olajšava)')
    si_is_student = fields.Boolean(string='Dijak/študent (olajšava)')
    si_is_young_worker = fields.Boolean(
        string='Mladi delojemalec (<30 let)',
        help='Special tax relief per ZDoh-2.',
    )
    si_is_pensioner = fields.Boolean(string='Upokojenec')
    si_children_count = fields.Integer(
        string='Število otrok (za olajšavo)',
        default=0,
    )
    si_additional_child_relief = fields.Boolean(
        string='Dodatna olajšava za otroke',
        help='For children with special needs — doubles child relief.',
    )
    si_bank_account = fields.Char(
        string='TRR (bančni račun)',
        help='IBAN format: SI56 1234 5678 9012 345',
    )
    si_work_permit_number = fields.Char(string='Številka delovnega dovoljenja')
    si_health_insurance_id = fields.Char(string='Številka ZZZS')
