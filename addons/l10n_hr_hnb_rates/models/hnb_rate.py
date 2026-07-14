# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
from datetime import date

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    import requests
except ImportError:
    requests = None
    _logger.warning("requests library not installed — HNB rates cannot be fetched.")


HNB_API_URL = "https://api.hnb.hr/tecajn/v2"


class HnbRate(models.Model):
    """Log of HNB exchange rate fetches — for audit purposes."""
    _name = "l10n_hr.hnb.rate"
    _description = "HNB Exchange Rate Fetch Log"
    _order = "rate_date desc"

    rate_date = fields.Date(required=True, readonly=True)
    currency_id = fields.Many2one("res.currency", required=True, readonly=True)
    currency_name = fields.Char(readonly=True)
    unit_value = fields.Float(
        readonly=True,
        help="Unit (1 or 100) — HNB publishes some currencies per 100 units.",
    )
    buy_rate = fields.Float(readonly=True)
    mean_rate = fields.Float(readonly=True)
    sell_rate = fields.Float(readonly=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    fetched_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    fetched_by = fields.Many2one("res.users", default=lambda self: self.env.user, readonly=True)

    # --- Fetch ------------------------------------------------------------
    @api.model
    def _cron_fetch_hnb_rates(self):
        """Daily cron — fetch today's rates from HNB API."""
        self._fetch_rates_for_date(fields.Date.today())

    @api.model
    def _fetch_rates_for_date(self, rate_date):
        """Fetch rates from HNB API for a specific date."""
        if requests is None:
            _logger.error("requests library not installed — cannot fetch HNB rates.")
            return False
        url = f"{HNB_API_URL}?datum-primjene={rate_date.strftime('%Y-%m-%d')}"
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            rates = response.json()
        except Exception as e:  # noqa: BLE001
            _logger.error("HNB API fetch failed: %s", e)
            return False
        if not rates or not isinstance(rates, list):
            _logger.warning("HNB API returned no rates for %s", rate_date)
            return False
        # Find EUR currency (base)
        eur = self.env.ref("base.EUR", raise_if_not_found=False) or \
            self.env["res.currency"].search([("name", "=", "EUR")], limit=1)
        if not eur:
            _logger.error("EUR currency not found — cannot store HNB rates.")
            return False
        count = 0
        for rate in rates:
            currency_code = rate.get("valuta", "").strip()
            if not currency_code or currency_code == "EUR":
                continue
            currency = self.env["res.currency"].search(
                [("name", "=", currency_code)], limit=1
            )
            if not currency:
                _logger.debug("Currency %s not in Odoo — skipping.", currency_code)
                continue
            # Parse rates (HNB uses comma as decimal separator)
            try:
                unit = int(rate.get("jedan za", "1"))
                mean_rate = float(rate.get("srednji za", "0").replace(",", "."))
                buy_rate = float(rate.get("kupovni za", "0").replace(",", "."))
                sell_rate = float(rate.get("prodajni za", "0").replace(",", "."))
            except (ValueError, TypeError):
                continue
            if mean_rate <= 0:
                continue
            # Normalize to per-unit rate (Odoo expects 1 unit of foreign = X EUR)
            # HNB publishes: 1 EUR = mean_rate / unit of foreign currency
            # Odoo rate: foreign currency 1 unit = 1 / (mean_rate / unit) EUR
            odoo_rate = unit / mean_rate if mean_rate else 0
            # Create rate log
            existing = self.search(
                [
                    ("rate_date", "=", rate_date),
                    ("currency_id", "=", currency.id),
                ],
                limit=1,
            )
            if existing:
                existing.write(
                    {
                        "unit_value": unit,
                        "buy_rate": buy_rate,
                        "mean_rate": mean_rate,
                        "sell_rate": sell_rate,
                        "fetched_on": fields.Datetime.now(),
                        "fetched_by": self.env.user.id,
                    }
                )
            else:
                self.create(
                    {
                        "rate_date": rate_date,
                        "currency_id": currency.id,
                        "currency_name": currency_code,
                        "unit_value": unit,
                        "buy_rate": buy_rate,
                        "mean_rate": mean_rate,
                        "sell_rate": sell_rate,
                    }
                )
            # Update Odoo's res.currency.rate
            existing_odoo = self.env["res.currency.rate"].search(
                [
                    ("currency_id", "=", currency.id),
                    ("name", "=", rate_date),
                ],
                limit=1,
            )
            if existing_odoo:
                existing_odoo.write({"rate": odoo_rate})
            else:
                self.env["res.currency.rate"].create(
                    {
                        "currency_id": currency.id,
                        "name": rate_date,
                        "rate": odoo_rate,
                        "company_id": self.env.company.id,
                    }
                )
            count += 1
        _logger.info("Fetched %d HNB rates for %s", count, rate_date)
        return True

    def action_fetch_today(self):
        """Manual fetch button."""
        self._fetch_rates_for_date(fields.Date.today())
