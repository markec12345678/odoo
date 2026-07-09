{
    'name': 'AI Chatbot Widget (SI)',
    'summary': 'Website chat widget powered by AI Concierge',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'description': """
AI Chatbot Widget (SI)
======================

Adds a floating chat widget to the website that connects to the AI Concierge.
Guests can ask questions about the hotel, services, check-in times, etc.

Features:
* Floating chat bubble in bottom-right corner
* Real-time AI responses (via l10n_si_ai_concierge)
* Conversation history per session
* Multi-language support
* Customizable welcome message
* Mobile responsive

Requires:
* l10n_si_ai_concierge (for AI backend)
* website (for frontend display)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['website', 'l10n_si_ai_concierge', 'account'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'qweb': [
        'static/src/xml/chatbot_widget.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'l10n_si_chatbot_widget/static/src/js/chatbot_widget.js',
            'l10n_si_chatbot_widget/static/src/css/chatbot_widget.css',
        ],
    },
    'installable': True,
}
