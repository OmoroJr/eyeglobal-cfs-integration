import frappe

def push_invoice_handler(data):
    payload = frappe.parse_json(data) if isinstance(data, str) else data
    # minimal: create Sales Invoice
    customer = payload.get('customer') or 'Guest'
    items = []
    for t in payload.get('tariff_items', []):
        items.append({'item_code': t.get('tariff_code'), 'qty': t.get('qty',1), 'rate': t.get('rate',0)})
    inv = frappe.get_doc({'doctype':'Sales Invoice','customer':customer,'posting_date': payload.get('posting_date'), 'items': items})
    inv.insert(ignore_permissions=True)
    frappe.db.commit()
    return {'status':'created','invoice': inv.name}
