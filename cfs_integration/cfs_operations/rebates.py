import frappe
from frappe.utils import nowdate

DEFAULT_REBATE_EXPENSE = 'Rebate Expense'
DEFAULT_CASH_ACCOUNT = 'Cash - CFS'
DEFAULT_BANK_ACCOUNT = 'Bank - CFS'

def get_rebate_expense_account():
    acct = frappe.get_value('CFS Settings', None, 'rebate_expense_account')
    return acct or DEFAULT_REBATE_EXPENSE

def get_payment_account(mode):
    if mode == 'Cash':
        return frappe.get_value('CFS Settings', None, 'cash_account') or DEFAULT_CASH_ACCOUNT
    return frappe.get_value('CFS Settings', None, 'bank_account') or DEFAULT_BANK_ACCOUNT

def create_rebate(doc, doctype):
    try:
        sales_person = getattr(doc, 'sales_person', None) or (doc.get('sales_person') if isinstance(doc, dict) else None)
        if not sales_person:
            return
        rate = frappe.db.get_value('Sales Rebate Rate', {'sales_person': sales_person}, 'rebate_percentage') or frappe.get_value('CFS Settings', None, 'default_rebate_rate') or 0.0
        base = getattr(doc, 'net_total', None) or (doc.get('net_total') if isinstance(doc, dict) else 0.0)
        rebate_amount = 0.0
        if rate and rate > 0:
            rebate_amount = round(base * (float(rate)/100.0), 2)
            # avoid duplicates
            existing = frappe.get_all('Sales Rebate', filters={'transaction_reference': getattr(doc, 'name', ''), 'transaction_doctype': doctype})
            if existing:
                return
            r = frappe.get_doc({'doctype':'Sales Rebate','sales_person': sales_person,'transaction_reference': getattr(doc, 'name', ''),'transaction_doctype': doctype,'rebate_type':'Percentage','rebate_value': rate,'computed_amount': rebate_amount,'status':'Pending'})
            r.insert(ignore_permissions=True)
            frappe.db.commit()
    except Exception as e:
        frappe.log_error(f'create_rebate failed: {e}', 'cfs_integration.rebates')

def create_rebate_for_invoice(doc, method=None):
    create_rebate(doc, 'Sales Invoice')

def create_rebate_for_delivery(doc, method=None):
    if not frappe.get_value('CFS Settings', None, 'enable_rebate_on_delivery_note'):
        return
    create_rebate(doc, 'Delivery Note')

def generate_monthly_payouts(period_start=None, period_end=None):
    import datetime
    today = datetime.date.today()
    if not period_start or not period_end:
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - datetime.timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        period_start = first_day_last_month.isoformat()
        period_end = last_day_last_month.isoformat()
    rebates = frappe.get_all('Sales Rebate', filters={'status':'Approved', 'creation': ['between', [period_start + ' 00:00:00', period_end + ' 23:59:59']]}, fields=['name','sales_person','computed_amount'])
    agg = {}
    for r in rebates:
        sp = r['sales_person']
        agg.setdefault(sp, 0.0)
        agg[sp] += float(r['computed_amount'] or 0.0)
    payouts = []
    for sp, total in agg.items():
        if total <= 0:
            continue
        payout = frappe.get_doc({'doctype':'Sales Rebate Payout','sales_person': sp, 'period_start': period_start, 'period_end': period_end, 'total_rebate_amount': total, 'status':'Draft'})
        payout.insert(ignore_permissions=True)
        payouts.append(payout.name)
    frappe.db.commit()
    return {'payouts': payouts}

def create_payment_entry_for_payout(payout_name, mode='Bank'):
    try:
        payout = frappe.get_doc('Sales Rebate Payout', payout_name)
        if payout.status != 'Draft':
            return {'error':'payout_not_draft'}
        rebate_account = get_rebate_expense_account()
        payment_account = get_payment_account(mode)
        pe = frappe.get_doc({
            'doctype': 'Payment Entry',
            'payment_type': 'Pay',
            'mode_of_payment': mode,
            'party_type': 'Sales Person',
            'party': payout.sales_person,
            'paid_amount': payout.total_rebate_amount,
            'received_amount': payout.total_rebate_amount,
            'paid_from': payment_account,
            'paid_to': rebate_account,
            'reference_no': payout.name,
            'remarks': 'Payout for rebates {} to {}'.format(payout.period_start, payout.period_end)
        })
        pe.insert(ignore_permissions=True)
        # keep draft; link and mark submitted for review
        payout.payment_entry = pe.name
        payout.status = 'Submitted'
        payout.save(ignore_permissions=True)
        frappe.db.commit()
        return {'ok': True, 'payment_entry': pe.name}
    except Exception as e:
        frappe.log_error(f'create_payment_entry_for_payout failed: {e}', 'cfs_integration.rebates')
        return {'error': str(e)}
