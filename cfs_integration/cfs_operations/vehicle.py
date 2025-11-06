import frappe
from frappe.model.document import Document

class VehicleUnit(Document):
    def before_insert(self):
        if not self.vehicle_id:
            self.vehicle_id = self.registration_number

def update_vehicle_status_from_delivery(doc, method=None):
    try:
        vehicle = getattr(doc, 'vehicle_id', None) or (doc.get('vehicle_id') if isinstance(doc, dict) else None)
        if not vehicle:
            return
        if frappe.db.exists('Vehicle Unit', vehicle):
            v = frappe.get_doc('Vehicle Unit', vehicle)
            v.status = 'In Use'
            v.save(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f'update_vehicle_status_from_delivery failed: {e}', 'cfs_integration.vehicle')
