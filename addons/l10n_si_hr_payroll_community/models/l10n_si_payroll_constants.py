# -*- coding: utf-8 -*-
"""Slovenian payroll constants for tax year 2024/2025.

Values per official FURS publication:
https://www.fu.gov.si/seznam/5664

Update annually by Jan 15 (FURS publishes changes by then).
"""

# Tax brackets for akontacija dohodnine (monthly basis)
# Per ZDoh-2, 95. člen
TAX_BRACKETS = [
    # (limit_yearly_eur, rate_percent)
    (8_500.00,  16),
    (25_000.00, 26),
    (36_000.00, 33),
    (70_000.00, 39),
    (float('inf'), 50),
]

# Tax relief (olajšave) — ZDoh-2, 109-117. člen, letne vrednosti 2024
GENERAL_RELIEF_YEARLY = 3_500.00       # splošna olajšava
DISABILITY_RELIEF_YEARLY = 2_250.00    # za invalide
STUDENT_RELIEF_YEARLY = 2_250.00       # za dijake/študente
YOUNG_WORKER_RELIEF_YEARLY = 3_500.00  # mladi delojemalec (<30)
PENSIONER_RELIEF_YEARLY = 3_500.00     # upokojenec

# Child relief per child per year (ZDoh-2, 110. člen, 2024 values)
CHILD_RELIEF_YEARLY = {
    1: 1_124.88,
    2: 1_687.32,
    3: 2_249.76,
    4: 2_812.20,
    5: 3_374.64,
}
CHILD_RELIEF_ADDITIONAL = 1_124.88  # dodatna olajšava za vsakega naslednjega otroka

# Contributions (Prispevki) — ZPrD
EMPLOYER_CONTRIBUTIONS = {
    'pension': 8.85,    # pokojninsko
    'health': 6.36,     # zdravstveno
    'parental': 0.36,   # starševsko
    'unemployment': 0.06,  # brezposelnost
    'injury': 0.53,     # poškodbe pri delu
}
EMPLOYER_CONTRIBUTIONS_TOTAL = sum(EMPLOYER_CONTRIBUTIONS.values())  # 16.16%

EMPLOYEE_CONTRIBUTIONS = {
    'pension': 15.50,
    'health': 6.36,
    'parental': 0.10,
    'unemployment': 0.14,
}
EMPLOYEE_CONTRIBUTIONS_TOTAL = sum(EMPLOYEE_CONTRIBUTIONS.values())  # 22.10%

# Minimum bruto wage (minimalna plača) — per ZMinP
MINIMUM_BRUTO_2024 = 1_253.90
MINIMUM_BRUTO_2025 = 1_277.00

# Yearly conversion factor: 12 months + letni obračun pravilo = ~12 (no 13th salary in SI)
MONTHS_PER_YEAR = 12
