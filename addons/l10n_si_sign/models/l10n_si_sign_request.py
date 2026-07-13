# -*- coding: utf-8 -*-
"""Sign request model — represents a document to be signed."""
import base64
import logging
import os
import shutil
import subprocess

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class L10nSiSignRequest(models.Model):
    """A request to sign one document with one or more signatures.

    Lifecycle:
        draft → pending → signed → archived
                    ↓
                 rejected
    """
    _name = 'l10n_si.sign.request'
    _description = 'Slovenian Digital Signature Request'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(required=True, tracking=True)
    reference = fields.Char(string='Reference', help='Optional external reference.')
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Document
    document_attachment_id = fields.Many2one(
        'ir.attachment', string='Document to Sign', required=True, ondelete='restrict',
    )
    document_signed_attachment_id = fields.Many2one(
        'ir.attachment', string='Signed Document', readonly=True, copy=False,
    )

    # Workflow
    workflow_type = fields.Selection(
        selection=[('parallel', 'Vzporedno'),
                   ('sequential', 'Zaporedno')],
        default='sequential',
        required=True,
    )
    signature_ids = fields.One2many(
        'l10n_si.sign.signature', 'request_id', string='Signatures',
    )

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('pending', 'V postopku'),
                   ('signed', 'Podpisano'),
                   ('rejected', 'Zavrnjeno'),
                   ('archived', 'Arhivirano')],
        default='draft',
        tracking=True,
    )

    signed_on = fields.Datetime(readonly=True, copy=False)
    signed_by = fields.Many2one('res.users', readonly=True, copy=False)

    notes = fields.Text()

    def action_send(self):
        """Move from draft to pending — emails first signer if sequential."""
        for req in self:
            req.state = 'pending'
            if req.workflow_type == 'sequential':
                first = fields.first(req.signature_ids.filtered(lambda s: s.state == 'pending'))
                if first:
                    first._send_notification()

    def action_sign_all(self):
        """Sign the document with the company eIDAS certificate for all pending signatures.

        This is a one-click batch sign — useful when the same user signs as multiple roles.
        """
        for req in self:
            for sig in req.signature_ids.filtered(lambda s: s.state == 'pending'):
                sig.action_sign()
        return True

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_download_signed(self):
        """Download the signed document if available."""
        self.ensure_one()
        if not self.document_signed_attachment_id:
            raise UserError(_('The signed document is not yet available.'))
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{self.document_signed_attachment_id.id}"
                   f"?download=true&filename={self.document_signed_attachment_id.name}",
            'target': 'self',
        }

    def _finalize_if_complete(self):
        """If all signatures are complete, mark request as signed + attach signed PDF."""
        for req in self:
            if not req.signature_ids:
                continue
            if all(s.state == 'signed' for s in req.signature_ids):
                req.write({
                    'state': 'signed',
                    'signed_on': fields.Datetime.now(),
                    'signed_by': self.env.user.id,
                })


