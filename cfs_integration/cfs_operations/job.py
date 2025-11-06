import frappe

def receive_job_handler(data):
    payload = frappe.parse_json(data) if isinstance(data, str) else data
    job_no = payload.get('job_no')
    if not job_no:
        frappe.throw('job_no required')
    if frappe.db.exists('CFS Job', {'job_no': job_no}):
        return {'status':'exists'}
    job = frappe.get_doc({'doctype':'CFS Job','job_no':job_no,'job_type':payload.get('job_type'),'customer':payload.get('customer'),'tariff_code': payload.get('tariff_code')})
    job.insert(ignore_permissions=True)
    frappe.db.commit()
    return {'status':'created','job':job.name}
