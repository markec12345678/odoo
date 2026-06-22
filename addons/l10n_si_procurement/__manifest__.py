# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Procurement (Hoteli)',
    'summary': 'Nabava za hotele - čistila, kozmetika, hrana, napisi, dobavnice',
    'version': '19.0.1.0.0',
    'category': 'Procurement',
    'description': """
Slovenian Procurement za hotele
================================

Nabava specifična za hotelsko/restavracijsko panogo:
* Katalog artiklov po kategorijah:
  - Čistila (CRT, pralne, kuhinjske)
  - Kozmetika (šamponi, mila, vrečke)
  - Posteljnina (rjuhe, prevleke, brisače)
  - Hrana (surovine za kuhinjo)
  - Pijača (vina, piva, žganja, brezaalkoholne)
  - Pisarniški material
  - Tehnična oprema
* Dobavitelji s kontaktnimi podatki + ocenami
* Avtomatski nabavni predlogi glede na:
  - Minimum stock level (reorder point)
  - Poraba v zadnjih 30/90 dneh
  - Sezonskost (več brisač poleti, več mleka pozimi)
* Pogodbe z dobavitelji (letni okviri)
* Prejeti računi (vendor bills) z OCR
* Avtomatska primerjava cen (več dobaviteljev za isti artikel)
* Approval workflow za naročila nad X EUR
* Sprejem blaga (goods receipt) z quality check
* Integracija z warehouse (stock moves)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['purchase', 'stock', 'account', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/procurement_data.xml',
        'views/l10n_si_procurement_item_views.xml',
        'views/l10n_si_procurement_vendor_views.xml',
        'views/l10n_si_procurement_contract_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
