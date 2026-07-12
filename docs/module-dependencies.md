# Module Dependency Graph

This document shows the dependencies between all SI/HR Odoo modules.
The graph is rendered automatically by GitHub (Mermaid syntax).

Blue nodes = Slovenian modules (l10n_si_*)
Orange nodes = Croatian modules (l10n_hr_*)

Arrows point from dependency to dependent (A --> B means B depends on A).

## Dependency Graph

```mermaid
graph TD
    l10n_si_accessibility["accessibility"]
    l10n_si_accounting_advanced["accounting_advanced"]
    l10n_si_ai_concierge["ai_concierge"]
    l10n_si_approvals["approvals"]
    l10n_si_assets["assets"]
    l10n_si_audit_trail["audit_trail"]
    l10n_si_bank_parser["bank_parser"]
    l10n_si_bank_sync["bank_sync"]
    l10n_si_budget_planning["budget_planning"]
    l10n_si_camping["camping"]
    l10n_si_channel_manager["channel_manager"]
    l10n_si_chatbot_widget["chatbot_widget"]
    l10n_si_competitor_pricing["competitor_pricing"]
    l10n_si_concierge_services["concierge_services"]
    l10n_si_customer_statements["customer_statements"]
    l10n_si_dashboard_executive["dashboard_executive"]
    l10n_si_data_protection["data_protection"]
    l10n_si_edi["edi"]
    l10n_si_etourism["etourism"]
    l10n_si_event_accommodation["event_accommodation"]
    l10n_si_event_contract["event_contract"]
    l10n_si_event_equipment_rental["event_equipment_rental"]
    l10n_si_event_photographer["event_photographer"]
    l10n_si_event_venue["event_venue"]
    l10n_si_farm_tourism["farm_tourism"]
    l10n_si_field_service["field_service"]
    l10n_si_fiscal["fiscal"]
    l10n_si_fleet["fleet"]
    l10n_si_gift_voucher["gift_voucher"]
    l10n_si_group_booking["group_booking"]
    l10n_si_health_check["health_check"]
    l10n_si_helpdesk_simple["helpdesk_simple"]
    l10n_si_hotel["hotel"]
    l10n_si_housekeeping["housekeeping"]
    l10n_si_hr_payroll_community["hr_payroll_community"]
    l10n_si_hr_roster["hr_roster"]
    l10n_si_intrastat["intrastat"]
    l10n_si_kitchen_display["kitchen_display"]
    l10n_si_knowledge["knowledge"]
    l10n_si_laundry["laundry"]
    l10n_si_loyalty_program["loyalty_program"]
    l10n_si_maintenance_advanced["maintenance_advanced"]
    l10n_si_maintenance_request["maintenance_request"]
    l10n_si_marketing_automation["marketing_automation"]
    l10n_si_minibar["minibar"]
    l10n_si_mobile_app["mobile_app"]
    l10n_si_multi_company["multi_company"]
    l10n_si_ocr_invoice["ocr_invoice"]
    l10n_si_partner_portal["partner_portal"]
    l10n_si_payment_gateway["payment_gateway"]
    l10n_si_pets["pets"]
    l10n_si_pos_advanced["pos_advanced"]
    l10n_si_procurement["procurement"]
    l10n_si_quality_control["quality_control"]
    l10n_si_reports["reports"]
    l10n_si_restaurant["restaurant"]
    l10n_si_revenue_management["revenue_management"]
    l10n_si_review_management["review_management"]
    l10n_si_sequence["sequence"]
    l10n_si_sign["sign"]
    l10n_si_stripe_payment["stripe_payment"]
    l10n_si_subscription_advanced["subscription_advanced"]
    l10n_si_sustainability["sustainability"]
    l10n_si_timesheet_approval["timesheet_approval"]
    l10n_si_tourist_tax["tourist_tax"]
    l10n_si_transport["transport"]
    l10n_si_vat_validation["vat_validation"]
    l10n_si_vies_return["vies_return"]
    l10n_si_weather_integration["weather_integration"]
    l10n_si_website_booking["website_booking"]
    l10n_si_wellness["wellness"]
    l10n_si_whatsapp["whatsapp"]
    l10n_si_whatsapp_business["whatsapp_business"]
    l10n_si_year_end_close["year_end_close"]
    l10n_hr_edi["edi"]
    l10n_hr_evisitor["evisitor"]
    l10n_hr_fiscal["fiscal"]
    l10n_hr_kuna["kuna"]
    l10n_hr_pdv["pdv"]

    l10n_hr_fiscal --> l10n_hr_evisitor
    l10n_hr_fiscal --> l10n_hr_pdv
    l10n_si_hotel --> l10n_si_accessibility
    l10n_si_knowledge --> l10n_si_ai_concierge
    l10n_si_whatsapp --> l10n_si_ai_concierge
    l10n_si_bank_parser --> l10n_si_bank_sync
    l10n_si_fiscal --> l10n_si_camping
    l10n_si_sequence --> l10n_si_camping
    l10n_si_hotel --> l10n_si_channel_manager
    l10n_si_camping --> l10n_si_channel_manager
    l10n_si_ai_concierge --> l10n_si_chatbot_widget
    l10n_si_hotel --> l10n_si_competitor_pricing
    l10n_si_hotel --> l10n_si_concierge_services
    l10n_si_hotel --> l10n_si_dashboard_executive
    l10n_si_restaurant --> l10n_si_dashboard_executive
    l10n_si_wellness --> l10n_si_dashboard_executive
    l10n_si_vat_validation --> l10n_si_edi
    l10n_si_hotel --> l10n_si_etourism
    l10n_si_camping --> l10n_si_etourism
    l10n_si_tourist_tax --> l10n_si_etourism
    l10n_si_event_venue --> l10n_si_event_accommodation
    l10n_si_hotel --> l10n_si_event_accommodation
    l10n_si_event_venue --> l10n_si_event_contract
    l10n_si_sign --> l10n_si_event_contract
    l10n_si_event_venue --> l10n_si_event_equipment_rental
    l10n_si_event_venue --> l10n_si_event_photographer
    l10n_si_fiscal --> l10n_si_event_venue
    l10n_si_sequence --> l10n_si_event_venue
    l10n_si_fiscal --> l10n_si_farm_tourism
    l10n_si_sequence --> l10n_si_farm_tourism
    l10n_si_sequence --> l10n_si_fiscal
    l10n_si_vat_validation --> l10n_si_fiscal
    l10n_si_hotel --> l10n_si_gift_voucher
    l10n_si_hotel --> l10n_si_group_booking
    l10n_si_event_venue --> l10n_si_group_booking
    l10n_si_fiscal --> l10n_si_hotel
    l10n_si_sequence --> l10n_si_hotel
    l10n_si_hotel --> l10n_si_housekeeping
    l10n_si_vat_validation --> l10n_si_hr_payroll_community
    l10n_si_restaurant --> l10n_si_kitchen_display
    l10n_si_hotel --> l10n_si_laundry
    l10n_si_hotel --> l10n_si_loyalty_program
    l10n_si_hotel --> l10n_si_maintenance_request
    l10n_si_housekeeping --> l10n_si_maintenance_request
    l10n_si_hotel --> l10n_si_minibar
    l10n_si_hotel --> l10n_si_mobile_app
    l10n_si_housekeeping --> l10n_si_mobile_app
    l10n_si_maintenance_request --> l10n_si_mobile_app
    l10n_si_hotel --> l10n_si_multi_company
    l10n_si_hotel --> l10n_si_partner_portal
    l10n_si_loyalty_program --> l10n_si_partner_portal
    l10n_si_maintenance_request --> l10n_si_partner_portal
    l10n_si_hotel --> l10n_si_pets
    l10n_si_fiscal --> l10n_si_pos_advanced
    l10n_si_hotel --> l10n_si_pos_advanced
    l10n_si_vat_validation --> l10n_si_reports
    l10n_si_fiscal --> l10n_si_restaurant
    l10n_si_sequence --> l10n_si_restaurant
    l10n_si_hotel --> l10n_si_revenue_management
    l10n_si_camping --> l10n_si_revenue_management
    l10n_si_hotel --> l10n_si_review_management
    l10n_si_hotel --> l10n_si_transport
    l10n_si_hotel --> l10n_si_weather_integration
    l10n_si_hotel --> l10n_si_website_booking
    l10n_si_camping --> l10n_si_website_booking
    l10n_si_revenue_management --> l10n_si_website_booking
    l10n_si_fiscal --> l10n_si_wellness
    l10n_si_sequence --> l10n_si_wellness

    classDef siModule fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
    classDef hrModule fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    class l10n_si_accessibility siModule
    class l10n_si_accounting_advanced siModule
    class l10n_si_ai_concierge siModule
    class l10n_si_approvals siModule
    class l10n_si_assets siModule
    class l10n_si_audit_trail siModule
    class l10n_si_bank_parser siModule
    class l10n_si_bank_sync siModule
    class l10n_si_budget_planning siModule
    class l10n_si_camping siModule
    class l10n_si_channel_manager siModule
    class l10n_si_chatbot_widget siModule
    class l10n_si_competitor_pricing siModule
    class l10n_si_concierge_services siModule
    class l10n_si_customer_statements siModule
    class l10n_si_dashboard_executive siModule
    class l10n_si_data_protection siModule
    class l10n_si_edi siModule
    class l10n_si_etourism siModule
    class l10n_si_event_accommodation siModule
    class l10n_si_event_contract siModule
    class l10n_si_event_equipment_rental siModule
    class l10n_si_event_photographer siModule
    class l10n_si_event_venue siModule
    class l10n_si_farm_tourism siModule
    class l10n_si_field_service siModule
    class l10n_si_fiscal siModule
    class l10n_si_fleet siModule
    class l10n_si_gift_voucher siModule
    class l10n_si_group_booking siModule
    class l10n_si_health_check siModule
    class l10n_si_helpdesk_simple siModule
    class l10n_si_hotel siModule
    class l10n_si_housekeeping siModule
    class l10n_si_hr_payroll_community siModule
    class l10n_si_hr_roster siModule
    class l10n_si_intrastat siModule
    class l10n_si_kitchen_display siModule
    class l10n_si_knowledge siModule
    class l10n_si_laundry siModule
    class l10n_si_loyalty_program siModule
    class l10n_si_maintenance_advanced siModule
    class l10n_si_maintenance_request siModule
    class l10n_si_marketing_automation siModule
    class l10n_si_minibar siModule
    class l10n_si_mobile_app siModule
    class l10n_si_multi_company siModule
    class l10n_si_ocr_invoice siModule
    class l10n_si_partner_portal siModule
    class l10n_si_payment_gateway siModule
    class l10n_si_pets siModule
    class l10n_si_pos_advanced siModule
    class l10n_si_procurement siModule
    class l10n_si_quality_control siModule
    class l10n_si_reports siModule
    class l10n_si_restaurant siModule
    class l10n_si_revenue_management siModule
    class l10n_si_review_management siModule
    class l10n_si_sequence siModule
    class l10n_si_sign siModule
    class l10n_si_stripe_payment siModule
    class l10n_si_subscription_advanced siModule
    class l10n_si_sustainability siModule
    class l10n_si_timesheet_approval siModule
    class l10n_si_tourist_tax siModule
    class l10n_si_transport siModule
    class l10n_si_vat_validation siModule
    class l10n_si_vies_return siModule
    class l10n_si_weather_integration siModule
    class l10n_si_website_booking siModule
    class l10n_si_wellness siModule
    class l10n_si_whatsapp siModule
    class l10n_si_whatsapp_business siModule
    class l10n_si_year_end_close siModule
    class l10n_hr_edi hrModule
    class l10n_hr_evisitor hrModule
    class l10n_hr_fiscal hrModule
    class l10n_hr_kuna hrModule
    class l10n_hr_pdv hrModule
```

## Statistics

| Metric | Value |
|--------|-------|
| Total SI modules | 74 |
| Total HR modules | 5 |
| SI → SI dependencies | 66 |
| SI → HR dependencies | 0 |
| HR → SI dependencies | 0 |
| HR → HR dependencies | 2 |
| Dependencies on Odoo core | 36 |

### Top 10 Most Depended-Upon Modules

| Module | Depended by (count) |
|--------|---------------------|
| `l10n_si_hotel` | 24 |
| `l10n_si_fiscal` | 7 |
| `l10n_si_sequence` | 7 |
| `l10n_si_event_venue` | 5 |
| `l10n_si_camping` | 4 |
| `l10n_si_vat_validation` | 4 |
| `l10n_hr_fiscal` | 2 |
| `l10n_si_restaurant` | 2 |
| `l10n_si_housekeeping` | 2 |
| `l10n_si_maintenance_request` | 2 |


---

*Generated by `scripts/generate_dependency_graph.py`*
