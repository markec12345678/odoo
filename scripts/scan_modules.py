#!/usr/bin/env python3
"""Comprehensive integrity scan for all l10n_si_* / l10n_hr_* modules.

Usage:
    python scripts/scan_modules.py [addons_path] [module1 module2 ...]

If no addons_path is given, defaults to 'addons/' relative to repo root.
If no modules are listed, scans all l10n_si_* / l10n_hr_* modules found.

Checks performed (per module):
  A. MANIFEST - 'data' files exist on disk, no duplicate entries,
                'depends' modules exist
  B. MODELS   - every .py in models/ is imported (incl. sibling imports)
                - every new Model/TransientModel has an ACL row
                  (skips AbstractModel and pure _inherit)
                - controllers inited, tests inited
  C. VIEWS    - XML parses, view model attribute is valid,
                top-level view field declarations are valid
                (correctly skips nested relational field trees and
                xpath-targeted fields)

Designed to run in CI (GitHub Actions) before each deploy.
Exit code: 0 = OK, 1 = issues found (CRIT/HIGH/MED), 2 = LOW only.
"""
import ast
import csv
import os
import re
import sys
import glob
import xml.etree.ElementTree as ET


def find_addons_path():
    """Find the addons/ directory relative to this script (scripts/ -> repo root)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # scripts/ is at repo root, so addons/ is one level up
    candidate = os.path.join(script_dir, '..', 'addons')
    if os.path.isdir(candidate):
        return os.path.abspath(candidate)
    # Fallback: current working directory
    if os.path.isdir('addons'):
        return os.path.abspath('addons')
    return None


ADDONS = find_addons_path() or os.path.join(os.getcwd(), 'addons')

CORE_FIELDS = {
    'name', 'active', 'company_id', 'create_date', 'create_uid',
    'write_date', 'write_uid', 'id', 'display_name', '__last_update',
    'state', 'sequence', 'parent_id', 'parent_path', 'color', 'note',
    'message_ids', 'message_follower_ids', 'message_partner_ids',
    'website_id', 'currency_id', 'partner_id', 'user_id', 'date', 'date_start',
    'date_end', 'amount', 'amount_total', 'reference', 'origin', 'notes',
    'description', 'code', 'type', 'value', 'quantity', 'price', 'price_unit',
    'country_id', 'state_id', 'phone', 'mobile', 'email', 'website', 'vat',
    'image_1920', 'lang', 'tz', 'category_id', 'employee_id',
    'product_id', 'product_tmpl_id', 'account_id', 'journal_id',
    'partner_bank_id', 'payment_id', 'invoice_id', 'invoice_ids',
    'order_id', 'order_line_ids', 'picking_id', 'picking_ids',
    'location_id', 'location_dest_id', 'lot_id', 'product_uom',
    'product_uom_qty', 'product_qty', 'amount_untaxed', 'amount_tax',
    'payment_state', 'access_url', 'access_token', 'is_company',
    'company_type', 'child_ids', 'user_ids', 'bank_ids', 'image',
    'comment', 'team_id', 'tag_ids', 'stage_id', 'kanban_state',
    'priority', 'activity_ids', 'activity_state', 'activity_summary',
    'activity_type_id', 'activity_user_id', 'activity_date_deadline',
    'my_activity_date_deadline', 'message_is_follower', 'message_unread',
    'message_unread_counter', 'message_needaction',
    'message_needaction_counter', 'message_has_error',
    'message_has_error_counter', 'message_attachment_count',
    'message_main_attachment_id', 'website_published', 'website_url',
    'is_published', 'allowed_company_ids', 'company_ids', 'branch_id',
    'commercial_partner_id', 'signup_token', 'signup_expiration',
    'signup_url', 'phone_normalized', 'mobile_normalized',
    'calendar_last_notif_ack', 'odoobot_state', 'odoobot_status',
    'image_512', 'image_128', 'image_small', 'image_medium', 'logo',
    'avatar_128', 'avatar_256', 'avatar_512', 'avatar_1024', 'avatar_1920',
    'phone_blacklisted', 'mobile_blacklisted', 'email_blacklisted',
    'phone_sanitized', 'phone_sanitized_blacklisted',
    'is_blacklisted', 'signup_type',
    'notification_type', 'notification_email_type',
    'notification_email_status', 'share', 'action_id',
    'login', 'new_password', 'password',
    'oauth_provider_id', 'oauth_uid', 'oauth_access_token',
    'oauth_access_token_expiration', 'oauth_master_uid',
    'oauth_refresh_token', 'oauth_referral_url', 'oauth_scope',
    'totp_secret', 'totp_enabled', 'totp_trusted_device_ids',
    'login_date', 'login_fail', 'login_fail_reason',
    'groups_id', 'res_model', 'res_id', 'res_name', 'model', 'model_id',
    'report_type', 'report_name', 'paperformat_id', 'report_file',
    'binding_type', 'binding_model_id', 'binding_view_types',
    'module', 'shortdesc', 'is_internal', 'access_right', 'can_publish',
    # product.template
    'categ_id', 'product_variant_id', 'product_variant_ids',
    'attribute_line_ids', 'attribute_value_ids', 'no_variant_attribute_ids',
    'product_template_attribute_value_ids',
    'valid_product_template_attribute_line_ids',
    'price_extra', 'price', 'list_price', 'standard_price',
    'volume', 'weight', 'description_sale', 'description_purchase',
    'description_picking', 'available_in_pos', 'to_weight',
    'pos_categ_id', 'taxes_id', 'supplier_taxes_id',
    'seller_ids', 'seller_id', 'route_ids', 'route_from_warehouse_ids',
    'purchase_line_warn', 'purchase_line_warn_msg',
    'sale_line_warn', 'sale_line_warn_msg', 'intrastat_id',
    'origin_line_ids', 'responsible_id', 'rental',
    'availability_warning_delay', 'expense_policy', 'invoice_policy',
    'service_type', 'optional_product_ids', 'alternative_product_ids',
    'accessory_product_ids', 'purchase_method',
    'property_account_income_id', 'property_account_expense_id',
    'property_account_creditor_price_difference',
    'image_variant_1920', 'image_variant_1024', 'image_variant_512',
    'image_variant_256', 'image_variant_128',
    'combination_indices', 'is_product_variant',
    'default_code', 'barcode', 'dimensions_needs_refresh',
    # account.move / account.move.line
    'line_ids', 'invoice_line_ids', 'invoice_payment_term_id',
    'invoice_partner_bank_id', 'invoice_incoterm_id',
    'invoice_source_email', 'invoice_date', 'invoice_date_due',
    'invoice_payment_ref', 'invoice_filter_type_domain',
    'invoice_sent', 'invoice_xml_attachment_ref',
    'fav_product_ids', 'amount_untaxed_signed', 'amount_tax_signed',
    'amount_total_signed', 'amount_residual_signed',
    'amount_untaxed_in_currency_signed',
    'amount_tax_in_currency_signed', 'amount_total_in_currency_signed',
    'amount_residual_in_currency_signed',
    'tax_totals', 'tax_totals_json',
    'amount_authorized', 'amount_captured', 'amount_refunded',
    'captured_amount', 'authorized_amount', 'currency_rate',
    'reversed_entry_id', 'reverse_entry_ids', 'auto_post',
    'auto_post_origin', 'quick_edit_mode', 'company_currency_id',
    'country_code', 'highest_name', 'post_name',
    'invoice_outstanding_credits_debits_widget',
    'invoice_outstanding_credits_debits_total',
    'invoice_has_outstanding', 'payments_widget',
    'invoice_payments_widget', 'restrict_mode_hash_table',
    'secure_sequence_number', 'inalterable_hash', 'inalterable_chain',
    'is_invoice', 'is_sale_document', 'is_purchase_document',
    'is_inbound', 'is_outbound', 'is_storno',
    'qr_code_method', 'preferred_date', 'stock_move_id',
    'stock_move_ids', 'purchase_line_id',
    'product_uom_id', 'discount',
    'price_subtotal', 'price_total',
    'price_subtotal_in_currency_signed',
    'price_total_in_currency_signed',
    'tax_ids', 'tax_tag_ids', 'tax_repartition_line_id',
    'group_tax_id', 'account_root_id', 'account_internal_type',
    'account_internal_group', 'account_type', 'analytic_distribution',
    'analytic_line_ids', 'analytic_account_id',
    'tag_ids', 'tax_tag_invert', 'debit', 'credit', 'balance',
    'amount_currency', 'partner_name', 'date_maturity', 'reconciled',
    'full_reconcile_id', 'matched_debit_ids', 'matched_credit_ids',
    'move_id', 'move_name', 'ref', 'statement_line_id',
    'exchange_rate',
    # payment / stripe
    'provider', 'provider_id', 'transaction_ids', 'payment_ids',
    'partner_email', 'partner_address',
    'partner_city', 'partner_zip', 'partner_country_id',
    'partner_phone', 'reference', 'reference_type',
    'tx_ref', 'acquirer_reference', 'capture_date',
    'authorize_transaction_id', 'capture_transaction_id',
    'refund_transaction_id', 'void_transaction_id',
    'operation', 'state', 'state_message', 'date', 'date_validate',
    'date_authorization', 'date_capture', 'date_refund',
    'date_cancellation', 'date_creation', 'date_modification',
    'date_transaction', 'date_confirmation',
    'stripe_publishable_key', 'stripe_secret_key', 'stripe_webhook_secret',
    'stripe_payment_method_types', 'stripe_checkout_session_type',
    'stripe_payment_intent_capture_method',
    # chatbot
    'chatbot_enabled', 'chatbot_color', 'chatbot_position',
    'chatbot_script_id', 'script_id', 'operator_id',
    'welcome_message', 'away_message', 'timeout_message',
    # Croatian-specific (l10n_hr_edi)
    'l10n_hr_operator_name', 'l10n_hr_operator_oib',
    'l10n_hr_process_type', 'l10n_hr_customer_defined_process_name',
    'l10n_hr_kpd_category_id', 'l10n_hr_mer_document_eid',
    'l10n_hr_mer_document_status', 'l10n_hr_fiscalization_status',
    'l10n_hr_fiscalization_request', 'l10n_hr_fiscalization_error',
    'l10n_hr_fiscalization_channel_type', 'l10n_hr_fiscal_user_id',
}


def parse_python_models(text):
    """Yield (class_name, _name_or_None, _inherit_value, fields_set,
    comodels_set, model_kind) where model_kind is 'Model' |
    'TransientModel' | 'AbstractModel' (derived from class bases).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        model_kind = None
        for base in node.bases:
            if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                if base.value.id == 'models':
                    if base.attr in ('Model', 'TransientModel', 'AbstractModel'):
                        model_kind = base.attr
                        break
        _name = None
        _inherit = None
        fields = set()
        comodels = set()
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name) and tgt.id == '_name':
                        if isinstance(stmt.value, ast.Constant):
                            _name = stmt.value.value
                    if isinstance(tgt, ast.Name) and tgt.id == '_inherit':
                        if isinstance(stmt.value, ast.Constant):
                            _inherit = stmt.value.value
                        elif isinstance(stmt.value, ast.List):
                            _inherit = [e.value for e in stmt.value.elts
                                        if isinstance(e, ast.Constant)]
                for tgt in stmt.targets:
                    if isinstance(tgt, ast.Name) and isinstance(stmt.value, ast.Call):
                        call = stmt.value
                        f = call.func
                        attr_chain = []
                        cur = f
                        while isinstance(cur, ast.Attribute):
                            attr_chain.append(cur.attr)
                            cur = cur.value
                        if isinstance(cur, ast.Name):
                            attr_chain.append(cur.id)
                        attr_chain.reverse()
                        if len(attr_chain) >= 2 and attr_chain[0] == 'fields':
                            field_type = attr_chain[1]
                            if field_type in ('Many2one', 'One2many', 'Many2many'):
                                if call.args and isinstance(call.args[0], ast.Constant):
                                    comodels.add(call.args[0].value)
                            fields.add(tgt.id)
        yield (node.name, _name, _inherit, fields, comodels,
               model_kind or 'Model')


