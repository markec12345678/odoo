# -*- coding: utf-8 -*-
{
    'name': 'SI/HR AI Core — Central LLM Router',
    'summary': 'Centraliziran AI router — task-based model routing z fallback chain',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'description': """
SI/HR AI Core — Central LLM Router
===================================

Centralni AI router, ki vsem modulom (AI Concierge, WhatsApp, marketing,
reports) ponuja enoten API za LLM klice.

Ključni koncepti:
1. Task-based routing — preprosta vprašanja → hiter model (GPT-4o),
   kompleksne analize → reasoning model (GLM 5.1)
2. Fallback chain — če primarni ponudnik odpove, poskusi sekundarnega
3. Token tracking — sledi porabi tokenov po modulu/ponudniku
4. Enoten API — vsi moduli kličejo ai.core.generate(), ne pa direktno
   LLM ponudnika

Arhitektura:

    AI Concierge  ─┐
    WhatsApp       ├─→ AI Core ─→ LLM Router ─→ Puter (GLM 5.1)
    Marketing      │              (task-based)  ├─→ ZAI (GLM 4+)
    Reports        │              (fallback)    ├─→ OpenAI (GPT-4o)
    Other modules ─┘                            └─→ Local (Llama)

Največja vrednost projekta ni LLM model — to je znanje, ki se nabira
v bazi (knowledge articles, conversation history, guest preferences).
LLM je samo "motor za razmišljanje". Če ga jutri zamenjaš z GLM-6,
GPT-6 ali drugim modelom, ostane sistem skoraj enak.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'l10n_si_ai_concierge'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_ai_core_route_views.xml',
        'views/l10n_si_ai_core_usage_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