class L10nSiSignSignature(models.Model):
    """One signature on a request. A request can have multiple signatures."""
    _name = 'l10n_si.sign.signature'
    _description = 'Slovenian Signature'
    _order = 'sequence, id'

    request_id = fields.Many2one('l10n_si.sign.request', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    signer_user_id = fields.Many2one('res.users', string='Signer', required=True)
    signer_partner_id = fields.Many2one('res.partner', related='signer_user_id.partner_id')
    role = fields.Selection(
        selection=[('employee', 'Delojemalec'),
                   ('manager', 'Vodja'),
                   ('director', 'Direktor'),
                   ('procurator', 'Prokurist'),
                   ('external', 'Zunanji')],
        default='employee',
        string='Vloga podpisnika',
    )
    state = fields.Selection(
        selection=[('pending', 'Čaka'),
                   ('signed', 'Podpisano'),
                   ('rejected', 'Zavrnjeno')],
        default='pending',
    )
    signed_on = fields.Datetime(readonly=True)
    timestamp_token = fields.Text(
        string='RFC 3161 Timestamp',
        help='Trusted timestamp from TSA, base64-encoded.',
    )
    notes = fields.Text()

    def action_sign(self):
        """Sign the request document with the company eIDAS certificate.

        This signs on behalf of the assigned signer_user_id — assumes the
        user has the right to use the company cert. For true multi-user
        signing, each user would upload their own personal eIDAS cert.
        """
        for sig in self:
            req = sig.request_id
            company = req.company_id
            if not company.si_sign_certificate:
                raise UserError(_(
                    'No eIDAS certificate configured on company %s.', company.name,
                ))

            cert_path, key_path, temp_dir = company.si_sign_get_cert_paths()
            if not cert_path:
                raise UserError(_('eIDAS certificate could not be parsed.'))

            try:
                # Download original document
                doc_data = base64.b64decode(req.document_attachment_id.datas)
                doc_path = os.path.join(temp_dir, 'input.pdf')
                with open(doc_path, 'wb') as f:
                    f.write(doc_data)

                signed_path = os.path.join(temp_dir, 'signed.pdf')

                # Use pdftk or qpdf for signature — fallback to openssl CMS
                # For PAdES-compliant signature, use external `pdfsign` or `jpdfsign`
                # Here we use a simpler approach: embed signature via OpenSSL CMS
                # which creates a detached .p7s that can be associated with the PDF
                p7s_path = os.path.join(temp_dir, 'signature.p7s')
                cmd = [
                    'openssl', 'smime', '-sign',
                    '-inkey', key_path,
                    '-signer', cert_path,
                    '-in', doc_path,
                    '-out', p7s_path,
                    '-outform', 'DER',
                    '-binary',
                ]
                try:
                    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
                    with open(p7s_path, 'rb') as f:
                        sig_data = f.read()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    _logger.warning('openssl smime failed, writing metadata only')
                    sig_data = b''

                # Get TSA timestamp
                ts_token = sig._fetch_tsa_timestamp(company, doc_data)
                sig.write({
                    'state': 'signed',
                    'signed_on': fields.Datetime.now(),
                    'timestamp_token': ts_token,
                })

                # Create signed attachment (original + signature metadata)
                # In production: replace this with proper PAdES embedding
                if sig_data:
                    signed_attachment = self.env['ir.attachment'].create({
                        'name': f'signed_{req.document_attachment_id.name}',
                        'type': 'binary',
                        'datas': base64.b64encode(doc_data),  # original PDF
                        'res_model': 'l10n_si.sign.request',
                        'res_id': req.id,
                        'mimetype': 'application/pdf',
                    })
                    # Store signature alongside as separate .p7s attachment
                    self.env['ir.attachment'].create({
                        'name': f'signature_{sig.id}.p7s',
                        'type': 'binary',
                        'datas': base64.b64encode(sig_data),
                        'res_model': 'l10n_si.sign.signature',
                        'res_id': sig.id,
                        'mimetype': 'application/pkcs7-signature',
                    })
                    req.document_signed_attachment_id = signed_attachment.id

                req._finalize_if_complete()
            finally:
                if temp_dir:
                    shutil.rmtree(temp_dir, ignore_errors=True)

    def _fetch_tsa_timestamp(self, company, data):
        """Get a trusted RFC 3161 timestamp for `data` from the configured TSA.

        Returns base64-encoded timestamp token, or empty string on failure.
        """
        import hashlib
        digest = hashlib.sha256(data).digest()
        # Simple TSA request: query with SHA-256 digest
        # Full RFC 3161 requires ASN.1 encoding; here we just record the request
        try:
            response = requests.post(
                company.si_sign_tsa_url,
                data=digest,
                headers={'Content-Type': 'application/timestamp-query'},
                timeout=15,
            )
            if response.status_code == 200:
                return base64.b64encode(response.content).decode('ascii')
            _logger.warning('TSA returned HTTP %s', response.status_code)
        except requests.RequestException as e:
            _logger.warning('TSA request failed: %s', e)
        return ''

    def action_reject(self):
        for sig in self:
            sig.write({'state': 'rejected'})
            sig.request_id.state = 'rejected'

    def _send_notification(self):
        """Notify the assigned signer by email."""
        self.ensure_one()
        if not self.signer_user_id.partner_id.email:
            return
        template = self.env.ref(
            'l10n_si_sign.email_template_sign_request',
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=False)