def scan_module(mod, addons_path):
    issues = []
    mod_path = f'{addons_path}/{mod}'
    if not os.path.isdir(mod_path):
        return [(mod, 'CRIT', f'module dir missing: {mod_path}')]

    manifest_path = f'{mod_path}/__manifest__.py'
    if not os.path.exists(manifest_path):
        return [(mod, 'CRIT', '__manifest__.py missing')]
    try:
        manifest = ast.literal_eval(open(manifest_path).read())
    except Exception as e:
        return [(mod, 'CRIT', f'cannot parse manifest: {e}')]

    # A.1 'data' files exist
    for f in manifest.get('data', []) + manifest.get('demo', []):
        full = f'{mod_path}/{f}'
        if not os.path.exists(full):
            issues.append((mod, 'HIGH', f'manifest.data: listed file missing: {f}'))

    # A.2 'data' files unique
    seen = set()
    for f in manifest.get('data', []):
        if f in seen:
            issues.append((mod, 'HIGH', f'manifest.data: duplicate entry: {f}'))
        seen.add(f)

    # A.3 'depends' modules exist
    all_addon_names = set(
        d for d in os.listdir(addons_path)
        if os.path.isdir(os.path.join(addons_path, d))
    )
    # Also include Odoo core modules
    repo_root = os.path.dirname(addons_path)
    core_addons_path = os.path.join(repo_root, 'odoo', 'addons')
    if os.path.isdir(core_addons_path):
        all_addon_names.update(
            d for d in os.listdir(core_addons_path)
            if os.path.isdir(os.path.join(core_addons_path, d))
        )
    all_addon_names.update({'base', 'mail', 'web', 'website',
                             'payment', 'payment_stripe'})
    for dep in manifest.get('depends', []):
        if dep not in all_addon_names:
            issues.append((mod, 'HIGH', f'manifest.depends: unknown dependency: {dep}'))

    # B.1 every .py in models/ is imported (in __init__.py OR by sibling .py)
    models_dir = f'{mod_path}/models'
    if os.path.isdir(models_dir):
        py_files = [os.path.basename(p)[:-3]
                    for p in glob.glob(f'{models_dir}/*.py')
                    if not p.endswith('__init__.py')]
        all_init_text = ''
        for py_path in glob.glob(f'{models_dir}/*.py'):
            all_init_text += open(py_path).read() + '\n'
        for py in py_files:
            pattern1 = f'from . import {py}'
            pattern2 = f'from .{py} import'
            if pattern1 not in all_init_text and pattern2 not in all_init_text:
                issues.append((mod, 'HIGH',
                    f'models/{py}.py not imported anywhere in models/ - DEAD CODE'))

    # B.2 collect models declared (handle multi-class files correctly)
    own_models = {}
    pure_inherits = set()
    abstract_models = set()
    if os.path.isdir(models_dir):
        for py in glob.glob(f'{models_dir}/*.py'):
            text = open(py).read()
            for class_name, _name, _inherit, fields, comodels, model_kind in parse_python_models(text):
                is_pure_inherit = (
                    _name is not None
                    and (
                        (isinstance(_inherit, str) and _inherit == _name)
                        or (isinstance(_inherit, list) and _name in _inherit)
                    )
                )
                key = _name or (_inherit if isinstance(_inherit, str) else None)
                if key:
                    if key in own_models:
                        prev_fields, prev_comodels, _, _ = own_models[key]
                        fields = prev_fields | fields
                        comodels = prev_comodels | comodels
                    own_models[key] = (fields, comodels, _inherit, model_kind)
                    if is_pure_inherit or _name is None:
                        pure_inherits.add(key)
                    if model_kind == 'AbstractModel':
                        abstract_models.add(key)

    # B.3 every new Model/TransientModel has ACL row
    access_csv = f'{mod_path}/security/ir.model.access.csv'
    csv_models = set()
    if os.path.exists(access_csv):
        with open(access_csv) as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                mid = row.get('model_id:id', '')
                if mid.startswith('model_'):
                    csv_models.add(mid)
    for m_name, (_, _, _, _kind) in own_models.items():
        if m_name in pure_inherits or m_name in abstract_models:
            continue
        underscored = 'model_' + m_name.replace('.', '_')
        if underscored not in csv_models:
            issues.append((mod, 'MED',
                f'security: no ACL row for new {_kind} {m_name}'))

    # B.4 controllers inited
    ctrl_dir = f'{mod_path}/controllers'
    if os.path.isdir(ctrl_dir):
        py_files = [os.path.basename(p)[:-3]
                    for p in glob.glob(f'{ctrl_dir}/*.py')
                    if not p.endswith('__init__.py')]
        all_init_text = ''
        for py_path in glob.glob(f'{ctrl_dir}/*.py'):
            all_init_text += open(py_path).read() + '\n'
        for py in py_files:
            pattern1 = f'from . import {py}'
            pattern2 = f'from .{py} import'
            if pattern1 not in all_init_text and pattern2 not in all_init_text:
                issues.append((mod, 'HIGH',
                    f'controllers/{py}.py not imported anywhere in controllers/ - DEAD CODE'))

    # B.5 tests inited
    tests_dir = f'{mod_path}/tests'
    if os.path.isdir(tests_dir):
        test_files = [os.path.basename(p)[:-3]
                      for p in glob.glob(f'{tests_dir}/test_*.py')]
        if test_files:
            init_path = f'{tests_dir}/__init__.py'
            init_text = open(init_path).read() if os.path.exists(init_path) else ''
            for tf in test_files:
                p1 = f'from . import {tf}'
                p2 = f'import {tf}'
                if p1 not in init_text and p2 not in init_text:
                    issues.append((mod, 'LOW',
                        f'tests/{tf}.py not imported in tests/__init__.py'))

    # C.1 view fields validation (multi-class aware, xpath-aware)
    for xml in glob.glob(f'{mod_path}/views/*.xml') + glob.glob(f'{mod_path}/data/*.xml'):
        try:
            tree = ET.parse(xml)
        except Exception as e:
            issues.append((mod, 'HIGH', f'xml.parse: {os.path.basename(xml)}: {e}'))
            continue
        for rec in tree.iter('record'):
            if rec.get('model') != 'ir.ui.view':
                continue
            m_field = rec.find('field[@name="model"]')
            if m_field is None:
                continue
            model_name = m_field.text
            if model_name not in own_models:
                continue
            declared_fields = own_models[model_name][0] | CORE_FIELDS
            arch_field = rec.find('field[@name="arch"]')
            if arch_field is None:
                continue

            def walk(elem, inside_relational):
                for child in elem:
                    if child.tag == 'field':
                        fname = child.get('name', '')
                        if not inside_relational and fname and fname not in (
                            'arch', 'model', 'name', 'type', 'priority',
                            'groups_id', 'inherit_id', 'mode', 'active', 'key'
                        ):
                            if fname not in declared_fields:
                                issues.append((mod, 'LOW',
                                    f'view.field: {os.path.basename(xml)}: '
                                    f'field "{fname}" not declared on {model_name}'))
                        has_elem_children = any(c.tag for c in child)
                        walk(child, inside_relational or has_elem_children)
                    elif child.tag == 'xpath':
                        expr = child.get('expr', '')
                        targets_field = ('field[@name=' in expr) or ('//field' in expr)
                        walk(child, inside_relational or targets_field)
                    else:
                        walk(child, inside_relational)
            walk(arch_field, False)

    return issues


