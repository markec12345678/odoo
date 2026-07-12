# -*- coding: utf-8 -*-
"""Audit trail for sensitive data changes.

Tracks create/write/unlink operations on models with sensitive fields.
IP address is captured from the HTTP request context.
Sensitive fields are configurable via ir.config_parameter.
"""
import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Default sensitive fields (can be extended via system parameter)
DEFAULT_SENSITIVE_FIELDS = [
    "price_unit", "list_price", "standard_price", "vat", "amount_total",
    "tax_ids", "l10n_si_zoi", "l10n_si_eor", "l10n_hr_zki", "l10n_hr_jir",
    "state", "partner_id", "amount", "quantity", "discount",
]


class L10nSiAuditTrail(models.Model):
    _name = "l10n_si.audit.trail"
    _description = "Slovenian Audit Trail"
    _order = "create_date DESC"

    name = fields.Char(compute="_compute_name", store=True)
    user_id = fields.Many2one(
        "res.users", string="Uporabnik", required=True,
        default=lambda s: s.env.user, readonly=True,
    )
    model_name = fields.Char(string="Model", required=True, readonly=True)
    record_id = fields.Integer(string="ID zapisa", required=True, readonly=True)
    record_name = fields.Char(string="Ime zapisa", readonly=True)
    action_type = fields.Selection(
        [("create", "Ustvarjeno"),
         ("write", "Spremenjeno"),
         ("unlink", "Izbrisano")],
        required=True, readonly=True,
    )
    field_name = fields.Char(string="Polje", readonly=True)
    old_value = fields.Text(string="Stara vrednost", readonly=True)
    new_value = fields.Text(string="Nova vrednost", readonly=True)
    ip_address = fields.Char(string="IP naslov", readonly=True)
    company_id = fields.Many2one(
        "res.company", string="Company",
        default=lambda s: s.env.company, required=True,
    )

    @api.depends("model_name", "record_name", "action_type")
    def _compute_name(self):
        for r in self:
            r.name = f"{r.action_type} - {r.model_name} ({r.record_name or r.record_id})"

    @api.model
    def get_sensitive_fields(self):
        """Get list of sensitive fields to track.

        Reads from ir.config_parameter 'l10n_si_audit_trail.sensitive_fields'
        if set, otherwise uses DEFAULT_SENSITIVE_FIELDS.
        """
        param = self.env['ir.config_parameter'].sudo().get_param(
            'l10n_si_audit_trail.sensitive_fields'
        )
        if param:
            try:
                fields_list = json.loads(param)
                if isinstance(fields_list, list):
                    return fields_list
            except (json.JSONDecodeError, TypeError):
                pass
        return DEFAULT_SENSITIVE_FIELDS

    @api.model
    def _get_request_ip(self):
        """Extract client IP from current HTTP request."""
        try:
            from odoo.http import request
            if request and hasattr(request, 'httprequest'):
                environ = request.httprequest.environ
                forwarded = environ.get('HTTP_X_FORWARDED_FOR', '')
                if forwarded:
                    return forwarded.split(',')[0].strip()
                return environ.get('REMOTE_ADDR', '')
        except Exception:
            pass
        return ''

    @api.model
    def log_action(self, model_name, record_id, record_name, action_type,
                   field_name=None, old_value=None, new_value=None):
        """Create an audit trail entry.

        Args:
            model_name: Model technical name (e.g., 'account.move')
            record_id: Record ID
            record_name: Display name of the record
            action_type: 'create', 'write', or 'unlink'
            field_name: Field that changed (None for create/unlink)
            old_value: Previous value (None for create)
            new_value: New value (None for unlink)
        """
        try:
            self.sudo().create({
                'model_name': model_name,
                'record_id': record_id,
                'record_name': record_name or '',
                'action_type': action_type,
                'field_name': field_name or '',
                'old_value': str(old_value) if old_value is not None else '',
                'new_value': str(new_value) if new_value is not None else '',
                'ip_address': self._get_request_ip(),
            })
        except Exception as e:
            _logger.error('Audit trail: failed to log %s on %s:%s — %s',
                         action_type, model_name, record_id, e)


class Base(models.AbstractModel):
    _inherit = "base"

    def write(self, vals):
        """Log changes to sensitive fields."""
        sensitive = self.env['l10n_si.audit.trail'].get_sensitive_fields()
        tracked = [f for f in sensitive if f in vals]
        if tracked and self.env.user and not self.env.context.get("no_audit"):
            for record in self:
                for field in tracked:
                    old = getattr(record, field, None)
                    new = vals[field]
                    if old != new:
                        self.env["l10n_si.audit.trail"].log_action(
                            model_name=self._name,
                            record_id=record.id,
                            record_name=record.display_name,
                            action_type="write",
                            field_name=field,
                            old_value=old,
                            new_value=new,
                        )
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Log creation of records with sensitive fields."""
        records = super().create(vals_list)
        sensitive = self.env['l10n_si.audit.trail'].get_sensitive_fields()
        if self.env.user and not self.env.context.get("no_audit"):
            for record in records:
                # Check if any sensitive field has a value
                has_sensitive = any(
                    getattr(record, f, None) for f in sensitive
                )
                if has_sensitive:
                    self.env["l10n_si.audit.trail"].log_action(
                        model_name=self._name,
                        record_id=record.id,
                        record_name=record.display_name,
                        action_type="create",
                    )
        return records

    def unlink(self):
        """Log deletion of records with sensitive fields."""
        if self.env.user and not self.env.context.get("no_audit"):
            for record in self:
                self.env["l10n_si.audit.trail"].log_action(
                    model_name=self._name,
                    record_id=record.id,
                    record_name=record.display_name,
                    action_type="unlink",
                )
        return super().unlink()
