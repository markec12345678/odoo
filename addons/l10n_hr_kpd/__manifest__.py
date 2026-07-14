# -*- coding: utf-8 -*-
{
    "name": "HR KPD (Klasus) Product Classification",
    "version": "19.0.1.0.0",
    "summary": "Croatian Klasus (KPD) statistical classification of products "
    "by activity. Required for monthly statistical reports to DZS.",
    "description": """
HR KPD (Klasus) Classification
==============================

Provides the Croatian Klasus (Klasifikacija proizvoda po djelatnostima)
classification system — the national product classification used for
statistical reporting to the Croatian Bureau of Statistics (DZS).

Klasus is based on:
- NACE (statistical classification of economic activities)
- CPA (classification of products by activity)
- PRODCOM (production statistics)

Used for:
- Monthly statistical reports (M-STAT, G-STAT)
- INTRASTAT declarations
- Tourist tax categorization
- Industry-specific reporting

This module:
1. Adds a `kpd_code_id` field on product.template and product.category
2. Provides a searchable database of KPD codes
3. Allows bulk assignment by category
4. Integrates with INTRASTAT reporting

Source: https://web.dzs.hr/App/klasus/
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Accounting/Localizations/Croatia",
    "depends": ["product"],
    "data": [
        "security/ir.model.access.csv",
        "data/kpd_code_data.xml",
        "views/kpd_code_views.xml",
        "views/product_template_views.xml",
        "views/product_category_views.xml",
        "views/kpd_menus.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
