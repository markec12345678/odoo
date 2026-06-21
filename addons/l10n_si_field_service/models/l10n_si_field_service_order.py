# -*- coding: utf-8 -*-
"""Field service work order."""
from odoo import api, fields, models


class L10nSiFieldServiceOrder(models.Model):
    _name = 'l10n_si.field.service.order'
    _description = 'Slovenian Field Service Order'
    _inherit = ['mail.thread']
    _order = 'scheduled_date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')

    # Customer + location
    partner_id = fields.Many2one('res.partner', string='Stranka', required=True, tracking=True)
    partner_address = fields.Text(compute='_compute_address', store=False)
    contact_phone = fields.Char(related='partner_id.phone')

    # Schedule
    scheduled_date = fields.Datetime(string='Načrtovani čas', required=True, default=fields.Datetime.now)
    actual_start = fields.Datetime(readonly=True, copy=False)
    actual_end = fields.Datetime(readonly=True, copy=False)
    duration = fields.Float(compute='_compute_duration', store=True, help='Trajanje v urah')

    # Assignment
    technician_id = fields.Many2one('hr.employee', string='Tehnik', tracking=True,
                                     domain="[('si_is_technician', '=', True)]")
    team_leader_id = fields.Many2one('hr.employee', string='Vodja ekipe')

    # Description
    title = fields.Char(string='Naslov', required=True)
    description = fields.Html(required=True)
    priority = fields.Selection(
        selection=[('0', 'Nizka'),
                   ('1', 'Normalna'),
                   ('2', 'Visoka'),
                   ('3', 'Nujno')],
        default='1',
        tracking=True,
    )
    category = fields.Selection(
        selection=[('installation', 'Vgradnja'),
                   ('repair', 'Popravilo'),
                   ('maintenance', 'Vzdrževanje'),
                   ('inspection', 'Pregled'),
                   ('delivery', 'Dostava')],
        default='repair',
    )

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('assigned', 'Dodeljeno'),
                   ('in_progress', 'V izvedbi'),
                   ('done', 'Opravljeno'),
                   ('cancelled', 'Preklicano'),
                   ('invoiced', 'Zaračunano')],
        default='draft',
        tracking=True,
    )

    # Material + costs
    material_line_ids = fields.One2many('l10n_si.field.service.material', 'order_id', string='Material')
    labor_cost = fields.Float(string='Strošek dela (€)', default=0.0)
    total_material_cost = fields.Float(compute='_compute_material_cost', store=True)
    total_cost = fields.Float(compute='_compute_total_cost', store=True)

    # Output
    invoice_id = fields.Many2one('account.move', string='Račun', readonly=True, copy=False)
    customer_signature = fields.Binary(string='Podpis stranke', copy=False)
    photo_before_ids = fields.One2many('l10n_si.field.service.photo', 'order_id', domain=[('type', '=', 'before')], string='Slike (pred)')
    photo_after_ids = fields.One2many('l10n_si.field.service.photo', 'order_id', domain=[('type', '=', 'after')], string='Slike (po)')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.field.service.order') or '/'
        return super().create(vals_list)

    @api.depends('number', 'partner_id', 'title')
    def _compute_name(self):
        for order in self:
            order.name = f'{order.number} - {order.title}'

    @api.depends('partner_id')
    def _compute_address(self):
        for order in self:
            p = order.partner_id
            order.partner_address = f'{p.street or ""}\n{p.zip or ""} {p.city or ""}\n{p.country_id.name or ""}'

    @api.depends('actual_start', 'actual_end')
    def _compute_duration(self):
        for order in self:
            if order.actual_start and order.actual_end:
                delta = order.actual_end - order.actual_start
                order.duration = delta.total_seconds() / 3600.0
            else:
                order.duration = 0.0

    @api.depends('material_line_ids.subtotal')
    def _compute_material_cost(self):
        for order in self:
            order.total_material_cost = sum(order.material_line_ids.mapped('subtotal'))

    @api.depends('labor_cost', 'total_material_cost')
    def _compute_total_cost(self):
        for order in self:
            order.total_cost = order.labor_cost + order.total_material_cost

    def action_assign(self):
        self.write({'state': 'assigned'})

    def action_start(self):
        for order in self:
            order.write({
                'state': 'in_progress',
                'actual_start': fields.Datetime.now(),
            })

    def action_complete(self):
        for order in self:
            order.write({
                'state': 'done',
                'actual_end': fields.Datetime.now(),
            })

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_generate_invoice(self):
        """Create customer invoice from work order."""
        Invoice = self.env['account.move']
        for order in self:
            if order.invoice_id:
                continue
            lines = [(0, 0, {
                'name': f'{order.title} - {order.category}',
                'quantity': order.duration,
                'price_unit': order.labor_cost / max(order.duration, 1) if order.duration else 0,
            })]
            for mat in order.material_line_ids:
                lines.append((0, 0, {
                    'product_id': mat.product_id.id,
                    'name': mat.product_id.name,
                    'quantity': mat.quantity,
                    'price_unit': mat.unit_price,
                }))
            invoice = Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': order.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': lines,
            })
            order.write({'invoice_id': invoice.id, 'state': 'invoiced'})


class L10nSiFieldServiceMaterial(models.Model):
    _name = 'l10n_si.field.service.material'
    _description = 'Slovenian Field Service Material Line'

    order_id = fields.Many2one('l10n_si.field.service.order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True)
    description = fields.Char()
    quantity = fields.Float(default=1.0, required=True)
    unit_price = fields.Float(required=True)
    subtotal = fields.Float(compute='_compute_subtotal', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price


class L10nSiFieldServicePhoto(models.Model):
    _name = 'l10n_si.field.service.photo'
    _description = 'Slovenian Field Service Photo'

    order_id = fields.Many2one('l10n_si.field.service.order', required=True, ondelete='cascade')
    type = fields.Selection(
        selection=[('before', 'Pred delom'),
                   ('after', 'Po delu'),
                   ('issue', 'Težava')],
        required=True,
        default='before',
    )
    image = fields.Binary(required=True)
    caption = fields.Char()
    taken_on = fields.Datetime(default=fields.Datetime.now)
