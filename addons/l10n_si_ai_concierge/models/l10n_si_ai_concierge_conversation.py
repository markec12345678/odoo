# -*- coding: utf-8 -*-
"""Pogovor med gostom in AI."""
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class L10nSiAiConciergeConversation(models.Model):
    _name = 'l10n_si.ai.concierge.conversation'
    _description = 'Slovenian AI Concierge Conversation'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    config_id = fields.Many2one('l10n_si.ai.concierge.config', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Gost')
    user_id = fields.Many2one('res.users', string='Internal user (if staff)')
    company_id = fields.Many2one(related='config_id.company_id', store=True)

    channel = fields.Selection(
        selection=[('website', 'Spletni chat'),
                   ('whatsapp', 'WhatsApp'),
                   ('email', 'E-pošta')],
        default='website',
        required=True,
    )

    state = fields.Selection(
        selection=[('active', 'Aktiven'),
                   ('ended', 'Zaključen'),
                   ('escalated', 'Prenesen na človeka')],
        default='active',
        tracking=True,
    )

    message_ids = fields.One2many(
        'l10n_si.ai.concierge.message', 'conversation_id', string='Sporočila',
    )
    message_count = fields.Integer(compute='_compute_count', store=False)

    # Kontekst
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Trenutni folio gosta')
    summary = fields.Text(readonly=True, copy=False,
                            help='AI povzetek pogovora ob zaključku.')

    @api.depends('partner_id', 'create_date')
    def _compute_name(self):
        for c in self:
            name = c.partner_id.name or 'Anonimni gost'
            date = fields.Datetime.from_string(c.create_date).strftime('%d.%m.%Y %H:%M') if c.create_date else ''
            c.name = f'{name} ({date})'

    def _compute_count(self):
        for c in self:
            c.message_count = len(c.message_ids)

    def action_end(self):
        """Zaključi pogovor - AI naredi povzetek."""
        for c in self:
            c._generate_summary()
            c.state = 'ended'

    def action_escalate(self):
        """Prenesi na človeka - obvesti recepcijo."""
        self.write({'state': 'escalated'})

    def _generate_summary(self):
        """AI generira povzetek pogovora."""
        # V produkciji: klic AI API-ja s celotno zgodovino
        messages_text = '\n'.join(
            f'{m.role}: {m.content}' for m in self.message_ids
        )
        # Zaenkrat preprosto shranimo zadnje sporočilo
        self.summary = f'Pogovor z {len(self.message_ids)} sporočili.'

    def send_message(self, content, role='user'):
        """Dodaj sporočilo in pridobi AI odgovor."""
        self.ensure_one()
        msg = self.env['l10n_si.ai.concierge.message'].create({
            'conversation_id': self.id,
            'role': role,
            'content': content,
        })

        if role == 'user':
            # Klic AI za odgovor
            ai_response = self._call_ai_for_response(content)
            self.env['l10n_si.ai.concierge.message'].create({
                'conversation_id': self.id,
                'role': 'assistant',
                'content': ai_response,
            })
            return ai_response
        return content

    def _call_ai_for_response(self, user_message):
        """Klici AI backend za odgovor.

        Poskusi pravi LLM (ZAI/OpenAI/Anthropic/Local). Če ni konfiguriran
        ali pa klic spodleti, uporabi rule-based fallback.
        """
        from .ai_client import get_ai_client, AIAuthError, AIRequestError, AIRateLimitError, Message

        cfg = self.config_id

        # Zberi kontekst iz knowledge base
        context = ''
        for article in cfg.knowledge_article_ids:
            context += f'\n--- {article.name} ---\n{article.body}\n'

        # Poskusi pravi LLM, če je API ključ konfiguriran
        if cfg.api_key:
            try:
                client = get_ai_client(
                    backend=cfg.ai_backend,
                    api_key=cfg.api_key,
                    model=cfg.model_name,
                )
                messages = [Message('system', cfg.system_prompt + context)]
                recent_msgs = self.message_ids[-10:]
                for msg in recent_msgs:
                    if msg.role in ('user', 'assistant'):
                        messages.append(Message(msg.role, msg.content))
                messages.append(Message('user', user_message))

                response = client.generate_response(
                    messages=messages,
                    temperature=cfg.temperature,
                    max_tokens=cfg.max_tokens,
                )
                return response
            except AIAuthError as e:
                _logger.warning('AI auth failed: %s — using rule-based fallback', e)
            except AIRateLimitError as e:
                _logger.warning('AI rate limited: %s — using rule-based fallback', e)
            except AIRequestError as e:
                _logger.warning('AI request failed: %s — using rule-based fallback', e)
            except Exception as e:
                _logger.exception('AI call failed: %s — using rule-based fallback', e)

        # Rule-based fallback (deluje tudi brez AI ključa)
        msg_lower = user_message.lower()

        if 'wifi' in msg_lower or 'internet' in msg_lower:
            return 'Geslo za WiFi je: Gost2025. Omrežje: Hotel_Guest_WiFi.'
        elif 'zajtrk' in msg_lower:
            return 'Zajtrk je vsak dan od 7:00 do 10:00 v restavraciji v pritličju.'
        elif 'check' in msg_lower or 'odjava' in msg_lower or 'prijava' in msg_lower:
            return 'Prijava je od 14:00, odjava do 11:00. Če želite pozno odjavo, prosim obvestite recepcijo.'
        elif 'bazen' in msg_lower or 'wellness' in msg_lower or 'sauna' in msg_lower:
            return 'Wellness center je odprt od 9:00 do 21:00. Masaže po predhodni rezervaciji.'
        elif 'hvala' in msg_lower:
            return 'Prosim! Še kaj lahko pomagam?'
        elif 'recepcija' in msg_lower or 'človek' in msg_lower or 'operater' in msg_lower:
            self.action_escalate()
            return 'Prenosam vas na recepcijo. Prosimo počakajte trenutek.'
        else:
            return 'Razumem. Ali lahko malo bolj natančno opišete, kar potrebujete? Lahko pomagam z informacijami o sobi, zajtrku, wellnessu ali lokalnih atrakcijah.'


class L10nSiAiConciergeMessage(models.Model):
    _name = 'l10n_si.ai.concierge.message'
    _description = 'Slovenian AI Concierge Message'
    _order = 'create_date'

    conversation_id = fields.Many2one('l10n_si.ai.concierge.conversation', required=True, ondelete='cascade')
    role = fields.Selection(
        selection=[('user', 'Gost'),
                   ('assistant', 'AI'),
                   ('system', 'Sistem'),
                   ('human', 'Recepcija')],
        required=True,
    )
    content = fields.Text(required=True)
    tokens_used = fields.Integer(readonly=True, copy=False)
    create_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
