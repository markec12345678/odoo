# -*- coding: utf-8 -*-
{
    'name': 'AI Concierge Website Chat Widget',
    'summary': 'Spletni chat widget za AI Concierge na spletni strani',
    'version': '19.0.1.0.1',
    'category': 'Website',
    'description': """
AI Concierge Website Chat Widget
=================================

Prikaže plavajoči chat gumb na spletni strani ki odpre AI Concierge.

Funkcionalnosti:
* Plavajoči chat gumb v spodnjem desnem kotu
* Odpira pogovorno okno z AI asistentom
* Povezava z l10n_si_ai_concierge modulom
* Večjezičnost (SI/EN)
* Mobile responsive
* Tema po meri (barve, logotip)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['website', 'l10n_si_ai_concierge'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/chatbot_templates.xml',
    ],
    'installable': True,
}
