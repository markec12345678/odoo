# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Knowledge Base',
    'summary': 'Internal wiki with templates, FAQ, procedures — replaces Enterprise Knowledge',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Knowledge',
    'description': """
Slovenian Knowledge Base
========================

Lightweight internal wiki for:
* Postopki (procedures)
* Predloge dokumentov (document templates)
* FAQ za stranke (customer FAQ)
* Onboarding material za nove zaposlene
* Tehnična dokumentacija

Features:
* Hierarchical articles (parent/child)
* Tags + full-text search
* Visibility: public / portal / internal
* Version history (every edit tracked)
* Templates with mail-merge placeholders
* AI-powered article suggestions (optional, requires OpenAI API key)
* Mobile-responsive
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'security/knowledge_security.xml',
        'views/l10n_si_knowledge_article_views.xml',
        'views/l10n_si_knowledge_template_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
