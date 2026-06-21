# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Approvals Workflow',
    'summary': 'Multi-step approval workflows for purchases, leaves, expenses, travel',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Approvals',
    'description': """
Slovenian Approvals Workflow
=============================

Multi-step approval workflows for typical SI business documents:
* Potni nalogi (travel expenses)
* Dopusti (leave requests)
* Nakupi (purchase orders above threshold)
* Službena vozila (vehicle usage)
* Vsidani stroški (reimbursements)

Features:
* Rule-based routing: amount > X € → manager; > Y € → director
* Parallel vs sequential approval chains
* Email + in-app notifications
* Delegation (pooblastilo) when approver is absent
* SLA: auto-escalation after N days
* Full audit log
* Mobile-friendly approve/reject buttons in email
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'hr', 'hr_holidays', 'purchase', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/l10n_si_approval_rule_views.xml',
        'views/l10n_si_approval_request_views.xml',
        'views/hr_employee_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