def main():
    addons_path = ADDONS
    modules = []

    args = sys.argv[1:]
    if args:
        # First arg may be a path
        if os.path.isdir(args[0]) and not args[0].endswith('.py'):
            addons_path = os.path.abspath(args[0])
            modules = args[1:]
        else:
            modules = args

    if not modules:
        if not os.path.isdir(addons_path):
            print(f'ERROR: addons path not found: {addons_path}')
            return 1
        modules = sorted([
            d for d in os.listdir(addons_path)
            if (d.startswith('l10n_si_') or d.startswith('l10n_hr_'))
            and os.path.isdir(os.path.join(addons_path, d))
        ])

    print(f'Scanning {len(modules)} module(s) in {addons_path}...\n')
    all_issues = []
    for mod in modules:
        all_issues.extend(scan_module(mod, addons_path))

    if not all_issues:
        print('OK: no issues found')
        return 0

    by_sev = {}
    for mod, sev, msg in all_issues:
        by_sev.setdefault(sev, []).append((mod, msg))

    # CRIT/HIGH/MED = exit 1, LOW only = exit 2
    exit_code = 0
    for sev in ('CRIT', 'HIGH', 'MED', 'LOW'):
        items = by_sev.get(sev, [])
        if items:
            print(f'--- {sev} ({len(items)}) ---')
            for mod, msg in items:
                print(f'  [{mod}] {msg}')
            print()
            if sev in ('CRIT', 'HIGH', 'MED'):
                exit_code = 1
            elif sev == 'LOW' and exit_code == 0:
                exit_code = 2

    return exit_code


if __name__ == '__main__':
    sys.exit(main())
