import frappe

@frappe.whitelist(allow_guest=False)
def push_invoice(data):
    return frappe.get_attr('cfs_integration.cfs_operations.tariff.push_invoice_handler')(data)

@frappe.whitelist(allow_guest=False)
def receive_job(data):
    return frappe.get_attr('cfs_integration.cfs_operations.job.receive_job_handler')(data)
