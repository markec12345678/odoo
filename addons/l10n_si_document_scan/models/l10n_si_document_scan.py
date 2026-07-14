# -*- coding: utf-8 -*-
"""Document scan model — posnetek osebnega dokumenta z OCR."""
import base64
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# MRZ (Machine Readable Zone) patterns per ICAO 9303
# TD1 format (ID cards): 3 lines × 30 chars
# TD3 format (passports): 2 lines × 44 chars
MRZ_TD1_PATTERN = re.compile(
    r'^(I|[A-Z]{3})[A-Z<]{1,27}\n'  # Line 1
    r'([A-Z0-9<]{9})([0-9])([A-Z<]{15})\n'  # Line 2: doc number + check digit + nationality + DOB + sex + expiry + personal number
    r'([A-Z0-9<]{30})$',  # Line 3: names
)
MRZ_TD3_PATTERN = re.compile(
    r'^P([A-Z]{3})([A-Z<]{39})\n'  # Line 1: passport + nationality + names
    r'([A-Z0-9<]{9})([0-9])([A-Z]{3})([0-9]{6})([0-9])([MFX<])([0-9]{6})([0-9])',  # Line 2
)


class L10nSiDocumentScan(models.Model):
    _name = 'l10n_si.document.scan'
    _description = 'SI Document Scan — OCR posnetek'
    _order = 'create_date DESC'
    _rec_name = 'scan_number'

    scan_number = fields.Char(string='Številka', copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', string='Gost')
    guest_registration_id = fields.Many2one(
        'l10n_si.etourism.guest.registration', string='eTurizem prijava',
        ondelete='set null',
        help='Povezana AJPES prijava — samodejno izpolnjena iz OCR',
    )
    document_type = fields.Selection(
        selection=[('passport', 'Potni list (TD3)'),
                   ('id_card', 'Osebna izkaznica (TD1)'),
                   ('driver_license', 'Vozni list'),
                   ('other', 'Drugo')],
        default='id_card',
        required=True,
        string='Vrsta dokumenta',
    )
    document_image = fields.Binary(
        string='Slika dokumenta', required=True,
        help='Posnetek/fotografija osebnega dokumenta',
    )
    document_image_filename = fields.Char(string='Ime datoteke')

    # OCR extracted fields (auto-filled)
    ocr_status = fields.Selection(
        selection=[('pending', 'Čaka na OCR'),
                   ('processing', 'OCR v teku'),
                   ('done', 'OCR zaključen'),
                   ('failed', 'OCR neuspešen'),
                   ('manual', 'Ročno vneseno')],
        default='pending',
        required=True,
        string='Status OCR',
        tracking=True,
    )
    ocr_raw_text = fields.Text(string='Surovi OCR tekst', readonly=True)
    ocr_mrz = fields.Text(string='MRZ (Machine Readable Zone)', readonly=True)

    # Extracted guest data
    first_name = fields.Char(string='Ime')
    last_name = fields.Char(string='Priimek')
    document_number = fields.Char(string='Številka dokumenta')
    birth_date = fields.Date(string='Datum rojstva')
    sex = fields.Selection([('M', 'Moški'), ('F', 'Ženski'), ('X', 'Drugo')], string='Spol')
    nationality_country_id = fields.Many2one('res.country', string='Državljanstvo')
    document_country_id = fields.Many2one('res.country', string='Država izdajatelja')
    document_expiry = fields.Date(string='Datum poteka dokumenta')
    personal_number = fields.Char(string='Osebna številka')

    # Validation
    document_expired = fields.Boolean(
        compute='_compute_document_expired', store=True,
        string='Dokument potekel',
    )
    validation_warnings = fields.Text(string='Opozorila', readonly=True)

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('scan_number', '/') == '/':
                vals['scan_number'] = self.env['ir.sequence'].next_by_code(
                    'l10n_si.document.scan'
                ) or '/'
        return super().create(vals_list)

    @api.depends('document_expiry')
    def _compute_document_expired(self):
        today = fields.Date.today()
        for scan in self:
            scan.document_expired = bool(
                scan.document_expiry and scan.document_expiry < today
            )

    def action_run_ocr(self):
        """Zažene AI OCR na sliki dokumenta.

        Uporablja AI Core (GLM 5.1 vision) ali fallback na MRZ parsing.
        """
        for scan in self:
            if not scan.document_image:
                raise UserError(_('Najprej naložite sliko dokumenta.'))

            scan.ocr_status = 'processing'
            scan.validation_warnings = ''

            # Try AI Core with vision capabilities
            AiCore = self.env.get('l10n_si.ai.core.route')
            if AiCore:
                try:
                    # Encode image as base64 data URL
                    image_data = base64.b64decode(scan.document_image)
                    image_b64 = base64.b64encode(image_data).decode()

                    prompt = (
                        "Preberi vse podatke s slike osebnega dokumenta.\n"
                        "Vrni JSON format:\n"
                        '{"first_name": "", "last_name": "", '
                        '"document_number": "", "birth_date": "YYYY-MM-DD", '
                        '"sex": "M/F/X", "nationality": "ISO 3166 code", '
                        '"document_country": "ISO 3166 code", '
                        '"document_expiry": "YYYY-MM-DD", '
                        '"mrz": "full MRZ text if visible", '
                        '"document_type": "passport/id_card"}'
                    )

                    result = AiCore.generate(
                        messages=[{'role': 'user', 'content': prompt}],
                        task_type='reasoning',
                        system_prompt='Si OCR sistem za branjenje osebnih '
                                      'dokumentov. Prebereš MRZ in vidna '
                                      'polja iz slike potnega lista ali '
                                      'osebne izkaznice. Vrneš JSON.',
                        source_module='document_scan',
                    )

                    if result.get('success') and result.get('response'):
                        scan._parse_ocr_response(result['response'])
                        scan.ocr_status = 'done'
                        _logger.info(
                            'Document scan OCR: %s via %s/%s',
                            scan.scan_number, result.get('provider'),
                            result.get('model'),
                        )
                        scan._validate_extracted_data()
                        continue
                except Exception as e:
                    _logger.warning('Document scan AI OCR failed: %s', e)

            # Fallback: try MRZ parsing from raw text (if available)
            scan._try_mrz_fallback()
            scan._validate_extracted_data()

    def _parse_ocr_response(self, response_text):
        """Parse JSON response from AI OCR."""
        import json
        try:
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
            else:
                data = json.loads(response_text)

            self.ocr_raw_text = response_text
            self.ocr_mrz = data.get('mrz', '')
            self.first_name = data.get('first_name', '').title()
            self.last_name = data.get('last_name', '').title()
            self.document_number = data.get('document_number', '').upper()

            birth = data.get('birth_date', '')
            if birth and len(birth) >= 10:
                self.birth_date = birth[:10]

            sex = data.get('sex', '').upper()
            if sex in ('M', 'F', 'X'):
                self.sex = sex

            expiry = data.get('document_expiry', '')
            if expiry and len(expiry) >= 10:
                self.document_expiry = expiry[:10]

            # Countries
            nat_code = data.get('nationality', '').upper()
            doc_code = data.get('document_country', '').upper()
            if nat_code:
                country = self.env['res.country'].search(
                    [('code', '=', nat_code)], limit=1)
                if country:
                    self.nationality_country_id = country.id
            if doc_code:
                country = self.env['res.country'].search(
                    [('code', '=', doc_code)], limit=1)
                if country:
                    self.document_country_id = country.id

            # Document type
            doc_type = data.get('document_type', '').lower()
            if 'passport' in doc_type:
                self.document_type = 'passport'
            elif 'id' in doc_type or 'card' in doc_type:
                self.document_type = 'id_card'

        except (json.JSONDecodeError, ValueError) as e:
            _logger.warning('Document scan: JSON parse failed: %s', e)
            self.ocr_raw_text = response_text
            self._try_mrz_fallback()

    def _try_mrz_fallback(self):
        """Try to parse MRZ from raw text."""
        if not self.ocr_raw_text:
            self.ocr_status = 'failed'
            self.validation_warnings = 'OCR ni uspel — vnesite podatke ročno.'
            return

        text = self.ocr_raw_text.upper().replace(' ', '<')
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) >= 25]

        # Try TD3 (passport — 2 lines × 44 chars)
        if len(lines) >= 2 and lines[0].startswith('P'):
            match = MRZ_TD3_PATTERN.match('\n'.join(lines[:2]))
            if match:
                nationality_code = match.group(1)
                names = match.group(2).replace('<', ' ').strip()
                doc_num = match.group(3)
                country_code = match.group(5)
                dob = match.group(6)  # YYMMDD
                sex_char = match.group(8)
                expiry = match.group(9)  # YYMMDD

                name_parts = names.split(' ', 1)
                self.last_name = name_parts[0].title()
                self.first_name = name_parts[1].title() if len(name_parts) > 1 else ''
                self.document_number = doc_num
                self.sex = sex_char if sex_char in ('M', 'F', 'X') else False
                self._parse_mrz_date(dob, 'birth_date')
                self._parse_mrz_date(expiry, 'document_expiry')

                country = self.env['res.country'].search(
                    [('code', '=', country_code)], limit=1)
                if country:
                    self.document_country_id = country.id
                    self.nationality_country_id = country.id

                self.ocr_mrz = '\n'.join(lines[:2])
                self.ocr_status = 'done'
                return

        # Try TD1 (ID card — 3 lines × 30 chars)
        if len(lines) >= 3:
            match = MRZ_TD1_PATTERN.match('\n'.join(lines[:3]))
            if match:
                doc_num = match.group(2)
                country_code = match.group(4) if len(match.groups()) >= 4 else ''
                names = match.group(5).replace('<', ' ').strip() if len(match.groups()) >= 5 else ''

                name_parts = names.split(' ', 1)
                self.last_name = name_parts[0].title()
                self.first_name = name_parts[1].title() if len(name_parts) > 1 else ''
                self.document_number = doc_num

                self.ocr_mrz = '\n'.join(lines[:3])
                self.ocr_status = 'done'
                return

        self.ocr_status = 'failed'
        self.validation_warnings = 'MRZ ni najden — vnesite podatke ročno.'

    def _parse_mrz_date(self, date_str, field_name):
        """Parse YYMMDD from MRZ to Date."""
        if len(date_str) == 6:
            try:
                yy = int(date_str[:2])
                mm = int(date_str[2:4])
                dd = int(date_str[4:6])
                # Assume 2000+ for birth dates < 30, 1900+ for >= 30
                year = 2000 + yy if yy < 30 else 1900 + yy
                setattr(self, field_name, fields.Date.to_date(f'{year}-{mm:02d}-{dd:02d}'))
            except (ValueError, IndexError):
                pass

    def _validate_extracted_data(self):
        """Validate extracted data and set warnings."""
        warnings = []
        if not self.first_name:
            warnings.append('Ime manjka')
        if not self.last_name:
            warnings.append('Priimek manjka')
        if not self.document_number:
            warnings.append('Številka dokumenta manjka')
        if not self.birth_date:
            warnings.append('Datum rojstva manjka')
        if self.document_expired:
            warnings.append('⚠️ DOKUMENT JE POTEKEL!')
        if not self.nationality_country_id:
            warnings.append('Državljanstvo manjka')

        self.validation_warnings = '\n'.join(warnings) if warnings else '✅ Vsi podatki veljavni'

    def action_create_guest_registration(self):
        """Ustvari eTurizem prijavo iz OCR podatkov."""
        self.ensure_one()
        if self.ocr_status != 'done':
            raise UserError(_('Najprej zaženite OCR.'))

        if not self.first_name or not self.last_name:
            raise UserError(_('Ime in priimek sta obvezna.'))

        # Poišči ali ustvari partnerja
        partner = self.partner_id
        if not partner:
            partner = self.env['res.partner'].search([
                ('name', 'ilike', f'{self.first_name} {self.last_name}'),
            ], limit=1)
        if not partner:
            partner = self.env['res.partner'].create({
                'firstname': self.first_name,
                'lastname': self.last_name,
                'name': f'{self.first_name} {self.last_name}',
                'country_id': self.nationality_country_id.id if self.nationality_country_id else False,
            })

        # Map document type to eTourism format
        doc_type_map = {
            'passport': 'potni_list',
            'id_card': 'osebna_izkaznica',
            'driver_license': 'vozni_list',
            'other': 'drugo',
        }

        # Ustvari eTurizem prijavo
        registration = self.env['l10n_si.etourism.guest.registration'].create({
            'partner_id': partner.id,
            'guest_first_name': self.first_name,
            'guest_last_name': self.last_name,
            'guest_birth_date': self.birth_date,
            'guest_sex': self.sex or False,
            'guest_citizenship_id': self.nationality_country_id.id if self.nationality_country_id else False,
            'guest_birth_country_id': self.nationality_country_id.id if self.nationality_country_id else False,
            'guest_document_type': doc_type_map.get(self.document_type, 'drugo'),
            'guest_document_number': self.document_number,
            'guest_document_country_id': self.document_country_id.id if self.document_country_id else False,
            'establishment_id': self.env.company.l10n_si_etourism_establishment_id.id if hasattr(self.env.company, 'l10n_si_etourism_establishment_id') else False,
        })

        self.guest_registration_id = registration.id
        self.partner_id = partner.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('eTurizem prijava'),
            'res_model': 'l10n_si.etourism.guest.registration',
            'res_id': registration.id,
            'view_mode': 'form',
            'target': 'current',
        }
