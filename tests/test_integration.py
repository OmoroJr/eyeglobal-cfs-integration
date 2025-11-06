import frappe
import pytest

@pytest.mark.usefixtures('test_sites')
def test_smoke_truck_item_and_rebate():
    # create sales person
    sp = frappe.get_doc({'doctype':'Sales Person','sales_person_name':'CI SP','employee_name':'CI Employee'})
    sp.insert(ignore_permissions=True)
    # create rebate rate
    rr = frappe.get_doc({'doctype':'Sales Rebate Rate','sales_person':sp.name,'rebate_percentage':5.0})
    rr.insert(ignore_permissions=True)
    # create customer
    cust = frappe.get_doc({'doctype':'Customer','customer_name':'CI Cust','customer_group':frappe.get_default('customer_group') or 'Commercial','territory':frappe.get_default('territory') or 'All Territories'})
    cust.insert(ignore_permissions=True)
    # create sales invoice
    si = frappe.get_doc({'doctype':'Sales Invoice','customer':cust.name,'posting_date':frappe.utils.nowdate(),'items':[{'item_code':'TEST-ITEM','qty':1,'rate':1000}],'sales_person':sp.name})
    si.insert(ignore_permissions=True)
    si.submit()
    frappe.db.commit()
    rebates = frappe.get_all('Sales Rebate', filters={'transaction_reference': si.name}, fields=['name','computed_amount'])
    assert rebates and float(rebates[0]['computed_amount']) == 50.0
