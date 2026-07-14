# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class QuestionnaireController(http.Controller):
    """Public questionnaire controller — token-authenticated, no login.
    """

    def _get_response(self, token):
        if not token:
            return request.env["l10n_si.questionnaire.response"]
        return request.env["l10n_si.questionnaire.response"].sudo().search(
            [("token", "=", token)], limit=1
        )

    @http.route("/questionnaire/start/<string:token>", type="http", auth="public", website=True)
    def questionnaire_start(self, token, **kw):
        """Show the welcome screen + first section."""
        response = self._get_response(token)
        if not response:
            return request.not_found(_("Invalid or expired questionnaire link."))
        if response.state == "expired":
            return request.render("l10n_si_pre_arrival_questionnaire.expired", {})
        if response.state == "completed":
            return request.render(
                "l10n_si_pre_arrival_questionnaire.already_completed",
                {"response": response},
            )
        # Mark as started
        response.action_mark_started()
        sections = response.template_id.section_ids.sorted("sequence")
        return request.render(
            "l10n_si_pre_arrival_questionnaire.welcome",
            {
                "response": response,
                "template": response.template_id,
                "sections": sections,
            },
        )

    @http.route("/questionnaire/section/<string:token>/<int:section_idx>", type="http", auth="public", website=True)
    def questionnaire_section(self, token, section_idx, **kw):
        """Show a specific section."""
        response = self._get_response(token)
        if not response:
            return request.not_found(_("Invalid questionnaire link."))
        sections = response.template_id.section_ids.sorted("sequence")
        if section_idx < 0 or section_idx >= len(sections):
            return request.redirect(f"/questionnaire/summary/{token}")
        section = sections[section_idx]
        return request.render(
            "l10n_si_pre_arrival_questionnaire.section",
            {
                "response": response,
                "template": response.template_id,
                "section": section,
                "section_idx": section_idx,
                "total_sections": len(sections),
                "next_idx": section_idx + 1,
                "prev_idx": section_idx - 1,
            },
        )

    @http.route("/questionnaire/submit_section/<string:token>/<int:section_idx>", type="http", auth="public", website=True, methods=["POST"])
    def questionnaire_submit_section(self, token, section_idx, **kw):
        """Save answers from one section and go to the next."""
        response = self._get_response(token)
        if not response:
            return request.not_found(_("Invalid questionnaire link."))
        sections = response.template_id.section_ids.sorted("sequence")
        if section_idx < 0 or section_idx >= len(sections):
            return request.redirect(f"/questionnaire/summary/{token}")
        section = sections[section_idx]
        # Save each question's answer
        extra = {}
        if response.answers_json:
            import json
            try:
                extra = json.loads(response.answers_json)
            except (ValueError, TypeError):
                extra = {}
        for question in section.question_ids:
            field_name = f"q_{question.id}"
            value = kw.get(field_name, "").strip() if isinstance(kw.get(field_name, ""), str) else kw.get(field_name)
            if value is None or value == "":
                continue
            # If question has a storage_field, save to structured field
            if question.storage_field:
                response.write({question.storage_field: value})
            else:
                extra[str(question.id)] = value
        if extra:
            import json
            response.write({"answers_json": json.dumps(extra, ensure_ascii=False)})
        next_idx = section_idx + 1
        if next_idx >= len(sections):
            return request.redirect(f"/questionnaire/summary/{token}")
        return request.redirect(f"/questionnaire/section/{token}/{next_idx}")

    @http.route("/questionnaire/summary/<string:token>", type="http", auth="public", website=True)
    def questionnaire_summary(self, token, **kw):
        """Show summary of all answers for final review."""
        response = self._get_response(token)
        if not response:
            return request.not_found(_("Invalid questionnaire link."))
        sections = response.template_id.section_ids.sorted("sequence")
        # Build summary: for each question, get the stored answer
        summary = []
        for section in sections:
            section_data = {
                "section": section,
                "questions": [],
            }
            for q in section.question_ids:
                answer = ""
                if q.storage_field:
                    val = getattr(response, q.storage_field, "")
                    if val:
                        answer = val
                else:
                    import json
                    try:
                        extra = json.loads(response.answers_json or "{}")
                    except (ValueError, TypeError):
                        extra = {}
                    answer = extra.get(str(q.id), "")
                section_data["questions"].append({"q": q, "answer": answer})
            summary.append(section_data)
        return request.render(
            "l10n_si_pre_arrival_questionnaire.summary",
            {
                "response": response,
                "template": response.template_id,
                "summary": summary,
            },
        )

    @http.route("/questionnaire/complete/<string:token>", type="http", auth="public", website=True, methods=["POST"])
    def questionnaire_complete(self, token, **kw):
        """Final submission — mark as completed and show thank you."""
        response = self._get_response(token)
        if not response:
            return request.not_found(_("Invalid questionnaire link."))
        # Gather all structured data from kw
        structured_fields = [
            "dietary_restrictions", "allergies", "pillow_preference",
            "bed_configuration", "floor_preference", "special_occasion",
            "occasion_date", "planned_activities", "estimated_arrival_time",
            "transport_mode", "parking_needed", "communication_preference",
            "notes",
        ]
        form_data = {f: kw.get(f, "") for f in structured_fields}
        # Also include any extra fields not in the structured list
        for key, value in kw.items():
            if key not in structured_fields and not key.startswith("q_") and key != "token":
                form_data[key] = value
        response.action_complete(form_data)
        return request.render(
            "l10n_si_pre_arrival_questionnaire.thank_you",
            {
                "response": response,
                "template": response.template_id,
            },
        )

    @http.route("/questionnaire/preview/<int:template_id>", type="http", auth="user", website=True)
    def questionnaire_preview(self, template_id, **kw):
        """Admin preview of a template (login required)."""
        template = request.env["l10n_si.questionnaire.template"].browse(template_id)
        if not template.exists():
            return request.not_found(_("Template not found."))
        sections = template.section_ids.sorted("sequence")
        return request.render(
            "l10n_si_pre_arrival_questionnaire.preview",
            {
                "template": template,
                "sections": sections,
                "is_preview": True,
            },
        )
