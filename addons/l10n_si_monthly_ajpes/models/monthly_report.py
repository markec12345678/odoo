# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import calendar
import logging
from datetime import date, datetime, timedelta
from io import BytesIO, StringIO

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MonthlyAjpessReport(models.Model):
    """Monthly AJPES eTurizem report — aggregates all guest registrations
    for a given month and establishment.
    """
    _name = "l10n_si.monthly.ajpes.report"
    _description = "Monthly AJPES eTurizem Report"
    _inherit = ["mail.thread"]
    _order = "year desc, month desc, establishment_id"

    name = fields.Char(compute="_compute_name", store=True)
    establishment_id = fields.Many2one(
        "l10n_si.etourism.establishment",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    company_id = fields.Many2one(
        related="establishment_id.company_id",
        store=True,
    )
    year = fields.Integer(required=True, default=lambda self: fields.Date.today().year)
    month = fields.Integer(
        required=True,
        default=lambda self: fields.Date.today().month,
    )
    month_name = fields.Char(compute="_compute_name", store=True)

    # --- State ------------------------------------------------------------
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generated", "Generated"),
            ("submitted", "Submitted to AJPES"),
            ("confirmed", "Confirmed by AJPES"),
            ("error", "Error"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    version = fields.Integer(
        default=1,
        help="Incremented on each re-generation (AJPES allows corrections).",
    )

    # --- Aggregated statistics -------------------------------------------
    total_arrivals = fields.Integer(
        readonly=True,
        help="Number of guests who arrived in this month.",
    )
    total_departures = fields.Integer(
        readonly=True,
        help="Number of guests who departed in this month.",
    )
    total_nights = fields.Integer(
        readonly=True,
        help="Sum of all nights stayed by guests who arrived this month.",
    )
    total_foreigners = fields.Integer(readonly=True)
    total_domestic = fields.Integer(readonly=True, help="Slovenian citizens.")
    avg_stay_nights = fields.Float(
        readonly=True,
        help="Average length of stay in nights.",
    )
    registration_count = fields.Integer(
        readonly=True,
        help="Total number of guest registration records included.",
    )

    # --- Country breakdown (stored as JSON) ------------------------------
    country_breakdown_json = fields.Text(readonly=True)
    purpose_breakdown_json = fields.Text(readonly=True)
    reservation_source_breakdown_json = fields.Text(readonly=True)

    # --- Files ------------------------------------------------------------
    xml_file = fields.Binary(readonly=True, string="XML Report")
    xml_filename = fields.Char(readonly=True)
    csv_file = fields.Binary(readonly=True, string="CSV Summary")
    csv_filename = fields.Char(readonly=True)
    ajpes_submission_id = fields.Char(readonly=True)
    ajpes_response = fields.Text(readonly=True)
    error_message = fields.Text(readonly=True)

    # --- Audit ------------------------------------------------------------
    generated_by = fields.Many2one("res.users", readonly=True)
    generated_on = fields.Datetime(readonly=True)
    submitted_by = fields.Many2one("res.users", readonly=True)
    submitted_on = fields.Datetime(readonly=True)

    # --- Related records --------------------------------------------------
    registration_ids = fields.Many2many(
        "l10n_si.etourism.guest.registration",
        "monthly_ajpes_report_registration_rel",
        "report_id",
        "registration_id",
        string="Included Registrations",
        readonly=True,
    )

    # --- Constraints ------------------------------------------------------
    _sql_constraints = [
        (
            "unique_establishment_month",
            "UNIQUE(establishment_id, year, month, version)",
            "A report for this establishment/month/version already exists.",
        ),
        (
            "month_range",
            "CHECK (month BETWEEN 1 AND 12)",
            "Month must be between 1 and 12.",
        ),
        (
            "year_range",
            "CHECK (year BETWEEN 2000 AND 2100)",
            "Year must be between 2000 and 2100.",
        ),
    ]

    @api.depends("establishment_id", "year", "month")
    def _compute_name(self):
        month_names = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        for r in self:
            est = r.establishment_id.name or ""
            r.month_name = month_names[r.month] if 1 <= r.month <= 12 else ""
            r.name = f"{est} — {r.month_name} {r.year}"

    # --- Generation -------------------------------------------------------
    def action_generate(self):
        """Generate the report: aggregate data, build XML + CSV."""
        for report in self:
            report._aggregate_data()
            report._generate_xml()
            report._generate_csv()
            report.write(
                {
                    "state": "generated",
                    "generated_by": self.env.user.id,
                    "generated_on": fields.Datetime.now(),
                    "error_message": False,
                }
            )
            report._send_notification_email()
        return True

    def _aggregate_data(self):
        """Aggregate all guest registrations for this month."""
        self.ensure_one()
        # Compute date range
        last_day = calendar.monthrange(self.year, self.month)[1]
        date_start = datetime(self.year, self.month, 1, 0, 0, 0)
        date_end = datetime(self.year, self.month, last_day, 23, 59, 59)
        # Find all registrations for this establishment that arrived in the month
        registrations = self.env["l10n_si.etourism.guest.registration"].search(
            [
                ("establishment_id", "=", self.establishment_id.id),
                ("arrival_date", ">=", date_start),
                ("arrival_date", "<=", date_end),
                ("ajpes_status", "in", ["submitted", "deregistered"]),
            ]
        )
        # Aggregate
        total_arrivals = len(registrations)
        total_nights = sum(r.nights or 0 for r in registrations)
        slovenia = self.env.ref("base.si", raise_if_not_found=False) or \
            self.env["res.country"].search([("code", "=", "SI")], limit=1)
        total_domestic = len(
            registrations.filtered(
                lambda r: r.guest_citizenship_id == slovenia
            )
        )
        total_foreigners = total_arrivals - total_domestic
        # Departures: those with departure_date in this month
        total_departures = len(
            registrations.filtered(
                lambda r: r.departure_date and date_start <= r.departure_date <= date_end
            )
        )
        avg_stay = (total_nights / total_arrivals) if total_arrivals else 0.0
        # Country breakdown
        country_map = {}
        for reg in registrations:
            country = reg.guest_citizenship_id
            key = country.name if country else "Unknown"
            country_map[key] = country_map.get(key, 0) + 1
        # Purpose breakdown
        purpose_map = {}
        for reg in registrations:
            key = reg.purpose or "unspecified"
            purpose_map[key] = purpose_map.get(key, 0) + 1
        # Reservation source breakdown
        source_map = {}
        for reg in registrations:
            key = reg.reservation_source or "unspecified"
            source_map[key] = source_map.get(key, 0) + 1
        import json

        self.write(
            {
                "registration_ids": [(6, 0, registrations.ids)],
                "total_arrivals": total_arrivals,
                "total_departures": total_departures,
                "total_nights": total_nights,
                "total_domestic": total_domestic,
                "total_foreigners": total_foreigners,
                "avg_stay_nights": round(avg_stay, 2),
                "registration_count": total_arrivals,
                "country_breakdown_json": json.dumps(country_map, ensure_ascii=False),
                "purpose_breakdown_json": json.dumps(purpose_map, ensure_ascii=False),
                "reservation_source_breakdown_json": json.dumps(source_map, ensure_ascii=False),
            }
        )

    def _generate_xml(self):
        """Generate the AJPES XML report (TURIZEM format)."""
        self.ensure_one()
        registrations = self.registration_ids
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<TURIZEM xmlns="http://www.ajpes.si/eTurizem">',
            '  <Header>',
            f'    <EstablishmentMID>{self.establishment_id.mid or ""}</EstablishmentMID>',
            f'    <EstablishmentSIFNAS>{self.establishment_id.sifnas or ""}</EstablishmentSIFNAS>',
            f'    <ReportYear>{self.year}</ReportYear>',
            f'    <ReportMonth>{self.month:02d}</ReportMonth>',
            f'    <Version>{self.version}</Version>',
            f'    <GeneratedOn>{fields.Datetime.now().isoformat()}</GeneratedOn>',
            f'    <TotalArrivals>{self.total_arrivals}</TotalArrivals>',
            f'    <TotalNights>{self.total_nights}</TotalNights>',
            f'    <TotalDomestic>{self.total_domestic}</TotalDomestic>',
            f'    <TotalForeigners>{self.total_foreigners}</TotalForeigners>',
            '  </Header>',
            '  <Guests>',
        ]
        for reg in registrations:
            xml_parts.append('    <Guest>')
            xml_parts.append(f'      <FirstName>{self._xml_escape(reg.guest_first_name or "")}</FirstName>')
            xml_parts.append(f'      <LastName>{self._xml_escape(reg.guest_last_name or "")}</LastName>')
            if reg.guest_birth_date:
                xml_parts.append(f'      <BirthDate>{reg.guest_birth_date.isoformat()}</BirthDate>')
            xml_parts.append(f'      <Sex>{reg.guest_sex or "X"}</Sex>')
            if reg.guest_citizenship_id:
                xml_parts.append(f'      <Citizenship>{reg.guest_citizenship_id.code}</Citizenship>')
            xml_parts.append(f'      <DocumentType>{reg.guest_document_type or "P"}</DocumentType>')
            xml_parts.append(f'      <DocumentNumber>{self._xml_escape(reg.guest_document_number or "")}</DocumentNumber>')
            xml_parts.append(f'      <ArrivalDate>{reg.arrival_date.isoformat() if reg.arrival_date else ""}</ArrivalDate>')
            if reg.departure_date:
                xml_parts.append(f'      <DepartureDate>{reg.departure_date.isoformat()}</DepartureDate>')
            xml_parts.append(f'      <Nights>{reg.nights or 0}</Nights>')
            xml_parts.append(f'      <Purpose>{reg.purpose or "L"}</Purpose>')
            xml_parts.append(f'      <Transport>{reg.transport or "Z"}</Transport>')
            if reg.country_of_origin_id:
                xml_parts.append(f'      <CountryOfOrigin>{reg.country_of_origin_id.code}</CountryOfOrigin>')
            xml_parts.append(f'      <ReservationSource>{reg.reservation_source or "O"}</ReservationSource>')
            xml_parts.append(f'      <AJPESStatus>{reg.ajpes_status}</AJPESStatus>')
            xml_parts.append('    </Guest>')
        xml_parts.append('  </Guests>')
        xml_parts.append('</TURIZEM>')
        xml_content = "\n".join(xml_parts)
        xml_bytes = xml_content.encode("utf-8")
        filename = f"ajpes_turizem_{self.establishment_id.mid or 'est'}_{self.year}_{self.month:02d}_v{self.version}.xml"
        self.write(
            {
                "xml_file": base64.b64encode(xml_bytes).decode(),
                "xml_filename": filename,
            }
        )

    def _generate_csv(self):
        """Generate a CSV summary for human review."""
        self.ensure_one()
        import csv

        output = StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(
            [
                "First Name", "Last Name", "Birth Date", "Sex",
                "Citizenship", "Document Type", "Document Number",
                "Arrival Date", "Departure Date", "Nights",
                "Purpose", "Transport", "Country of Origin",
                "Reservation Source", "AJPES Status",
            ]
        )
        for reg in self.registration_ids:
            writer.writerow(
                [
                    reg.guest_first_name or "",
                    reg.guest_last_name or "",
                    reg.guest_birth_date.isoformat() if reg.guest_birth_date else "",
                    reg.guest_sex or "",
                    reg.guest_citizenship_id.code if reg.guest_citizenship_id else "",
                    reg.guest_document_type or "",
                    reg.guest_document_number or "",
                    reg.arrival_date.isoformat() if reg.arrival_date else "",
                    reg.departure_date.isoformat() if reg.departure_date else "",
                    reg.nights or 0,
                    reg.purpose or "",
                    reg.transport or "",
                    reg.country_of_origin_id.code if reg.country_of_origin_id else "",
                    reg.reservation_source or "",
                    reg.ajpes_status or "",
                ]
            )
        csv_content = output.getvalue()
        csv_bytes = csv_content.encode("utf-8")
        filename = f"ajpes_summary_{self.establishment_id.mid or 'est'}_{self.year}_{self.month:02d}_v{self.version}.csv"
        self.write(
            {
                "csv_file": base64.b64encode(csv_bytes).decode(),
                "csv_filename": filename,
            }
        )

    @staticmethod
    def _xml_escape(text):
        """Escape XML special characters."""
        if not text:
            return ""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    # --- Submission -------------------------------------------------------
    def action_submit_to_ajpes(self):
        """Submit the report to AJPES via the eTurizem API.

        This is a placeholder — actual submission requires SI-PASS credentials
        and the AJPES test/production endpoint configuration.
        """
        for report in self:
            if report.state != "generated":
                raise UserError(_("Report must be in 'Generated' state to submit."))
            if not report.xml_file:
                raise UserError(_("No XML file found. Generate the report first."))
            try:
                # In production, this would call the AJPES API
                # For now, we mark as submitted and record a placeholder
                report.write(
                    {
                        "state": "submitted",
                        "ajpes_submission_id": f"AJPES-{report.year}{report.month:02d}-{report.version}",
                        "submitted_by": self.env.user.id,
                        "submitted_on": fields.Datetime.now(),
                        "ajpes_response": "Submitted via eTurizem API (placeholder).",
                    }
                )
                report.message_post(
                    body=_("Report submitted to AJPES. Submission ID: %s")
                    % report.ajpes_submission_id,
                )
            except Exception as e:  # noqa: BLE001
                report.write(
                    {
                        "state": "error",
                        "error_message": str(e)[:500],
                    }
                )
        return True

    def action_confirm(self):
        """Manually mark as confirmed by AJPES (after receiving confirmation)."""
        for report in self:
            report.state = "confirmed"

    def action_reset_to_draft(self):
        """Reset to draft for re-generation (increments version)."""
        for report in self:
            new_version = report.version + 1
            report.write(
                {
                    "state": "draft",
                    "version": new_version,
                    "error_message": False,
                    "ajpes_submission_id": False,
                    "ajpes_response": False,
                }
            )

    # --- Email ------------------------------------------------------------
    def _send_notification_email(self):
        """Send email notification with the report attached."""
        self.ensure_one()
        if not self.company_id.email:
            return
        template = self.env.ref(
            "l10n_si_monthly_ajpes.email_template_monthly_report",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=False)

    # --- Dashboard helpers ------------------------------------------------
    def get_country_breakdown(self):
        """Return country breakdown as a list of (country, count) tuples."""
        self.ensure_one()
        import json

        if not self.country_breakdown_json:
            return []
        try:
            data = json.loads(self.country_breakdown_json)
            return sorted(data.items(), key=lambda x: x[1], reverse=True)
        except (ValueError, TypeError):
            return []

    def get_purpose_breakdown(self):
        self.ensure_one()
        import json

        if not self.purpose_breakdown_json:
            return []
        try:
            data = json.loads(self.purpose_breakdown_json)
            return sorted(data.items(), key=lambda x: x[1], reverse=True)
        except (ValueError, TypeError):
            return []

    # --- Cron -------------------------------------------------------------
    @api.model
    def _cron_generate_monthly_reports(self):
        """Called on 1st of each month — generates report for previous month."""
        today = fields.Date.today()
        # Previous month
        if today.month == 1:
            prev_year = today.year - 1
            prev_month = 12
        else:
            prev_year = today.year
            prev_month = today.month - 1
        # Find all active establishments
        establishments = self.env["l10n_si.etourism.establishment"].search(
            [("active", "=", True)]
        )
        for est in establishments:
            # Check if report already exists
            existing = self.search(
                [
                    ("establishment_id", "=", est.id),
                    ("year", "=", prev_year),
                    ("month", "=", prev_month),
                    ("version", "=", 1),
                ],
                limit=1,
            )
            if existing:
                continue
            try:
                report = self.create(
                    {
                        "establishment_id": est.id,
                        "year": prev_year,
                        "month": prev_month,
                        "version": 1,
                    }
                )
                report.action_generate()
            except Exception as e:  # noqa: BLE001
                _logger.error("Failed to generate AJPES report for %s/%d-%d: %s",
                              est.name, prev_year, prev_month, e)
