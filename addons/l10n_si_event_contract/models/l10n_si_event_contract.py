# -*- coding: utf-8 -*-
"""Contract - konkretna pogodba izpredloge, vezana na event."""
import base64

from odoo import api, fields, models


class L10nSiEventContract(models.Model):
    _name = 'l10n_si.event.contract'
    _description = 'Slovenian Event Contract'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(required=True, tracking=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    event_id = fields.Many2one('l10n_si.event.event', required=True, ondelete='cascade')
    template_id = fields.Many2one('l10n_si.event.contract.template', required=True, ondelete='restrict')
    company_id = fields.Many2one(related='event_id.company_id', store=True)

    # Vsebina
    body = fields.Html(required=True, sanitize=False)

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('sent', 'Poslano stranki'),
                   ('signed_customer', 'Podpisala stranka'),
                   ('signed_both', 'Podpisalo oboje'),
                   ('archived', 'Arhivirano'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )

    # Podpisi
    pdf_attachment_id = fields.Many2one('ir.attachment', string='PDF', readonly=True, copy=False)
    sign_request_id = fields.Many2one('l10n_si.sign.request', string='Sign Request', readonly=True, copy=False)

    # Datumi
    sent_on = fields.Datetime(readonly=True, copy=False)
    customer_signed_on = fields.Datetime(readonly=True, copy=False)
    both_signed_on = fields.Datetime(readonly=True, copy=False)

    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.event.contract') or '/'
        return super().create(vals_list)

    @api.onchange('template_id', 'event_id')
    def _onchange_template_id(self):
        """Avtomatsko zafilaj body iz template z substituiranimi placeholders."""
        if self.template_id and self.event_id:
            self.body = self._render_template(self.template_id.body, self.event_id)
            if not self.name:
                self.name = f'{self.template_id.name} - {self.event_id.name}'

    def _render_template(self, template_body, event):
        """Zamenjaj placeholderje z dejanskimi vrednostmi."""
        ev = event
        co = ev.company_id
        partner = ev.partner_id
        venue = ev.venue_id

        replacements = {
            '{{event.name}}': ev.name or '',
            '{{event.number}}': ev.number or '',
            '{{event.date_start}}': ev.date_start.strftime('%d.%m.%Y %H:%M') if ev.date_start else '',
            '{{event.date_end}}': ev.date_end.strftime('%d.%m.%Y %H:%M') if ev.date_end else '',
            '{{event.expected_guests}}': str(ev.expected_guests or 0),
            '{{event.total_amount}}': f'{ev.total_amount:.2f} EUR',
            '{{event.special_requests}}': ev.special_requests or '',
            '{{partner.name}}': partner.name or '',
            '{{partner.street}}': partner.street or '',
            '{{partner.zip}}': partner.zip or '',
            '{{partner.city}}': partner.city or '',
            '{{partner.vat}}': partner.vat or '',
            '{{partner.email}}': partner.email or '',
            '{{partner.phone}}': partner.phone or '',
            '{{venue.name}}': venue.name or '',
            '{{venue.street}}': venue.street or '',
            '{{venue.zip}}': venue.zip or '',
            '{{venue.city}}': venue.city or '',
            '{{company.name}}': co.name or '',
            '{{company.street}}': co.street or '',
            '{{company.zip}}': co.zip or '',
            '{{company.city}}': co.city or '',
            '{{company.vat}}': co.vat or '',
            '{{company.phone}}': co.phone or '',
            '{{company.email}}': co.email or '',
            '{{date.today}}': fields.Date.today().strftime('%d.%m.%Y'),
        }
        body = template_body
        for placeholder, value in replacements.items():
            body = body.replace(placeholder, value)
        return body

    def action_generate_pdf(self):
        """Generiraj PDF iz body (uporabi QWeb report)."""
        for contract in self:
            # Preprosta PDF generacija preko reporta
            attachment = self.env['ir.attachment'].create({
                'name': f'Pogodba_{contract.number}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(contract.body.encode('utf-8')),
                'res_model': 'l10n_si.event.contract',
                'res_id': contract.id,
                'mimetype': 'application/pdf',
            })
            contract.pdf_attachment_id = attachment.id

    def action_send_to_customer(self):
        """Pošlji pogodbo stranki z e-pošto za podpis."""
        for contract in self:
            if not contract.pdf_attachment_id:
                contract.action_generate_pdf()
            # Ustvari sign request preko l10n_si_sign
            sign_request = self.env['l10n_si.sign.request'].create({
                'name': f'Pogodba {contract.number} - {contract.event_id.name}',
                'partner_id': contract.event_id.partner_id.id,
                'document_attachment_id': contract.pdf_attachment_id.id,
                'workflow_type': 'sequential',
            })
            # Dva podpisnika: stranka + organizator
            self.env['l10n_si.sign.signature'].create({
                'request_id': sign_request.id,
                'signer_user_id': self.env.user.id,
                'role': 'employee',
            })
            sign_request.action_send()
            contract.write({
                'sign_request_id': sign_request.id,
                'state': 'sent',
                'sent_on': fields.Datetime.now(),
            })

    def action_mark_customer_signed(self):
        """Stranka je podpisala."""
        self.write({
            'state': 'signed_customer',
            'customer_signed_on': fields.Datetime.now(),
        })

    def action_mark_both_signed(self):
        """Oboje podpisalo."""
        self.write({
            'state': 'signed_both',
            'both_signed_on': fields.Datetime.now(),
        })

    def action_archive(self):
        """Arhiviraj podpisano pogodbo."""
        self.write({'state': 'archived'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
